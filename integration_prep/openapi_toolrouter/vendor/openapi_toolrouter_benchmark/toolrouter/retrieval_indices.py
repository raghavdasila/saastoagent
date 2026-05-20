from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .graphgen import GraphArtifacts
from .openapi_loader import NormalizedBundle, normalize_text
from .raggen import RagCorpus


def make_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True, strip_accents="unicode", norm="l2")


def tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", normalize_text(value))


def minmax(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    lo = min(values.values())
    hi = max(values.values())
    if np.isclose(lo, hi):
        return {key: 1.0 for key in values}
    return {key: (value - lo) / (hi - lo) for key, value in values.items()}


def pool_doc_scores(doc_scores: list[tuple[str, float]], endpoint_ids: list[str], pooling: str) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for endpoint_id, score in doc_scores:
        grouped[endpoint_id].append(float(score))
    pooled: dict[str, float] = {}
    for endpoint_id in endpoint_ids:
        scores = grouped.get(endpoint_id, [])
        if not scores:
            pooled[endpoint_id] = 0.0
        elif pooling == "max":
            pooled[endpoint_id] = max(scores)
        elif pooling == "mean":
            pooled[endpoint_id] = sum(scores) / len(scores)
        elif pooling == "top3":
            top = sorted(scores, reverse=True)[:3]
            pooled[endpoint_id] = sum(top) / len(top)
        else:
            raise ValueError(f"Unknown pooling mode: {pooling}")
    return pooled


@dataclass
class GraphSparseConfig:
    name: str
    seed_top_n: int = 200
    steps: int = 3
    damping: float = 0.85
    directed: bool = False
    edge_kind_weights: dict[str, float] = field(default_factory=dict)
    high_degree_downweight: bool = False
    endpoint_prior_weight: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "seed_top_n": self.seed_top_n,
            "steps": self.steps,
            "damping": self.damping,
            "directed": self.directed,
            "edge_kind_weights": self.edge_kind_weights,
            "high_degree_downweight": self.high_degree_downweight,
            "endpoint_prior_weight": self.endpoint_prior_weight,
        }


DEFAULT_GRAPH_SPARSE_CONFIG = GraphSparseConfig(name="default")


def graph_sparse_config_grid() -> list[GraphSparseConfig]:
    structural_weights = {
        "operates_on": 1.5,
        "requires_param": 1.4,
        "request_schema": 1.3,
        "response_schema": 1.2,
        "has_tag": 1.1,
        "references": 0.8,
        "has_method": 0.5,
    }
    configs = [DEFAULT_GRAPH_SPARSE_CONFIG]
    configs.extend(GraphSparseConfig(name=f"seed_{seed}", seed_top_n=seed) for seed in [50, 500])
    configs.extend(GraphSparseConfig(name=f"steps_{steps}", steps=steps) for steps in [1, 5])
    configs.extend(GraphSparseConfig(name=f"damping_{str(damping).replace('.', '_')}", damping=damping) for damping in [0.65, 0.95])
    configs.append(GraphSparseConfig(name="directed", directed=True))
    configs.append(GraphSparseConfig(name="weighted_structural", edge_kind_weights=structural_weights))
    configs.append(GraphSparseConfig(name="high_degree_downweight", high_degree_downweight=True))
    configs.extend(
        GraphSparseConfig(name=f"endpoint_prior_{str(weight).replace('.', '_')}", endpoint_prior_weight=weight)
        for weight in [0.25, 0.50]
    )
    return configs


@dataclass
class RetrievalIndices:
    endpoint_ids: list[str]
    endpoint_docs: list[dict[str, Any]]
    all_docs: list[dict[str, Any]]
    endpoint_vectorizer: TfidfVectorizer
    endpoint_matrix: Any
    all_doc_vectorizer: TfidfVectorizer
    all_doc_matrix: Any
    bm25: Any
    bm25_tokens: list[list[str]]
    graph_node_ids: list[str]
    graph_node_vectorizer: TfidfVectorizer
    graph_node_matrix: Any
    graph_adjacency: csr_matrix
    graph_edges: list[dict[str, Any]]
    endpoint_node_indices: dict[str, int]
    doc_to_graph_node_ids: dict[str, list[str]]
    endpoint_required_nodes: dict[str, dict[str, list[str]]]
    graph_neighbors: dict[str, set[str]]
    graph_degrees: dict[str, int]
    graph_text_endpoint_ids: list[str]
    graph_text_vectorizer: TfidfVectorizer
    graph_text_matrix: Any
    _adjacency_cache: dict[str, csr_matrix] = field(default_factory=dict)
    _all_doc_score_cache: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def tfidf_endpoint_scores(self, query: str) -> dict[str, float]:
        q_vec = self.endpoint_vectorizer.transform([normalize_text(query)])
        scores = cosine_similarity(q_vec, self.endpoint_matrix).ravel()
        return {doc["endpoint_id"]: float(score) for doc, score in zip(self.endpoint_docs, scores)}

    def tfidf_all_scores(self, query: str, pooling: str) -> dict[str, float]:
        q_vec = self.all_doc_vectorizer.transform([normalize_text(query)])
        scores = cosine_similarity(q_vec, self.all_doc_matrix).ravel()
        return pool_doc_scores(
            [(doc["endpoint_id"], float(score)) for doc, score in zip(self.all_docs, scores)],
            self.endpoint_ids,
            pooling,
        )

    def bm25_all_scores(self, query: str, pooling: str) -> dict[str, float]:
        raw_scores = self.bm25.get_scores(tokenize(query)) if self.bm25 else np.zeros(len(self.all_docs))
        return pool_doc_scores(
            [(doc["endpoint_id"], float(score)) for doc, score in zip(self.all_docs, raw_scores)],
            self.endpoint_ids,
            pooling,
        )

    def all_doc_scores(self, query: str) -> list[dict[str, Any]]:
        cache_key = normalize_text(query)
        if cache_key in self._all_doc_score_cache:
            return [dict(row) for row in self._all_doc_score_cache[cache_key]]
        q_vec = self.all_doc_vectorizer.transform([normalize_text(query)])
        scores = cosine_similarity(q_vec, self.all_doc_matrix).ravel()
        rows = [
            {**doc, "score": float(score), "graph_nodes": self.doc_graph_nodes(doc)}
            for doc, score in zip(self.all_docs, scores)
        ]
        self._all_doc_score_cache[cache_key] = [dict(row) for row in rows]
        return rows

    def top_all_docs(self, query: str, limit: int) -> list[dict[str, Any]]:
        rows = self.all_doc_scores(query)
        rows.sort(key=lambda row: (float(row["score"]), str(row["id"])), reverse=True)
        return rows[:limit]

    def doc_graph_nodes(self, doc: dict[str, Any]) -> list[str]:
        return list(self.doc_to_graph_node_ids.get(str(doc.get("id", "")), []))

    def param_schema_scores(self, query: str) -> dict[str, float]:
        q_vec = self.all_doc_vectorizer.transform([normalize_text(query)])
        scores = cosine_similarity(q_vec, self.all_doc_matrix).ravel()
        doc_scores = [
            (doc["endpoint_id"], float(score))
            for doc, score in zip(self.all_docs, scores)
            if doc.get("kind") in {"parameter", "request_schema", "response_schema", "auth"}
        ]
        return pool_doc_scores(doc_scores, self.endpoint_ids, pooling="top3")

    def graph_text_scores(self, query: str) -> dict[str, float]:
        q_vec = self.graph_text_vectorizer.transform([normalize_text(query)])
        scores = cosine_similarity(q_vec, self.graph_text_matrix).ravel()
        return {endpoint_id: float(score) for endpoint_id, score in zip(self.graph_text_endpoint_ids, scores)}

    def graph_seed_scores(self, query: str) -> np.ndarray:
        q_vec = self.graph_node_vectorizer.transform([normalize_text(query)])
        return cosine_similarity(q_vec, self.graph_node_matrix).ravel()

    def graph_seed_score_matrix(self, queries: list[str]) -> np.ndarray:
        q_matrix = self.graph_node_vectorizer.transform([normalize_text(query) for query in queries])
        return cosine_similarity(q_matrix, self.graph_node_matrix)

    def expand_nodes(self, seed_scores: dict[str, float], hops: int) -> dict[str, float]:
        scores: dict[str, float] = defaultdict(float)
        queue: deque[tuple[str, int, float]] = deque()
        for node_id, score in seed_scores.items():
            if node_id in self.graph_neighbors and score > 0:
                scores[node_id] = max(scores[node_id], float(score))
                queue.append((node_id, 0, float(score)))
        while queue:
            node_id, depth, score = queue.popleft()
            if depth >= hops:
                continue
            next_score = score / float(depth + 2)
            for neighbor in self.graph_neighbors.get(node_id, set()):
                if next_score <= scores.get(neighbor, 0.0):
                    continue
                scores[neighbor] = next_score
                queue.append((neighbor, depth + 1, next_score))
        return dict(scores)

    def endpoint_scores_from_graph_nodes(self, node_scores: dict[str, float]) -> dict[str, float]:
        endpoint_scores = {endpoint_id: 0.0 for endpoint_id in self.endpoint_ids}
        for node_id, score in node_scores.items():
            if node_id.startswith("endpoint:"):
                endpoint_id = node_id.removeprefix("endpoint:")
                if endpoint_id in endpoint_scores:
                    endpoint_scores[endpoint_id] = max(endpoint_scores[endpoint_id], float(score))
            for neighbor in self.graph_neighbors.get(node_id, set()):
                if neighbor.startswith("endpoint:"):
                    endpoint_id = neighbor.removeprefix("endpoint:")
                    if endpoint_id in endpoint_scores:
                        endpoint_scores[endpoint_id] = max(endpoint_scores[endpoint_id], float(score) * 0.75)
        return endpoint_scores

    def shortest_distances(self, seed_nodes: list[str], max_hops: int = 3) -> dict[str, int]:
        distances: dict[str, int] = {}
        queue: deque[tuple[str, int]] = deque()
        for node_id in seed_nodes:
            if node_id in self.graph_neighbors and node_id not in distances:
                distances[node_id] = 0
                queue.append((node_id, 0))
        while queue:
            node_id, depth = queue.popleft()
            if depth >= max_hops:
                continue
            for neighbor in self.graph_neighbors.get(node_id, set()):
                if neighbor in distances:
                    continue
                distances[neighbor] = depth + 1
                queue.append((neighbor, depth + 1))
        return distances

    def endpoint_requirement_nodes(self, endpoint_id: str) -> dict[str, list[str]]:
        return self.endpoint_required_nodes.get(endpoint_id, {"param": [], "request_schema": [], "auth": [], "resource": []})

    def adjacency_for_config(self, config: GraphSparseConfig) -> csr_matrix:
        if config.name == DEFAULT_GRAPH_SPARSE_CONFIG.name:
            return self.graph_adjacency
        if config.name not in self._adjacency_cache:
            self._adjacency_cache[config.name] = build_graph_adjacency(
                self.graph_edges,
                self.graph_node_ids,
                directed=config.directed,
                edge_kind_weights=config.edge_kind_weights,
                high_degree_downweight=config.high_degree_downweight,
            )
        return self._adjacency_cache[config.name]

    def graph_sparse_trace(
        self,
        query: str,
        config: GraphSparseConfig | None = None,
        seed_scores: np.ndarray | None = None,
    ) -> dict[str, Any]:
        config = config or DEFAULT_GRAPH_SPARSE_CONFIG
        if not self.graph_node_ids:
            return {
                "scores": {endpoint_id: 0.0 for endpoint_id in self.endpoint_ids},
                "top_seed_nodes": [],
                "propagated_endpoint_scores": [],
            }
        seed_scores = seed_scores if seed_scores is not None else self.graph_seed_scores(query)
        if config.seed_top_n and len(seed_scores) > config.seed_top_n:
            keep = np.argpartition(seed_scores, -config.seed_top_n)[-config.seed_top_n:]
            seeds = np.zeros_like(seed_scores)
            seeds[keep] = seed_scores[keep]
        else:
            seeds = seed_scores
        state = seeds.astype(float)
        frontier = state.copy()
        adjacency = self.adjacency_for_config(config)
        for _step in range(config.steps):
            frontier = config.damping * (adjacency.T @ frontier)
            state = state + frontier
        endpoint_scores = {
            endpoint_id: float(
                (1.0 - config.endpoint_prior_weight) * state[node_index]
                + config.endpoint_prior_weight * seed_scores[node_index]
            )
            for endpoint_id, node_index in self.endpoint_node_indices.items()
        }
        degrees = np.asarray(self.adjacency_for_config(config).sum(axis=1)).ravel()
        top_seed_indices = np.argsort(seed_scores)[::-1][:10]
        high_degree_indices = np.argsort(degrees)[::-1][:10]
        top_endpoint_scores = sorted(endpoint_scores.items(), key=lambda item: (item[1], item[0]), reverse=True)[:10]
        return {
            "scores": endpoint_scores,
            "top_seed_nodes": [
                {
                    "node_id": self.graph_node_ids[int(index)],
                    "score": float(seed_scores[int(index)]),
                }
                for index in top_seed_indices
                if seed_scores[int(index)] > 0
            ],
            "high_degree_seed_nodes": [
                {
                    "node_id": self.graph_node_ids[int(index)],
                    "degree": float(degrees[int(index)]),
                    "seed_score": float(seed_scores[int(index)]),
                }
                for index in high_degree_indices
                if seed_scores[int(index)] > 0
            ],
            "top_high_degree_nodes": [
                {
                    "node_id": self.graph_node_ids[int(index)],
                    "degree": float(degrees[int(index)]),
                }
                for index in high_degree_indices
            ],
            "propagated_endpoint_scores": [
                {"endpoint_id": endpoint_id, "score": float(score)}
                for endpoint_id, score in top_endpoint_scores
            ],
            "endpoint_projection": [
                {
                    "endpoint_id": endpoint_id,
                    "node_id": f"endpoint:{endpoint_id}",
                    "projected_score": float(score),
                    "seed_component": float(seed_scores[self.endpoint_node_indices[endpoint_id]]),
                    "propagated_component": float(score),
                }
                for endpoint_id, score in top_endpoint_scores
                if endpoint_id in self.endpoint_node_indices
            ],
        }

    def graph_sparse_scores(self, query: str, config: GraphSparseConfig | None = None) -> dict[str, float]:
        return self.graph_sparse_trace(query, config=config)["scores"]

    def graph_sparse_scores_from_seed(self, seed_scores: np.ndarray, config: GraphSparseConfig | None = None) -> dict[str, float]:
        return self.graph_sparse_trace("", config=config, seed_scores=seed_scores)["scores"]

    def graph_sparse_score_matrix_from_seed(
        self,
        seed_matrix: np.ndarray,
        config: GraphSparseConfig | None = None,
    ) -> np.ndarray:
        config = config or DEFAULT_GRAPH_SPARSE_CONFIG
        if not self.graph_node_ids:
            return np.zeros((seed_matrix.shape[0], len(self.endpoint_ids)), dtype=float)
        if config.seed_top_n and seed_matrix.shape[1] > config.seed_top_n:
            keep = np.argpartition(seed_matrix, -config.seed_top_n, axis=1)[:, -config.seed_top_n:]
            row_indices = np.repeat(np.arange(seed_matrix.shape[0]), keep.shape[1])
            col_indices = keep.ravel()
            data = seed_matrix[row_indices, col_indices]
            seeds = csr_matrix((data, (row_indices, col_indices)), shape=seed_matrix.shape)
        else:
            seeds = csr_matrix(seed_matrix)
        state = seeds.astype(float, copy=True)
        frontier = state.copy()
        adjacency = self.adjacency_for_config(config)
        for _step in range(config.steps):
            frontier = config.damping * (frontier @ adjacency)
            state = state + frontier
        output = np.zeros((seed_matrix.shape[0], len(self.endpoint_ids)), dtype=float)
        valid_columns = [
            (column, node_index)
            for column, endpoint_id in enumerate(self.endpoint_ids)
            if (node_index := self.endpoint_node_indices.get(endpoint_id)) is not None
        ]
        if valid_columns:
            columns, node_indices = zip(*valid_columns)
            projected = state[:, list(node_indices)].toarray()
            output[:, list(columns)] = projected
            if config.endpoint_prior_weight:
                seed_projected = seed_matrix[:, list(node_indices)]
                output[:, list(columns)] = (
                    (1.0 - config.endpoint_prior_weight) * output[:, list(columns)]
                    + config.endpoint_prior_weight * seed_projected
                )
        return output


def fit_vectorizer(texts: list[str]) -> tuple[TfidfVectorizer, Any]:
    vectorizer = make_vectorizer()
    matrix = vectorizer.fit_transform(texts or [""])
    return vectorizer, matrix


def build_graph_adjacency(
    edges: list[dict[str, Any]],
    node_ids: list[str],
    directed: bool = False,
    edge_kind_weights: dict[str, float] | None = None,
    high_degree_downweight: bool = False,
) -> csr_matrix:
    index = {node_id: idx for idx, node_id in enumerate(node_ids)}
    edge_kind_weights = edge_kind_weights or {}
    degree: defaultdict[int, int] = defaultdict(int)
    if high_degree_downweight:
        for edge in edges:
            source = index.get(edge["source"])
            target = index.get(edge["target"])
            if source is None or target is None:
                continue
            degree[source] += 1
            if not directed:
                degree[target] += 1
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for edge in edges:
        source = index.get(edge["source"])
        target = index.get(edge["target"])
        if source is None or target is None:
            continue
        weight = float(edge_kind_weights.get(edge.get("kind", ""), 1.0))
        if high_degree_downweight:
            weight = weight / np.sqrt(max(1, degree[source]))
        rows.append(source)
        cols.append(target)
        data.append(weight)
        if not directed:
            reverse_weight = float(edge_kind_weights.get(edge.get("kind", ""), 1.0))
            if high_degree_downweight:
                reverse_weight = reverse_weight / np.sqrt(max(1, degree[target]))
            rows.append(target)
            cols.append(source)
            data.append(reverse_weight)
    adjacency = csr_matrix((data, (rows, cols)), shape=(len(node_ids), len(node_ids)), dtype=float)
    row_sums = np.asarray(adjacency.sum(axis=1)).ravel()
    row_sums[row_sums == 0] = 1.0
    inv_rows = csr_matrix((1.0 / row_sums, (range(len(row_sums)), range(len(row_sums)))), shape=adjacency.shape)
    return inv_rows @ adjacency


def build_graph_text_docs(bundle: NormalizedBundle, graph: GraphArtifacts) -> tuple[list[str], list[str]]:
    node_text = {
        node["id"]: normalize_text(f"{node.get('label', '')} {node.get('text', '')} {node.get('kind', '')}")[:800]
        for node in graph.nodes
    }
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in graph.edges:
        adjacency[edge["source"]].add(edge["target"])
        adjacency[edge["target"]].add(edge["source"])
    endpoint_ids: list[str] = []
    texts: list[str] = []
    for endpoint in bundle.endpoints:
        endpoint_node = f"endpoint:{endpoint.id}"
        related = {endpoint_node}
        related.update(adjacency.get(endpoint_node, set()))
        endpoint_ids.append(endpoint.id)
        texts.append(" ".join(node_text.get(node_id, "") for node_id in related))
    return endpoint_ids, texts


def build_graph_neighbors(edges: list[dict[str, Any]]) -> tuple[dict[str, set[str]], dict[str, int]]:
    neighbors: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if not source or not target:
            continue
        neighbors[source].add(target)
        neighbors[target].add(source)
    degrees = {node_id: len(values) for node_id, values in neighbors.items()}
    return neighbors, degrees


def doc_schema_node_id(doc: dict[str, Any], kind: str) -> str | None:
    endpoint_id = str(doc.get("endpoint_id", ""))
    doc_id = str(doc.get("id", ""))
    prefix = f"{kind}:{endpoint_id}."
    if not doc_id.startswith(prefix):
        return None
    schema_name = doc_id.removeprefix(prefix)
    return f"schema:{schema_name}" if schema_name else None


def map_doc_to_graph_nodes(
    doc: dict[str, Any],
    endpoint_by_id: dict[str, Any],
    graph_node_ids: set[str],
) -> list[str]:
    kind = str(doc.get("kind", ""))
    doc_id = str(doc.get("id", ""))
    endpoint_id = str(doc.get("endpoint_id", ""))
    candidates: list[str] = []
    if kind == "endpoint":
        candidates.append(f"endpoint:{endpoint_id}")
    elif kind == "parameter":
        candidates.append(doc_id)
    elif kind in {"request_schema", "response_schema"}:
        schema_node = doc_schema_node_id(doc, kind)
        if schema_node:
            candidates.append(schema_node)
    elif kind == "auth":
        endpoint = endpoint_by_id.get(endpoint_id)
        if endpoint is not None:
            candidates.extend(f"auth:{scheme}" for scheme in endpoint.security)
    return [node_id for node_id in dict.fromkeys(candidates) if node_id in graph_node_ids]


def build_doc_graph_mapping(
    docs: list[dict[str, Any]],
    bundle: NormalizedBundle,
    graph_node_ids: set[str],
) -> dict[str, list[str]]:
    endpoint_by_id = {endpoint.id: endpoint for endpoint in bundle.endpoints}
    return {
        str(doc.get("id", "")): map_doc_to_graph_nodes(doc, endpoint_by_id, graph_node_ids)
        for doc in docs
    }


def build_endpoint_required_nodes(bundle: NormalizedBundle, graph_node_ids: set[str]) -> dict[str, dict[str, list[str]]]:
    required: dict[str, dict[str, list[str]]] = {}
    for endpoint in bundle.endpoints:
        param_nodes = [
            f"param:{endpoint.id}.{param.location}.{param.name}"
            for param in endpoint.params
            if param.required and f"param:{endpoint.id}.{param.location}.{param.name}" in graph_node_ids
        ]
        request_nodes = [
            f"schema:{schema_name}"
            for schema_name in endpoint.request_schemas
            if f"schema:{schema_name}" in graph_node_ids
        ]
        auth_nodes = [
            f"auth:{scheme}"
            for scheme in endpoint.security
            if f"auth:{scheme}" in graph_node_ids
        ]
        resource_nodes = [
            f"resource:{resource}"
            for resource in endpoint.resources
            if f"resource:{resource}" in graph_node_ids
        ]
        required[endpoint.id] = {
            "param": param_nodes,
            "request_schema": request_nodes,
            "auth": auth_nodes,
            "resource": resource_nodes,
        }
    return required


def build_retrieval_indices(bundle: NormalizedBundle, corpus: RagCorpus, graph: GraphArtifacts) -> RetrievalIndices:
    try:
        from rank_bm25 import BM25Okapi
    except ImportError as exc:
        raise RuntimeError("rank-bm25 is required for BM25 baselines") from exc

    endpoint_ids = [endpoint.id for endpoint in bundle.endpoints]
    endpoint_docs = [doc for doc in corpus.documents if doc["kind"] == "endpoint"]
    all_docs = list(corpus.documents)
    endpoint_vectorizer, endpoint_matrix = fit_vectorizer([normalize_text(doc["text"]) for doc in endpoint_docs])
    all_doc_vectorizer, all_doc_matrix = fit_vectorizer([normalize_text(doc["text"]) for doc in all_docs])
    bm25_tokens = [tokenize(doc["text"]) for doc in all_docs]
    bm25 = BM25Okapi(bm25_tokens) if bm25_tokens else None

    graph_node_ids = [node["id"] for node in graph.nodes]
    graph_node_id_set = set(graph_node_ids)
    graph_node_texts = [normalize_text(f"{node.get('label', '')} {node.get('text', '')} {node.get('kind', '')}") for node in graph.nodes]
    graph_node_vectorizer, graph_node_matrix = fit_vectorizer(graph_node_texts)
    graph_adjacency = build_graph_adjacency(graph.edges, graph_node_ids)
    node_index = {node_id: idx for idx, node_id in enumerate(graph_node_ids)}
    endpoint_node_indices = {
        endpoint.id: node_index[f"endpoint:{endpoint.id}"]
        for endpoint in bundle.endpoints
        if f"endpoint:{endpoint.id}" in node_index
    }

    graph_text_endpoint_ids, graph_texts = build_graph_text_docs(bundle, graph)
    graph_text_vectorizer, graph_text_matrix = fit_vectorizer(graph_texts)
    doc_to_graph_node_ids = build_doc_graph_mapping(all_docs, bundle, graph_node_id_set)
    endpoint_required_nodes = build_endpoint_required_nodes(bundle, graph_node_id_set)
    graph_neighbors, graph_degrees = build_graph_neighbors(graph.edges)

    return RetrievalIndices(
        endpoint_ids=endpoint_ids,
        endpoint_docs=endpoint_docs,
        all_docs=all_docs,
        endpoint_vectorizer=endpoint_vectorizer,
        endpoint_matrix=endpoint_matrix,
        all_doc_vectorizer=all_doc_vectorizer,
        all_doc_matrix=all_doc_matrix,
        bm25=bm25,
        bm25_tokens=bm25_tokens,
        graph_node_ids=graph_node_ids,
        graph_node_vectorizer=graph_node_vectorizer,
        graph_node_matrix=graph_node_matrix,
        graph_adjacency=graph_adjacency,
        graph_edges=graph.edges,
        endpoint_node_indices=endpoint_node_indices,
        doc_to_graph_node_ids=doc_to_graph_node_ids,
        endpoint_required_nodes=endpoint_required_nodes,
        graph_neighbors=graph_neighbors,
        graph_degrees=graph_degrees,
        graph_text_endpoint_ids=graph_text_endpoint_ids,
        graph_text_vectorizer=graph_text_vectorizer,
        graph_text_matrix=graph_text_matrix,
    )
