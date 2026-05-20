from __future__ import annotations

import math
import time
from collections import Counter, defaultdict
from typing import Any

import numpy as np

from .graphgen import GraphArtifacts
from .openapi_loader import NormalizedBundle, normalize_text
from .raggen import RagCorpus
from .retrieval_indices import (
    DEFAULT_GRAPH_SPARSE_CONFIG,
    GraphSparseConfig,
    RetrievalIndices,
    build_retrieval_indices,
    graph_sparse_config_grid,
    minmax,
)
from .splits import training_contexts


BASELINE_NAMES = [
    "rag_endpoint",
    "rag_all_max",
    "rag_all_mean",
    "rag_all_top3",
    "bm25_all_max",
    "bm25_all_mean",
    "bm25_all_top3",
    "grag_expand",
    "grag_rerank",
    "grag_constrained",
    "graph_text",
    "graph_sparse",
    "hybrid",
    "learned_lexical",
    "learned_bm25",
    "learned_graph",
    "learned_schema_param",
    "learned_lexical_graph",
    "learned_all",
    "learned",
]


HYBRID_COMPONENTS = ["lexical", "bm25", "graph", "schema_param"]
HYBRID_SCORE_KEYS = {
    "lexical": "rag_all_max",
    "bm25": "bm25_all_max",
    "graph": "graph_sparse",
    "schema_param": "schema_param",
}
OLD_FIXED_HYBRID_WEIGHTS = {"lexical": 0.5, "bm25": 0.0, "graph": 0.5, "schema_param": 0.0}
DEFAULT_HYBRID_WEIGHTS = {"lexical": 1.0, "bm25": 0.0, "graph": 0.0, "schema_param": 0.0}

FEATURE_NAMES = [
    "rag_endpoint",
    "rag_all_max",
    "rag_all_top3",
    "bm25_all_max",
    "bm25_all_top3",
    "graph_sparse",
    "graph_text",
    "schema_param",
    "hybrid",
    "operation_class_match",
    "query_endpoint_overlap",
    "required_param_count",
    "request_schema_count",
    "response_schema_count",
    "operation_confidence",
]
FEATURE_GROUPS = {
    "learned_lexical": ["rag_endpoint", "rag_all_max", "rag_all_top3", "query_endpoint_overlap"],
    "learned_bm25": ["bm25_all_max", "bm25_all_top3"],
    "learned_graph": ["graph_sparse", "graph_text"],
    "learned_schema_param": [
        "schema_param",
        "required_param_count",
        "request_schema_count",
        "response_schema_count",
    ],
    "learned_lexical_graph": [
        "rag_endpoint",
        "rag_all_max",
        "rag_all_top3",
        "graph_sparse",
        "graph_text",
        "query_endpoint_overlap",
    ],
    "learned_all": list(FEATURE_NAMES),
}
LEARNED_BASELINES = list(FEATURE_GROUPS)
LEARNED_ALIAS = "learned"
GRAG_BASELINES = ["grag_expand", "grag_rerank", "grag_constrained"]
GRAG_RERANK_FEATURES = [
    "resource_match",
    "param_match",
    "schema_proximity",
    "auth_proximity",
    "graph_distance",
    "endpoint_degree",
    "operation_confidence",
]


def endpoint_metadata(bundle: NormalizedBundle, endpoint_id: str) -> dict[str, Any]:
    endpoint = bundle.endpoint_by_id(endpoint_id)
    return endpoint_metadata_for_endpoint(endpoint)


def endpoint_metadata_for_endpoint(endpoint: Any) -> dict[str, Any]:
    return {
        "endpoint_id": endpoint.id,
        "operation_id": endpoint.operation_id,
        "method": endpoint.method,
        "path": endpoint.path,
        "operation_class": endpoint.operation_class,
        "required_params": endpoint.required_params,
        "resources": endpoint.resources,
    }


def rank_from_scores(
    bundle: NormalizedBundle,
    scores: dict[str, float],
    latency_ms: float = 0.0,
    metadata_by_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    metadata_by_id = metadata_by_id or {
        endpoint.id: endpoint_metadata_for_endpoint(endpoint)
        for endpoint in bundle.endpoints
    }
    ranked = []
    for endpoint in bundle.endpoints:
        item = dict(metadata_by_id[endpoint.id])
        item["score"] = float(scores.get(endpoint.id, 0.0))
        item["latency_ms"] = latency_ms
        ranked.append(item)
    ranked.sort(key=lambda item: (item["score"], item["endpoint_id"]), reverse=True)
    return ranked


def task_query(task: dict[str, Any]) -> str:
    return str(task.get("router_query") or task.get("query") or "")


def complete_plan_for_ids(top_ids: list[str], task: dict[str, Any]) -> float:
    expected = set(task.get("expected_endpoint_sequence", []))
    if not expected:
        return 1.0 if not top_ids else 0.0
    groups = [expected]
    groups.extend(set(group) for group in task.get("allowed_alternatives", []) or [])
    top = set(top_ids)
    return 1.0 if any(group <= top for group in groups) else 0.0


def first_step_for_ids(top_ids: list[str], task: dict[str, Any]) -> float:
    expected = task.get("expected_endpoint_sequence", [])
    return 1.0 if top_ids and expected and top_ids[0] == expected[0] else 0.0


def top_ids_from_scores(scores: dict[str, float], k: int) -> list[str]:
    return [
        endpoint_id
        for endpoint_id, _score in sorted(scores.items(), key=lambda item: (item[1], item[0]), reverse=True)[:k]
    ]


def endpoint_scores_from_row(endpoint_ids: list[str], row: np.ndarray) -> dict[str, float]:
    return minmax({endpoint_id: float(score) for endpoint_id, score in zip(endpoint_ids, row)})


def weighted_score_sum(
    score_maps: dict[str, dict[str, float]],
    weights: dict[str, float],
    endpoint_ids: list[str],
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for endpoint_id in endpoint_ids:
        value = 0.0
        for component, weight in weights.items():
            score_key = HYBRID_SCORE_KEYS[component]
            value += float(weight) * score_maps.get(score_key, {}).get(endpoint_id, 0.0)
        scores[endpoint_id] = value
    return minmax(scores)


def hybrid_weight_grid() -> list[dict[str, float]]:
    grid: list[dict[str, float]] = []
    steps = [0.0, 0.25, 0.5, 0.75, 1.0]
    for lexical in steps:
        for bm25 in steps:
            for graph in steps:
                for schema_param in steps:
                    if not math.isclose(lexical + bm25 + graph + schema_param, 1.0):
                        continue
                    weights = {
                        "lexical": lexical,
                        "bm25": bm25,
                        "graph": graph,
                        "schema_param": schema_param,
                    }
                    if weights == OLD_FIXED_HYBRID_WEIGHTS:
                        continue
                    grid.append(weights)
    return sorted(grid, key=lambda weights: tuple(weights[name] for name in HYBRID_COMPONENTS))


def hybrid_config_name(weights: dict[str, float]) -> str:
    return "_".join(f"{name}{weights[name]:.2f}" for name in HYBRID_COMPONENTS)


def grag_expand_grid() -> list[dict[str, Any]]:
    configs: list[dict[str, Any]] = []
    for doc_top_n in [5, 10, 20]:
        for hops in [1, 2, 3]:
            for rag_weight, graph_weight in [(0.7, 0.3), (0.5, 0.5), (0.3, 0.7)]:
                configs.append(
                    {
                        "name": f"docs{doc_top_n}_hops{hops}_rag{rag_weight:.1f}_graph{graph_weight:.1f}",
                        "doc_top_n": doc_top_n,
                        "hops": hops,
                        "rag_weight": rag_weight,
                        "graph_weight": graph_weight,
                    }
                )
    return configs


def candidate_top_ids(score_map: dict[str, float], k: int) -> list[str]:
    return top_ids_from_scores(score_map, k)


def grag_candidate_union(score_maps: dict[str, dict[str, float]], k: int) -> list[str]:
    ids = candidate_top_ids(score_maps["rag_all_max"], k)
    ids.extend(candidate_top_ids(score_maps["bm25_all_max"], k))
    return list(dict.fromkeys(ids))


def rerank_weight_grid() -> list[dict[str, float]]:
    weights: list[dict[str, float]] = []
    for feature in GRAG_RERANK_FEATURES:
        weights.append({"name": feature, **{item: 1.0 if item == feature else 0.0 for item in GRAG_RERANK_FEATURES}})
    weights.append({"name": "balanced", **{item: 1.0 / len(GRAG_RERANK_FEATURES) for item in GRAG_RERANK_FEATURES}})
    weights.append(
        {
            "name": "semantic",
            "resource_match": 0.20,
            "param_match": 0.20,
            "schema_proximity": 0.20,
            "auth_proximity": 0.10,
            "graph_distance": 0.20,
            "endpoint_degree": 0.05,
            "operation_confidence": 0.05,
        }
    )
    return weights


def constrained_grid() -> list[dict[str, float]]:
    return [
        {"name": "balanced", "base": 0.55, "reachable_boost": 0.35, "missing_penalty": 0.25, "incompat_penalty": 0.15},
        {"name": "base_heavy", "base": 0.75, "reachable_boost": 0.20, "missing_penalty": 0.20, "incompat_penalty": 0.10},
        {"name": "constraint_heavy", "base": 0.45, "reachable_boost": 0.45, "missing_penalty": 0.35, "incompat_penalty": 0.25},
    ]


def inverse_distance(distances: dict[str, int], nodes: list[str]) -> float:
    values = [1.0 / (1 + distances[node]) for node in nodes if node in distances]
    return max(values) if values else 0.0


def fraction_reachable(distances: dict[str, int], nodes: list[str]) -> float:
    if not nodes:
        return 1.0
    return len([node for node in nodes if node in distances]) / len(nodes)


def query_path_overlap(query: str, path: str) -> float:
    query_tokens = set(normalize_text(query).replace("/", " ").replace("{", " ").replace("}", " ").split())
    path_tokens = {
        token
        for token in normalize_text(path).replace("/", " ").replace("{", " ").replace("}", " ").split()
        if token
    }
    if not path_tokens:
        return 1.0
    return len(query_tokens & path_tokens) / len(path_tokens)


def grag_seed_docs_and_nodes(
    query: str,
    indices: RetrievalIndices,
    doc_top_n: int,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    seed_docs = indices.top_all_docs(query, doc_top_n)
    node_scores: dict[str, float] = {}
    for doc in seed_docs:
        for node_id in doc.get("graph_nodes", []):
            node_scores[node_id] = max(node_scores.get(node_id, 0.0), float(doc.get("score", 0.0)))
    return seed_docs, node_scores


def grag_expand_scores(
    query: str,
    indices: RetrievalIndices,
    config: dict[str, Any],
) -> tuple[dict[str, float], dict[str, Any]]:
    seed_docs, seed_nodes = grag_seed_docs_and_nodes(query, indices, int(config["doc_top_n"]))
    expanded = indices.expand_nodes(seed_nodes, int(config["hops"]))
    graph_scores = minmax(indices.endpoint_scores_from_graph_nodes(expanded))
    rag_seed_scores = minmax(
        {
            endpoint_id: max(
                [float(doc.get("score", 0.0)) for doc in seed_docs if doc.get("endpoint_id") == endpoint_id] or [0.0]
            )
            for endpoint_id in indices.endpoint_ids
        }
    )
    combined = {
        endpoint_id: float(config["rag_weight"]) * rag_seed_scores.get(endpoint_id, 0.0)
        + float(config["graph_weight"]) * graph_scores.get(endpoint_id, 0.0)
        for endpoint_id in indices.endpoint_ids
    }
    trace = {
        "seed_docs": [
            {"doc_id": doc.get("id"), "endpoint_id": doc.get("endpoint_id"), "kind": doc.get("kind"), "score": doc.get("score", 0.0)}
            for doc in seed_docs[:10]
        ],
        "seed_nodes": [{"node_id": node_id, "score": score} for node_id, score in sorted(seed_nodes.items(), key=lambda item: item[1], reverse=True)[:10]],
        "score_components": {
            endpoint_id: {"rag_seed": rag_seed_scores.get(endpoint_id, 0.0), "graph_expansion": graph_scores.get(endpoint_id, 0.0)}
            for endpoint_id in top_ids_from_scores(combined, 10)
        },
    }
    return minmax(combined), trace


def grag_features_for_endpoint(
    query: str,
    endpoint: Any,
    indices: RetrievalIndices,
    seed_nodes: dict[str, float],
    distances: dict[str, int],
) -> dict[str, float]:
    required = indices.endpoint_requirement_nodes(endpoint.id)
    endpoint_node = f"endpoint:{endpoint.id}"
    resource_nodes = required.get("resource", [])
    param_nodes = required.get("param", [])
    schema_nodes = required.get("request_schema", [])
    auth_nodes = required.get("auth", [])
    max_degree = max(indices.graph_degrees.values()) if indices.graph_degrees else 1
    return {
        "resource_match": fraction_reachable(distances, resource_nodes) if resource_nodes else 0.0,
        "param_match": fraction_reachable(distances, param_nodes),
        "schema_proximity": inverse_distance(distances, schema_nodes),
        "auth_proximity": fraction_reachable(distances, auth_nodes),
        "graph_distance": inverse_distance(distances, [endpoint_node]),
        "endpoint_degree": indices.graph_degrees.get(endpoint_node, 0) / max_degree,
        "operation_confidence": float(getattr(endpoint, "operation_confidence", 0.0)),
    }


def grag_rerank_scores(
    query: str,
    bundle: NormalizedBundle,
    indices: RetrievalIndices,
    score_maps: dict[str, dict[str, float]],
    weights: dict[str, float],
    candidate_k: int = 25,
) -> tuple[dict[str, float], dict[str, Any]]:
    seed_docs, seed_nodes = grag_seed_docs_and_nodes(query, indices, 20)
    distances = indices.shortest_distances(list(seed_nodes), max_hops=3)
    endpoint_by_id = {endpoint.id: endpoint for endpoint in bundle.endpoints}
    candidates = grag_candidate_union(score_maps, candidate_k)
    scores = {endpoint_id: 0.0 for endpoint_id in indices.endpoint_ids}
    feature_trace: dict[str, dict[str, float]] = {}
    for endpoint_id in candidates:
        endpoint = endpoint_by_id.get(endpoint_id)
        if endpoint is None:
            continue
        features = grag_features_for_endpoint(query, endpoint, indices, seed_nodes, distances)
        score = sum(float(weights.get(name, 0.0)) * features[name] for name in GRAG_RERANK_FEATURES)
        scores[endpoint_id] = score
        feature_trace[endpoint_id] = features
    trace = {
        "seed_docs": [{"doc_id": doc.get("id"), "score": doc.get("score", 0.0), "kind": doc.get("kind")} for doc in seed_docs[:10]],
        "seed_nodes": [{"node_id": node_id, "score": score} for node_id, score in sorted(seed_nodes.items(), key=lambda item: item[1], reverse=True)[:10]],
        "candidate_endpoints": candidates[:25],
        "graph_features": feature_trace,
    }
    return minmax(scores), trace


def grag_constrained_scores(
    query: str,
    bundle: NormalizedBundle,
    indices: RetrievalIndices,
    score_maps: dict[str, dict[str, float]],
    config: dict[str, float],
    candidate_k: int = 50,
) -> tuple[dict[str, float], dict[str, Any]]:
    seed_docs, seed_nodes = grag_seed_docs_and_nodes(query, indices, 20)
    distances = indices.shortest_distances(list(seed_nodes), max_hops=3)
    endpoint_by_id = {endpoint.id: endpoint for endpoint in bundle.endpoints}
    candidates = candidate_top_ids(score_maps["rag_all_max"], candidate_k)
    scores = {endpoint_id: 0.0 for endpoint_id in indices.endpoint_ids}
    constraints: dict[str, dict[str, float]] = {}
    for endpoint_id in candidates:
        endpoint = endpoint_by_id.get(endpoint_id)
        if endpoint is None:
            continue
        required = indices.endpoint_requirement_nodes(endpoint_id)
        param_reach = fraction_reachable(distances, required.get("param", []))
        schema_reach = fraction_reachable(distances, required.get("request_schema", []))
        auth_reach = fraction_reachable(distances, required.get("auth", []))
        resource_reach = fraction_reachable(distances, required.get("resource", [])) if required.get("resource") else 0.0
        path_overlap = query_path_overlap(query, endpoint.path)
        operation_match = 1.0 if endpoint.operation_class in normalize_text(query) else 0.0
        reachable_boost = (param_reach + schema_reach + auth_reach + resource_reach) / 4.0
        missing_penalty = 1.0 - ((param_reach + schema_reach + auth_reach) / 3.0)
        incompat_penalty = 1.0 if resource_reach == 0.0 and path_overlap == 0.0 and operation_match == 0.0 else 0.0
        base = score_maps["rag_all_max"].get(endpoint_id, 0.0)
        score = (
            float(config["base"]) * base
            + float(config["reachable_boost"]) * reachable_boost
            - float(config["missing_penalty"]) * missing_penalty
            - float(config["incompat_penalty"]) * incompat_penalty
        )
        scores[endpoint_id] = score
        constraints[endpoint_id] = {
            "base": base,
            "param_reachable": param_reach,
            "schema_reachable": schema_reach,
            "auth_reachable": auth_reach,
            "resource_reachable": resource_reach,
            "path_overlap": path_overlap,
            "operation_match": operation_match,
            "missing_penalty": missing_penalty,
            "incompat_penalty": incompat_penalty,
        }
    trace = {
        "seed_docs": [{"doc_id": doc.get("id"), "score": doc.get("score", 0.0), "kind": doc.get("kind")} for doc in seed_docs[:10]],
        "seed_nodes": [{"node_id": node_id, "score": score} for node_id, score in sorted(seed_nodes.items(), key=lambda item: item[1], reverse=True)[:10]],
        "candidate_endpoints": candidates[:25],
        "constraints": constraints,
        "score_components": constraints,
    }
    return minmax(scores), trace


def graph_config_metrics(
    config: GraphSparseConfig,
    tasks: list[dict[str, Any]],
    dev_ids: set[str],
    graph_scores_by_config: dict[str, dict[str, dict[str, float]]],
) -> dict[str, Any]:
    rows = [task for task in tasks if task["id"] in dev_ids]
    if not rows:
        return {
            **config.to_dict(),
            "dev_task_count": 0,
            "complete_plan_at_1": 0.0,
            "complete_plan_at_10": 0.0,
            "first_step_top1": 0.0,
        }
    score_by_task = graph_scores_by_config[config.name]
    complete_1 = []
    complete_10 = []
    first_1 = []
    for task in rows:
        scores = score_by_task[task["id"]]
        complete_1.append(complete_plan_for_ids(top_ids_from_scores(scores, 1), task))
        complete_10.append(complete_plan_for_ids(top_ids_from_scores(scores, 10), task))
        first_1.append(first_step_for_ids(top_ids_from_scores(scores, 1), task))
    return {
        **config.to_dict(),
        "dev_task_count": len(rows),
        "complete_plan_at_1": sum(complete_1) / len(complete_1),
        "complete_plan_at_10": sum(complete_10) / len(complete_10),
        "first_step_top1": sum(first_1) / len(first_1),
    }


def score_map_metrics_for_tasks(
    tasks: list[dict[str, Any]],
    score_by_task: dict[str, dict[str, float]],
    threshold: float,
) -> dict[str, float]:
    if not tasks:
        return {
            "task_count": 0,
            "complete_plan_at_1": 0.0,
            "complete_plan_at_10": 0.0,
            "first_step_top1": 0.0,
        }
    complete_1 = []
    complete_10 = []
    first_1 = []
    for task in tasks:
        scores = apply_abstention(score_by_task.get(task["id"], {}), threshold)
        complete_1.append(complete_plan_for_ids(top_ids_from_scores(scores, 1), task))
        complete_10.append(complete_plan_for_ids(top_ids_from_scores(scores, 10), task))
        first_1.append(first_step_for_ids(top_ids_from_scores(scores, 1), task))
    return {
        "task_count": len(tasks),
        "complete_plan_at_1": sum(complete_1) / len(complete_1),
        "complete_plan_at_10": sum(complete_10) / len(complete_10),
        "first_step_top1": sum(first_1) / len(first_1),
    }


def select_hybrid_weights(
    tasks: list[dict[str, Any]],
    tasks_by_id: dict[str, dict[str, Any]],
    dev_ids: set[str],
    eval_ids: set[str],
    scoped_precomputed: dict[str, dict[str, dict[str, float]]],
    endpoint_ids: list[str],
) -> tuple[dict[str, float], list[dict[str, Any]], dict[str, Any]]:
    dev_tasks = [tasks_by_id[task_id] for task_id in sorted(dev_ids) if task_id in tasks_by_id]
    eval_tasks = [tasks_by_id[task_id] for task_id in sorted(eval_ids) if task_id in tasks_by_id]
    rows: list[dict[str, Any]] = []
    selected_weights = dict(DEFAULT_HYBRID_WEIGHTS)
    selected_score_by_task: dict[str, dict[str, float]] = {}
    selected_threshold = 0.0
    for weights in hybrid_weight_grid():
        score_by_task = {
            task["id"]: weighted_score_sum(scoped_precomputed[task["id"]], weights, endpoint_ids)
            for task in dev_tasks
        }
        threshold = calibrate_threshold(tasks_by_id, dev_ids, score_by_task)
        dev_metrics = score_map_metrics_for_tasks(dev_tasks, score_by_task, threshold)
        row = {
            "name": hybrid_config_name(weights),
            "weights": weights,
            "threshold": threshold,
            "dev_task_count": dev_metrics["task_count"],
            "complete_plan_at_1": dev_metrics["complete_plan_at_1"],
            "complete_plan_at_10": dev_metrics["complete_plan_at_10"],
            "first_step_top1": dev_metrics["first_step_top1"],
        }
        rows.append(row)
    if rows:
        selected_row = max(
            rows,
            key=lambda row: (
                row["complete_plan_at_1"],
                row["complete_plan_at_10"],
                row["first_step_top1"],
                str(row["name"]),
            ),
        )
        selected_weights = dict(selected_row["weights"])
        selected_score_by_task = {
            task["id"]: weighted_score_sum(scoped_precomputed[task["id"]], selected_weights, endpoint_ids)
            for task in tasks
        }
        selected_threshold = calibrate_threshold(tasks_by_id, dev_ids, selected_score_by_task)
        eval_metrics = score_map_metrics_for_tasks(eval_tasks, selected_score_by_task, selected_threshold)
        for row in rows:
            row["selected"] = row["weights"] == selected_weights
        selection = {
            "selected_weights": selected_weights,
            "selected_config": selected_row["name"],
            "threshold": selected_threshold,
            "dev_metrics": {
                "task_count": selected_row["dev_task_count"],
                "complete_plan_at_1": selected_row["complete_plan_at_1"],
                "complete_plan_at_10": selected_row["complete_plan_at_10"],
                "first_step_top1": selected_row["first_step_top1"],
            },
            "held_out_metrics": eval_metrics,
        }
        return selected_weights, rows, selection
    selection = {
        "selected_weights": selected_weights,
        "selected_config": hybrid_config_name(selected_weights),
        "threshold": 0.0,
        "dev_metrics": score_map_metrics_for_tasks(dev_tasks, {}, 0.0),
        "held_out_metrics": score_map_metrics_for_tasks(eval_tasks, {}, 0.0),
    }
    return selected_weights, rows, selection


def config_metrics(
    config: dict[str, Any],
    tasks: list[dict[str, Any]],
    dev_ids: set[str],
    score_by_config: dict[str, dict[str, dict[str, float]]],
) -> dict[str, Any]:
    dev_tasks = [task for task in tasks if task["id"] in dev_ids]
    score_by_task = score_by_config[str(config["name"])]
    threshold = calibrate_threshold({task["id"]: task for task in tasks}, dev_ids, score_by_task)
    metrics = score_map_metrics_for_tasks(dev_tasks, score_by_task, threshold)
    return {
        **config,
        "threshold": threshold,
        "dev_task_count": metrics["task_count"],
        "complete_plan_at_1": metrics["complete_plan_at_1"],
        "complete_plan_at_10": metrics["complete_plan_at_10"],
        "first_step_top1": metrics["first_step_top1"],
    }


def select_named_config(
    configs: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    dev_ids: set[str],
    score_by_config: dict[str, dict[str, dict[str, float]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = [config_metrics(config, tasks, dev_ids, score_by_config) for config in configs]
    selected = max(
        rows,
        key=lambda row: (
            row["complete_plan_at_1"],
            row["complete_plan_at_10"],
            row["first_step_top1"],
            str(row["name"]),
        ),
    )
    for row in rows:
        row["selected"] = row["name"] == selected["name"]
    return selected, rows


def select_graph_config(
    configs: list[GraphSparseConfig],
    tasks: list[dict[str, Any]],
    dev_ids: set[str],
    graph_scores_by_config: dict[str, dict[str, dict[str, float]]],
) -> tuple[GraphSparseConfig, list[dict[str, Any]]]:
    metrics = [graph_config_metrics(config, tasks, dev_ids, graph_scores_by_config) for config in configs]
    selected_row = max(
        metrics,
        key=lambda row: (
            row["complete_plan_at_1"],
            row["complete_plan_at_10"],
            row["first_step_top1"],
            str(row["name"]),
        ),
    )
    selected = next(config for config in configs if config.name == selected_row["name"])
    return selected, metrics


def compute_scores_for_query(
    query: str,
    indices: RetrievalIndices,
    graph_config: GraphSparseConfig | None = None,
    graph_seed_scores: np.ndarray | None = None,
    graph_scores_override: dict[str, float] | None = None,
) -> dict[str, dict[str, float]]:
    graph_config = graph_config or DEFAULT_GRAPH_SPARSE_CONFIG
    if graph_scores_override is not None:
        graph_scores = graph_scores_override
    else:
        graph_scores = (
            indices.graph_sparse_scores_from_seed(graph_seed_scores, config=graph_config)
            if graph_seed_scores is not None
            else indices.graph_sparse_scores(query, config=graph_config)
        )
    scores = {
        "rag_endpoint": minmax(indices.tfidf_endpoint_scores(query)),
        "rag_all_max": minmax(indices.tfidf_all_scores(query, pooling="max")),
        "rag_all_mean": minmax(indices.tfidf_all_scores(query, pooling="mean")),
        "rag_all_top3": minmax(indices.tfidf_all_scores(query, pooling="top3")),
        "bm25_all_max": minmax(indices.bm25_all_scores(query, pooling="max")),
        "bm25_all_mean": minmax(indices.bm25_all_scores(query, pooling="mean")),
        "bm25_all_top3": minmax(indices.bm25_all_scores(query, pooling="top3")),
        "graph_text": minmax(indices.graph_text_scores(query)),
        "graph_sparse": minmax(graph_scores),
        "schema_param": minmax(indices.param_schema_scores(query)),
    }
    scores["hybrid"] = weighted_score_sum(scores, DEFAULT_HYBRID_WEIGHTS, indices.endpoint_ids)
    return scores


def feature_row(query: str, endpoint: Any, score_maps: dict[str, dict[str, float]]) -> list[float]:
    q = normalize_text(query)
    endpoint_text = normalize_text(" ".join([endpoint.operation_id, endpoint.summary, endpoint.path, " ".join(endpoint.resources)]))
    overlap = len(set(q.split()) & set(endpoint_text.split()))
    return [
        score_maps["rag_endpoint"].get(endpoint.id, 0.0),
        score_maps["rag_all_max"].get(endpoint.id, 0.0),
        score_maps["rag_all_top3"].get(endpoint.id, 0.0),
        score_maps["bm25_all_max"].get(endpoint.id, 0.0),
        score_maps["bm25_all_top3"].get(endpoint.id, 0.0),
        score_maps["graph_sparse"].get(endpoint.id, 0.0),
        score_maps["graph_text"].get(endpoint.id, 0.0),
        score_maps["schema_param"].get(endpoint.id, 0.0),
        score_maps["hybrid"].get(endpoint.id, 0.0),
        1.0 if endpoint.operation_class in q else 0.0,
        float(overlap),
        float(len(endpoint.required_params)),
        float(len(endpoint.request_schemas)),
        float(len(endpoint.response_schemas)),
        endpoint.operation_confidence,
    ]


def feature_rows_for_task(
    query: str,
    bundle: NormalizedBundle,
    score_maps: dict[str, dict[str, float]],
) -> list[list[float]]:
    q = normalize_text(query)
    query_tokens = set(q.split())
    rows: list[list[float]] = []
    for endpoint in bundle.endpoints:
        endpoint_text = normalize_text(
            " ".join([endpoint.operation_id, endpoint.summary, endpoint.path, " ".join(endpoint.resources)])
        )
        overlap = len(query_tokens & set(endpoint_text.split()))
        rows.append(
            [
                score_maps["rag_endpoint"].get(endpoint.id, 0.0),
                score_maps["rag_all_max"].get(endpoint.id, 0.0),
                score_maps["rag_all_top3"].get(endpoint.id, 0.0),
                score_maps["bm25_all_max"].get(endpoint.id, 0.0),
                score_maps["bm25_all_top3"].get(endpoint.id, 0.0),
                score_maps["graph_sparse"].get(endpoint.id, 0.0),
                score_maps["graph_text"].get(endpoint.id, 0.0),
                score_maps["schema_param"].get(endpoint.id, 0.0),
                score_maps["hybrid"].get(endpoint.id, 0.0),
                1.0 if endpoint.operation_class in q else 0.0,
                float(overlap),
                float(len(endpoint.required_params)),
                float(len(endpoint.request_schemas)),
                float(len(endpoint.response_schemas)),
                endpoint.operation_confidence,
            ]
        )
    return rows


def feature_indices(feature_names: list[str]) -> list[int]:
    return [FEATURE_NAMES.index(name) for name in feature_names]


def apply_feature_mask(rows: list[list[float]], feature_names: list[str]) -> list[list[float]]:
    indices = feature_indices(feature_names)
    return [[row[index] for index in indices] for row in rows]


def centroid_scores(
    training_rows: list[list[float]],
    labels: list[int],
    query_rows: list[list[float]],
    endpoint_ids: list[str],
) -> dict[str, float]:
    matrix = np.asarray(training_rows, dtype=float)
    query = np.asarray(query_rows, dtype=float)
    positive = matrix[np.asarray(labels) == 1]
    negative = matrix[np.asarray(labels) == 0]
    if positive.size == 0 or negative.size == 0:
        raw = query[:, 4] if len(query) else np.array([])
    else:
        pos = positive.mean(axis=0)
        neg = negative.mean(axis=0)
        weights = pos - neg
        denom = np.linalg.norm(weights) or 1.0
        raw = query @ (weights / denom)
    lo = float(raw.min()) if len(raw) else 0.0
    hi = float(raw.max()) if len(raw) else 1.0
    if math.isclose(lo, hi):
        scaled = np.ones_like(raw)
    else:
        scaled = (raw - lo) / (hi - lo)
    return {endpoint_id: float(score) for endpoint_id, score in zip(endpoint_ids, scaled)}


def train_centroid_weights(
    train_tasks: list[dict[str, Any]],
    bundle: NormalizedBundle,
    precomputed: dict[str, dict[str, dict[str, float]]],
    feature_names: list[str] | None = None,
    feature_rows_by_task: dict[str, list[list[float]]] | None = None,
) -> np.ndarray | None:
    training_rows: list[list[float]] = []
    labels: list[int] = []
    for task in train_tasks:
        expected = set(task.get("expected_endpoint_sequence", []))
        maps = precomputed[task["id"]]
        rows = feature_rows_by_task.get(task["id"]) if feature_rows_by_task else None
        if rows is None:
            rows = feature_rows_for_task(task_query(task), bundle, maps)
        for endpoint, row in zip(bundle.endpoints, rows):
            training_rows.append(row)
            labels.append(1 if endpoint.id in expected else 0)
    if feature_names is not None:
        training_rows = apply_feature_mask(training_rows, feature_names)
    if len(set(labels)) < 2:
        return None
    matrix = np.asarray(training_rows, dtype=float)
    positive = matrix[np.asarray(labels) == 1]
    negative = matrix[np.asarray(labels) == 0]
    if positive.size == 0 or negative.size == 0:
        return None
    weights = positive.mean(axis=0) - negative.mean(axis=0)
    denom = np.linalg.norm(weights) or 1.0
    return weights / denom


def learned_scores_for_task(
    query_task: dict[str, Any],
    bundle: NormalizedBundle,
    precomputed: dict[str, dict[str, dict[str, float]]],
    weights: np.ndarray | None,
    feature_names: list[str] | None = None,
    feature_rows_by_task: dict[str, list[list[float]]] | None = None,
) -> dict[str, float]:
    if weights is None:
        return precomputed[query_task["id"]]["hybrid"]
    query_maps = precomputed[query_task["id"]]
    rows = feature_rows_by_task.get(query_task["id"]) if feature_rows_by_task else None
    if rows is None:
        rows = feature_rows_for_task(task_query(query_task), bundle, query_maps)
    if feature_names is not None:
        rows = apply_feature_mask(rows, feature_names)
    query_rows = np.asarray(rows, dtype=float)
    raw = query_rows @ weights
    lo = float(raw.min()) if len(raw) else 0.0
    hi = float(raw.max()) if len(raw) else 1.0
    if math.isclose(lo, hi):
        scaled = np.ones_like(raw)
    else:
        scaled = (raw - lo) / (hi - lo)
    return {endpoint.id: float(score) for endpoint, score in zip(bundle.endpoints, scaled)}


def calibrate_threshold(
    tasks_by_id: dict[str, dict[str, Any]],
    dev_ids: set[str],
    score_by_task: dict[str, dict[str, float]],
) -> float:
    if not dev_ids:
        return -1e-9
    dev_rows: list[tuple[dict[str, Any], dict[str, float], float]] = []
    for task_id in dev_ids:
        scores = score_by_task.get(task_id, {})
        top = max(scores.values()) if scores else 0.0
        if task_id in tasks_by_id:
            dev_rows.append((tasks_by_id[task_id], scores, top))
    if not dev_rows:
        return -1e-9
    unique_scores = sorted({top for _task, _scores, top in dev_rows})
    candidates = [-1e-9, max(unique_scores) + 1e-9]
    candidates.extend(unique_scores)
    candidates.extend(
        (left + right) / 2
        for left, right in zip(unique_scores, unique_scores[1:])
        if not math.isclose(left, right)
    )
    best_threshold = -1e-9
    best_key = (-1.0, -1.0, 0.0, -1.0)
    for threshold in sorted(set(candidates)):
        complete_scores = []
        first_step_scores = []
        abstention_scores = []
        for task, scores, _top in dev_rows:
            thresholded = apply_abstention(scores, threshold)
            top_ids = top_ids_from_scores(thresholded, 1)
            complete_scores.append(complete_plan_for_ids(top_ids, task))
            first_step_scores.append(first_step_for_ids(top_ids, task))
            should_abstain = task.get("task_type") in {"policy_required", "ambiguous"} and not task.get("expected_endpoint_sequence")
            if should_abstain:
                abstention_scores.append(1.0 if not top_ids else 0.0)
            else:
                abstention_scores.append(1.0)
        key = (
            sum(complete_scores) / len(complete_scores),
            sum(first_step_scores) / len(first_step_scores),
            -threshold,
            sum(abstention_scores) / len(abstention_scores),
        )
        if key > best_key:
            best_key = key
            best_threshold = threshold
    return best_threshold


def apply_abstention(scores: dict[str, float], threshold: float) -> dict[str, float]:
    if not scores:
        return scores
    if max(scores.values()) <= threshold:
        return {}
    return scores


def rank_all_baselines(
    query: str,
    bundle: NormalizedBundle,
    corpus: RagCorpus,
    graph: GraphArtifacts,
    tasks: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    indices = build_retrieval_indices(bundle, corpus, graph)
    started = time.perf_counter()
    scores = compute_scores_for_query(query, indices)
    scores["grag_expand"], _expand_trace = grag_expand_scores(query, indices, grag_expand_grid()[0])
    scores["grag_rerank"], _rerank_trace = grag_rerank_scores(query, bundle, indices, scores, rerank_weight_grid()[-1])
    scores["grag_constrained"], _constrained_trace = grag_constrained_scores(query, bundle, indices, scores, constrained_grid()[0])
    latency_ms = (time.perf_counter() - started) * 1000
    scores["learned"] = scores["hybrid"]
    for baseline in LEARNED_BASELINES:
        scores[baseline] = scores["hybrid"]
    scores[LEARNED_ALIAS] = scores["learned_all"]
    metadata_by_id = {
        endpoint.id: endpoint_metadata_for_endpoint(endpoint)
        for endpoint in bundle.endpoints
    }
    return {
        baseline: rank_from_scores(bundle, scores[baseline], latency_ms, metadata_by_id=metadata_by_id)
        for baseline in BASELINE_NAMES
    }


def rank_tasks(
    tasks: list[dict[str, Any]],
    bundle: NormalizedBundle,
    corpus: RagCorpus,
    graph: GraphArtifacts,
    splits: dict[str, Any] | None = None,
    include_diagnostics: bool = False,
) -> dict[str, dict[str, dict[str, list[dict[str, Any]]]]] | tuple[dict[str, dict[str, dict[str, list[dict[str, Any]]]]], dict[str, Any]]:
    indices = build_retrieval_indices(bundle, corpus, graph)
    metadata_by_id = {
        endpoint.id: endpoint_metadata_for_endpoint(endpoint)
        for endpoint in bundle.endpoints
    }
    tasks_by_id = {task["id"]: task for task in tasks}
    contexts = training_contexts(tasks, splits)
    base_precomputed: dict[str, dict[str, dict[str, float]]] = {}
    graph_configs = graph_sparse_config_grid()
    graph_scores_by_config: dict[str, dict[str, dict[str, float]]] = {
        config.name: {}
        for config in graph_configs
    }
    grag_expand_configs = grag_expand_grid()
    rerank_configs = rerank_weight_grid()
    constrained_configs = constrained_grid()
    grag_expand_scores_by_config: dict[str, dict[str, dict[str, float]]] = {config["name"]: {} for config in grag_expand_configs}
    grag_rerank_scores_by_config: dict[str, dict[str, dict[str, float]]] = {config["name"]: {} for config in rerank_configs}
    grag_constrained_scores_by_config: dict[str, dict[str, dict[str, float]]] = {config["name"]: {} for config in constrained_configs}
    grag_traces: dict[str, dict[str, dict[str, dict[str, Any]]]] = {
        "grag_expand": {config["name"]: {} for config in grag_expand_configs},
        "grag_rerank": {config["name"]: {} for config in rerank_configs},
        "grag_constrained": {config["name"]: {} for config in constrained_configs},
    }
    latencies: dict[str, dict[str, float]] = {}
    task_ids = [task["id"] for task in tasks]
    task_queries = [task_query(task) for task in tasks]
    graph_seed_matrix = indices.graph_seed_score_matrix(task_queries)
    for config in graph_configs:
        score_matrix = indices.graph_sparse_score_matrix_from_seed(graph_seed_matrix, config=config)
        for row_index, task_id in enumerate(task_ids):
            graph_scores_by_config[config.name][task_id] = endpoint_scores_from_row(indices.endpoint_ids, score_matrix[row_index])

    for row_index, task in enumerate(tasks):
        started = time.perf_counter()
        base_precomputed[task["id"]] = compute_scores_for_query(
            task_query(task),
            indices,
            graph_config=DEFAULT_GRAPH_SPARSE_CONFIG,
            graph_seed_scores=graph_seed_matrix[row_index],
            graph_scores_override=graph_scores_by_config[DEFAULT_GRAPH_SPARSE_CONFIG.name][task["id"]],
        )
        elapsed = (time.perf_counter() - started) * 1000
        latencies[task["id"]] = {baseline: elapsed for baseline in base_precomputed[task["id"]]}

    for config in grag_expand_configs:
        for task in tasks:
            scores, trace = grag_expand_scores(task_query(task), indices, config)
            grag_expand_scores_by_config[str(config["name"])][task["id"]] = scores
            grag_traces["grag_expand"][str(config["name"])][task["id"]] = trace
    for config in rerank_configs:
        weights = {name: float(config[name]) for name in GRAG_RERANK_FEATURES}
        for task in tasks:
            scores, trace = grag_rerank_scores(task_query(task), bundle, indices, base_precomputed[task["id"]], weights)
            grag_rerank_scores_by_config[str(config["name"])][task["id"]] = scores
            grag_traces["grag_rerank"][str(config["name"])][task["id"]] = trace
    for config in constrained_configs:
        for task in tasks:
            scores, trace = grag_constrained_scores(task_query(task), bundle, indices, base_precomputed[task["id"]], config)
            grag_constrained_scores_by_config[str(config["name"])][task["id"]] = scores
            grag_traces["grag_constrained"][str(config["name"])][task["id"]] = trace

    rankings: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {
        baseline: defaultdict(dict) for baseline in BASELINE_NAMES
    }
    diagnostics: dict[str, Any] = {
        "graph_sparse_ablation": [],
        "graph_sparse_selected_configs": {},
        "graph_sparse_diagnostics": [],
        "graph_sparse_stability": {},
        "hybrid_weight_selection": {},
        "hybrid_weight_ablation": [],
        "learned_ablations": {
            baseline: {"features": FEATURE_GROUPS[baseline]}
            for baseline in LEARNED_BASELINES
        },
        "grag_expand_selection": {},
        "grag_rerank_selection": {},
        "grag_constrained_selection": {},
        "grag_expand_ablation": [],
        "grag_rerank_ablation": [],
        "grag_constrained_ablation": [],
        "grag_diagnostics": [],
    }

    for scope, context in contexts.items():
        eval_ids = context["eval"]
        selected_graph_config, ablation_rows = select_graph_config(graph_configs, tasks, context["dev"], graph_scores_by_config)
        selected_expand_config, expand_rows = select_named_config(grag_expand_configs, tasks, context["dev"], grag_expand_scores_by_config)
        selected_rerank_config, rerank_rows = select_named_config(rerank_configs, tasks, context["dev"], grag_rerank_scores_by_config)
        selected_constrained_config, constrained_rows = select_named_config(constrained_configs, tasks, context["dev"], grag_constrained_scores_by_config)
        diagnostics["grag_expand_selection"][scope] = selected_expand_config
        diagnostics["grag_rerank_selection"][scope] = {
            **selected_rerank_config,
            "selected_weights": {name: selected_rerank_config[name] for name in GRAG_RERANK_FEATURES},
        }
        diagnostics["grag_constrained_selection"][scope] = selected_constrained_config
        diagnostics["grag_expand_ablation"].extend({**row, "split": scope} for row in expand_rows)
        diagnostics["grag_rerank_ablation"].extend({**row, "split": scope} for row in rerank_rows)
        diagnostics["grag_constrained_ablation"].extend({**row, "split": scope} for row in constrained_rows)
        diagnostics["graph_sparse_selected_configs"][scope] = selected_graph_config.to_dict()
        for row in ablation_rows:
            diagnostics["graph_sparse_ablation"].append({**row, "split": scope, "selected": row["name"] == selected_graph_config.name})
        scoped_precomputed: dict[str, dict[str, dict[str, float]]] = {}
        for task in tasks:
            maps = dict(base_precomputed[task["id"]])
            maps["graph_sparse"] = graph_scores_by_config[selected_graph_config.name][task["id"]]
            maps["grag_expand"] = grag_expand_scores_by_config[str(selected_expand_config["name"])][task["id"]]
            maps["grag_rerank"] = grag_rerank_scores_by_config[str(selected_rerank_config["name"])][task["id"]]
            maps["grag_constrained"] = grag_constrained_scores_by_config[str(selected_constrained_config["name"])][task["id"]]
            scoped_precomputed[task["id"]] = maps
        selected_hybrid_weights, hybrid_rows, hybrid_selection = select_hybrid_weights(
            tasks,
            tasks_by_id,
            context["dev"],
            eval_ids,
            scoped_precomputed,
            indices.endpoint_ids,
        )
        diagnostics["hybrid_weight_selection"][scope] = hybrid_selection
        for row in hybrid_rows:
            diagnostics["hybrid_weight_ablation"].append({**row, "split": scope})
        for task in tasks:
            scoped_precomputed[task["id"]]["hybrid"] = weighted_score_sum(
                scoped_precomputed[task["id"]],
                selected_hybrid_weights,
                indices.endpoint_ids,
            )
        feature_rows_by_task = {
            task["id"]: feature_rows_for_task(task_query(task), bundle, scoped_precomputed[task["id"]])
            for task in tasks
        }
        train_tasks = [tasks_by_id[task_id] for task_id in sorted(context["train"]) if task_id in tasks_by_id]
        learned_score_by_baseline: dict[str, dict[str, dict[str, float]]] = {}
        for learned_baseline in LEARNED_BASELINES:
            features = FEATURE_GROUPS[learned_baseline]
            learned_weights = train_centroid_weights(
                train_tasks,
                bundle,
                scoped_precomputed,
                feature_names=features,
                feature_rows_by_task=feature_rows_by_task,
            )
            learned_score_by_task: dict[str, dict[str, float]] = {}
            for task_id in sorted(set(eval_ids) | set(context["dev"])):
                if task_id in tasks_by_id:
                    learned_score_by_task[task_id] = learned_scores_for_task(
                        tasks_by_id[task_id],
                        bundle,
                        scoped_precomputed,
                        learned_weights,
                        feature_names=features,
                        feature_rows_by_task=feature_rows_by_task,
                    )
            learned_score_by_baseline[learned_baseline] = learned_score_by_task
        learned_score_by_baseline[LEARNED_ALIAS] = learned_score_by_baseline["learned_all"]

        threshold_by_baseline: dict[str, float] = {}
        for baseline in BASELINE_NAMES:
            if baseline in learned_score_by_baseline:
                threshold_by_baseline[baseline] = calibrate_threshold(tasks_by_id, context["dev"], learned_score_by_baseline[baseline])
            else:
                threshold_by_baseline[baseline] = calibrate_threshold(
                    tasks_by_id,
                    context["dev"],
                    {task_id: scoped_precomputed[task_id][baseline] for task_id in context["dev"] if task_id in scoped_precomputed and baseline in scoped_precomputed[task_id]},
                )

        for task_id in sorted(eval_ids):
            if task_id not in tasks_by_id:
                continue
            for baseline in BASELINE_NAMES:
                if baseline in learned_score_by_baseline:
                    score_map = learned_score_by_baseline[baseline].get(task_id, {})
                    latency_ms = 0.0
                else:
                    score_map = scoped_precomputed[task_id][baseline]
                    latency_ms = latencies[task_id].get(baseline, 0.0)
                score_map = apply_abstention(score_map, threshold_by_baseline[baseline])
                rankings[baseline][scope][task_id] = (
                    rank_from_scores(bundle, score_map, latency_ms, metadata_by_id=metadata_by_id)
                    if score_map
                    else []
                )
            graph_ranked = rankings["graph_sparse"][scope].get(task_id, [])
            for baseline, selected_config in [
                ("grag_expand", selected_expand_config),
                ("grag_rerank", selected_rerank_config),
                ("grag_constrained", selected_constrained_config),
            ]:
                ranked = rankings[baseline][scope].get(task_id, [])
                top_ids_for_baseline = [item["endpoint_id"] for item in ranked[:1]]
                if complete_plan_for_ids(top_ids_for_baseline, tasks_by_id[task_id]) < 1.0:
                    trace = grag_traces[baseline][str(selected_config["name"])][task_id]
                    diagnostics["grag_diagnostics"].append(
                        {
                            "baseline": baseline,
                            "task_id": task_id,
                            "split": scope,
                            "router_query": task_query(tasks_by_id[task_id]),
                            "selected_config": selected_config,
                            "expected_endpoint_sequence": tasks_by_id[task_id].get("expected_endpoint_sequence", []),
                            "top_ranked_endpoints": [
                                {"endpoint_id": item["endpoint_id"], "score": item.get("score", 0.0)}
                                for item in ranked[:10]
                            ],
                            **trace,
                        }
                    )
            top_ids = [item["endpoint_id"] for item in graph_ranked[:1]]
            if complete_plan_for_ids(top_ids, tasks_by_id[task_id]) < 1.0:
                trace = indices.graph_sparse_trace(task_query(tasks_by_id[task_id]), config=selected_graph_config)
                diagnostics["graph_sparse_diagnostics"].append(
                    {
                        "task_id": task_id,
                        "split": scope,
                        "router_query": task_query(tasks_by_id[task_id]),
                        "expected_endpoint_sequence": tasks_by_id[task_id].get("expected_endpoint_sequence", []),
                        "top_ranked_endpoints": [
                            {"endpoint_id": item["endpoint_id"], "score": item.get("score", 0.0)}
                            for item in graph_ranked[:10]
                        ],
                        "selected_config": selected_graph_config.to_dict(),
                        "top_seed_nodes": trace["top_seed_nodes"],
                        "high_degree_seed_nodes": trace.get("high_degree_seed_nodes", []),
                        "top_high_degree_nodes": trace.get("top_high_degree_nodes", []),
                        "propagated_endpoint_scores": trace["propagated_endpoint_scores"],
                        "endpoint_projection": trace.get("endpoint_projection", []),
                    }
                )

    final_rankings = {baseline: dict(scopes) for baseline, scopes in rankings.items()}
    selected_names = [
        row.get("name", "")
        for row in diagnostics["graph_sparse_selected_configs"].values()
    ]
    diagnostics["graph_sparse_stability"] = {
        "selected_config_frequency": dict(Counter(selected_names)),
        "selected_by_scope": diagnostics["graph_sparse_selected_configs"],
        "scope_count": len(selected_names),
    }
    if include_diagnostics:
        return final_rankings, diagnostics
    return final_rankings
