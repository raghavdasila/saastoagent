from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from .ladder_llm import stable_hash, write_llm_audit
from .semantic_graph import SemanticGraph, SemanticNodeCard


OPENAI_EMBEDDING_TOKEN_LIMIT = 8000
OPENAI_EMBEDDING_CHAR_FALLBACK_LIMIT = 12000


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        ...


class EndpointReranker(Protocol):
    def score(self, query: str, endpoint_ids: list[str], endpoint_texts: list[str]) -> np.ndarray:
        ...


class QueryExpander(Protocol):
    def expand(self, query: str) -> list[str]:
        ...


class SentenceTransformerEmbeddingProvider:
    def __init__(
        self,
        model_name: str,
        *,
        device: str = "cpu",
        batch_size: int = 64,
        revision: str | None = None,
        local_files_only: bool = False,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            raise RuntimeError("sentence_transformers provider requires sentence-transformers and torch.") from exc
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.revision = revision
        self.local_files_only = local_files_only
        self.model = SentenceTransformer(
            model_name,
            device=device,
            revision=revision,
            local_files_only=local_files_only,
        )

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            self.model.encode(
                texts,
                batch_size=self.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            ),
            dtype=np.float32,
        )


class OpenAIEmbeddingProvider:
    def __init__(self, *, api_key: str, model: str = "text-embedding-3-small", batch_size: int = 128) -> None:
        if not api_key:
            raise RuntimeError("OpenAIEmbeddingProvider requires a non-empty API key.")
        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("OpenAIEmbeddingProvider requires the openai package.") from exc
        self.model = model
        self.batch_size = batch_size
        self.client = OpenAI(api_key=api_key, timeout=120.0)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = [openai_embedding_safe_text(text, self.model) for text in texts[start : start + self.batch_size]]
            response = self.client.embeddings.create(model=self.model, input=batch)
            vectors.extend(item.embedding for item in sorted(response.data, key=lambda item: item.index))
        return _l2_normalize(np.asarray(vectors, dtype=np.float32))


def openai_embedding_safe_text(text: str, model: str) -> str:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return " "
    try:
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(normalized)
        if len(tokens) <= OPENAI_EMBEDDING_TOKEN_LIMIT:
            return normalized
        trimmed = encoding.decode(tokens[:OPENAI_EMBEDDING_TOKEN_LIMIT]).strip()
        return trimmed or " "
    except Exception:
        words = normalized.split()
        if len(words) > OPENAI_EMBEDDING_TOKEN_LIMIT:
            normalized = " ".join(words[:OPENAI_EMBEDDING_TOKEN_LIMIT])
        if len(normalized) <= OPENAI_EMBEDDING_CHAR_FALLBACK_LIMIT:
            return normalized
        trimmed = normalized[:OPENAI_EMBEDDING_CHAR_FALLBACK_LIMIT].strip()
        return trimmed or " "


class CrossEncoderEndpointReranker:
    def __init__(
        self,
        model_name: str,
        *,
        device: str = "cpu",
        revision: str | None = None,
        local_files_only: bool = False,
    ) -> None:
        try:
            from sentence_transformers import CrossEncoder
        except Exception as exc:
            raise RuntimeError("cross_encoder reranker requires sentence-transformers and torch.") from exc
        self.model_name = model_name
        self.device = device
        self.revision = revision
        self.local_files_only = local_files_only
        self.model = CrossEncoder(
            model_name,
            device=device,
            revision=revision,
            local_files_only=local_files_only,
        )

    def score(self, query: str, endpoint_ids: list[str], endpoint_texts: list[str]) -> np.ndarray:
        pairs = [(query, text) for text in endpoint_texts]
        return np.asarray(self.model.predict(pairs, show_progress_bar=False), dtype=np.float32)


class OpenAIEndpointReranker:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        cache_dir: Path,
        audit_path: Path | None = None,
    ) -> None:
        if not api_key:
            raise RuntimeError("OpenAIEndpointReranker requires a non-empty API key.")
        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("OpenAIEndpointReranker requires the openai package.") from exc
        self.client = OpenAI(api_key=api_key, timeout=90.0)
        self.model = model
        self.cache_dir = cache_dir
        self.audit_path = audit_path

    def score(self, query: str, endpoint_ids: list[str], endpoint_texts: list[str]) -> np.ndarray:
        candidates = [
            {"endpoint_id": endpoint_id, "evidence": text[:1400]}
            for endpoint_id, text in zip(endpoint_ids, endpoint_texts)
        ]
        payload = {
            "task": "rerank_semantic_graph_candidates",
            "query": query,
            "candidates": candidates,
            "rules": [
                "Use only the provided endpoint_id values.",
                "Choose the endpoint whose evidence best matches the user intent.",
                "Prefer exact action and object semantics over generic word similarity.",
                "Return every candidate with a relevance score from 0 to 1.",
            ],
            "schema": {"items": [{"endpoint_id": "string", "score": "number"}]},
        }
        key = stable_hash({"model": self.model, "payload": payload, "version": 1})
        cache_path = self.cache_dir / "semantic_graph_endpoint_rerank" / f"{key}.json"
        started = time.perf_counter()
        cache_hit = cache_path.exists()
        if cache_hit:
            parsed = json.loads(cache_path.read_text(encoding="utf-8"))
            scores_by_id = _parse_endpoint_rerank_scores(parsed, endpoint_ids)
        else:
            last_error: ValueError | None = None
            for _attempt in range(2):
                response = self.client.responses.create(
                    model=self.model,
                    input=[
                        {
                            "role": "system",
                            "content": "Rerank provided OpenAPI endpoint candidates. Return valid JSON only.",
                        },
                        {"role": "user", "content": json.dumps(payload, sort_keys=True)},
                    ],
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "endpoint_rerank_scores",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "items": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "additionalProperties": False,
                                            "properties": {
                                                "endpoint_id": {"type": "string"},
                                                "score": {"type": "number"},
                                            },
                                            "required": ["endpoint_id", "score"],
                                        },
                                    }
                                },
                                "required": ["items"],
                            },
                        }
                    },
                    max_output_tokens=8000,
                )
                try:
                    parsed = json.loads(getattr(response, "output_text", "") or "{}")
                    scores_by_id = _parse_endpoint_rerank_scores(parsed, endpoint_ids)
                    break
                except ValueError as exc:
                    last_error = exc
            else:
                raise ValueError(f"Endpoint reranker returned malformed scores twice: {last_error}") from last_error
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(parsed, indent=2, sort_keys=True), encoding="utf-8")
        if self.audit_path is not None:
            write_llm_audit(
                self.audit_path,
                stage_component="semantic_graph_endpoint_rerank",
                model=self.model,
                mode="openai",
                input_hash=stable_hash(payload),
                output_hash=stable_hash(parsed),
                endpoint_ids_visible=True,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                cache_hit=cache_hit,
            )
        return np.asarray([scores_by_id.get(endpoint_id, 0.0) for endpoint_id in endpoint_ids], dtype=np.float32)


def _parse_endpoint_rerank_scores(parsed: dict[str, Any], endpoint_ids: list[str]) -> dict[str, float]:
    items = parsed.get("items", parsed.get("results", parsed.get("result", parsed.get("endpoint_rankings", []))))
    if not isinstance(items, list):
        raise ValueError("Endpoint reranker response must contain items as a list.")
    scores_by_id = {}
    allowed = set(endpoint_ids)
    for item in items:
        if not isinstance(item, dict):
            continue
        endpoint_id = str(item.get("endpoint_id") or "")
        if endpoint_id not in allowed:
            continue
        scores_by_id[endpoint_id] = float(item.get("score", 0.0))
    if not scores_by_id:
        raise ValueError("Endpoint reranker did not score any provided candidate endpoint IDs.")
    return scores_by_id


class OpenAIQueryExpander:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        vocabulary: list[str],
        cache_dir: Path,
        audit_path: Path | None = None,
    ) -> None:
        if not api_key:
            raise RuntimeError("OpenAIQueryExpander requires a non-empty API key.")
        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("OpenAIQueryExpander requires the openai package.") from exc
        self.client = OpenAI(api_key=api_key, timeout=90.0)
        self.model = model
        self.vocabulary = list(dict.fromkeys(item for item in vocabulary if item.strip()))[:600]
        self.cache_dir = cache_dir
        self.audit_path = audit_path

    def expand(self, query: str) -> list[str]:
        payload = {
            "task": "expand_query_for_semantic_graph_retrieval",
            "query": query,
            "vocabulary": self.vocabulary,
            "rules": [
                "Return up to 4 short search phrases.",
                "Use likely domain/API vocabulary from the vocabulary list when helpful.",
                "Do not choose or output endpoint IDs, HTTP paths, or HTTP methods.",
                "Keep the user's intent and do not add unrelated actions.",
            ],
            "schema": {"expanded_queries": ["string"]},
        }
        key = stable_hash({"model": self.model, "payload": payload, "version": 1})
        cache_path = self.cache_dir / "semantic_graph_query_expansion" / f"{key}.json"
        started = time.perf_counter()
        cache_hit = cache_path.exists()
        if cache_hit:
            parsed = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": "Expand user language into retrieval search phrases. Return valid JSON only.",
                    },
                    {"role": "user", "content": json.dumps(payload, sort_keys=True)},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "query_expansion",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "expanded_queries": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                }
                            },
                            "required": ["expanded_queries"],
                        },
                    }
                },
                max_output_tokens=1500,
            )
            parsed = json.loads(getattr(response, "output_text", "") or "{}")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(parsed, indent=2, sort_keys=True), encoding="utf-8")
        if self.audit_path is not None:
            write_llm_audit(
                self.audit_path,
                stage_component="semantic_graph_query_expansion",
                model=self.model,
                mode="openai",
                input_hash=stable_hash(payload),
                output_hash=stable_hash(parsed),
                endpoint_ids_visible=False,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                cache_hit=cache_hit,
            )
        expanded = parsed.get("expanded_queries", [])
        if not isinstance(expanded, list):
            raise ValueError("Query expander response must contain expanded_queries as a list.")
        cleaned = []
        for item in expanded:
            text = " ".join(str(item or "").split())
            if text and text != query and text not in cleaned:
                cleaned.append(text)
        return cleaned[:4]


@dataclass(frozen=True)
class CardHit:
    card_id: str
    node_id: str
    node_type: str
    endpoint_id: str | None
    score: float
    cosine_score: float
    discovery_weight: float
    title: str


@dataclass(frozen=True)
class EndpointScore:
    endpoint_id: str
    score: float


@dataclass(frozen=True)
class SemanticOnlyRouteResult:
    query: str
    ranked_endpoints: list[EndpointScore]
    score_components: dict[str, dict[str, float]]
    trace: dict[str, Any]


DEFAULT_EDGE_TYPE_WEIGHTS = {
    "projects": 1.00,
    "performs": 0.95,
    "resembles": 0.90,
    "exposes": 0.80,
    "accepts": 0.75,
    "returns": 0.65,
    "uses_schema": 0.88,
    "references": 0.62,
    "contains_object": 0.60,
    "contains_many": 0.60,
    "all_of": 0.58,
    "one_of": 0.54,
    "any_of": 0.54,
    "not": 0.35,
    "additional_properties": 0.48,
    "describes_resource": 0.76,
    "equivalent_shape": 0.52,
    "projection_of": 0.48,
    "requires": 0.50,
    "has_field": 0.45,
    "has_action": 0.70,
    "reads": 0.72,
    "mutates": 0.72,
    "creates": 0.72,
    "deletes": 0.72,
    "related_to": 0.35,
}

NODE_PROJECTION_WEIGHTS = {
    "api_operation": 1.00,
    "example_query": 0.95,
    "action": 0.92,
    "doc_chunk": 0.80,
    "api_shape": 0.62,
    "api_schema": 0.54,
    "api_inline_shape": 0.38,
    "api_field": 0.42,
}

DISCOVERY_NODE_TYPE_WEIGHTS = {
    "example_query": 1.15,
    "action": 1.08,
    "api_operation": 1.00,
    "doc_chunk": 0.95,
    "resource": 0.65,
    "side_effect": 0.45,
    "api_shape": 0.35,
    "api_schema": 0.52,
    "api_inline_shape": 0.32,
    "api_field": 0.20,
    "permission": 0.10,
}


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2:
        raise ValueError(f"Expected a 2D embedding matrix, got shape {matrix.shape}")
    output = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(output, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return output / norms


@dataclass(frozen=True)
class SemanticGraphIndex:
    graph: SemanticGraph
    cards: list[SemanticNodeCard]
    embeddings: np.ndarray
    embedding_provider: EmbeddingProvider
    edge_type_weights: dict[str, float]
    adjacency: dict[str, list[tuple[str, str, float]]]

    @classmethod
    def build(
        cls,
        graph: SemanticGraph,
        embedding_provider: EmbeddingProvider,
        *,
        edge_type_weights: dict[str, float] | None = None,
    ) -> "SemanticGraphIndex":
        if not graph.cards:
            raise ValueError("Semantic graph index requires at least one node card.")
        texts = [card.embedding_text() for card in graph.cards]
        embeddings = _l2_normalize(np.asarray(embedding_provider.embed_texts(texts), dtype=np.float32))
        if embeddings.shape[0] != len(graph.cards):
            raise ValueError(
                f"Embedding provider returned {embeddings.shape[0]} rows for {len(graph.cards)} semantic cards."
            )
        weights = {**DEFAULT_EDGE_TYPE_WEIGHTS, **(edge_type_weights or {})}
        adjacency: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
        for edge in graph.edges:
            weight = weights.get(edge.type, 0.25) * float(edge.confidence)
            adjacency[edge.source].append((edge.target, edge.type, weight))
            adjacency[edge.target].append((edge.source, f"reverse:{edge.type}", weight * 0.72))
        return cls(
            graph=graph,
            cards=list(graph.cards),
            embeddings=embeddings,
            embedding_provider=embedding_provider,
            edge_type_weights=weights,
            adjacency=dict(adjacency),
        )

    def search_cards(self, query: str, limit: int = 12) -> list[CardHit]:
        if limit <= 0:
            return []
        query_embedding = _l2_normalize(np.asarray(self._embed_query(query), dtype=np.float32))
        raw_scores = np.matmul(self.embeddings, query_embedding[0]).ravel()
        weights = np.asarray(
            [DISCOVERY_NODE_TYPE_WEIGHTS.get(card.node_type, 0.50) for card in self.cards],
            dtype=np.float32,
        )
        scores = raw_scores * weights
        order = np.argsort(scores)[::-1][:limit]
        return [
            CardHit(
                card_id=self.cards[int(index)].card_id,
                node_id=self.cards[int(index)].node_id,
                node_type=self.cards[int(index)].node_type,
                endpoint_id=self.cards[int(index)].endpoint_id,
                score=float(scores[int(index)]),
                cosine_score=float(raw_scores[int(index)]),
                discovery_weight=float(weights[int(index)]),
                title=self.cards[int(index)].title,
            )
            for index in order
            if float(scores[int(index)]) > 0.0
        ]

    def _embed_query(self, query: str) -> np.ndarray:
        embedding = self.embedding_provider.embed_texts([query])
        if embedding.shape[0] != 1:
            raise ValueError(f"Embedding provider returned {embedding.shape[0]} rows for one query.")
        return embedding

    def endpoint_text(self, endpoint_id: str) -> str:
        priority = {
            "action": 0,
            "api_operation": 1,
            "api_shape": 2,
            "example_query": 3,
            "doc_chunk": 4,
        }
        limits = {
            "action": 420,
            "api_operation": 420,
            "api_shape": 900,
            "example_query": 280,
            "doc_chunk": 700,
        }
        cards = [card for card in self.cards if card.endpoint_id == endpoint_id]
        cards.sort(key=lambda card: (priority.get(card.node_type, 9), card.card_id))
        snippets: list[str] = []
        seen: set[str] = set()
        for card in cards:
            text = " ".join(f"{card.node_type} {card.title} {card.body}".split())
            limit = limits.get(card.node_type, 420)
            snippet = text[:limit]
            if snippet and snippet not in seen:
                snippets.append(snippet)
                seen.add(snippet)
        return "\n".join(snippets)[:6000]

    def endpoint_identity(self, endpoint_id: str) -> tuple[str, str, str] | None:
        for card in self.cards:
            if card.endpoint_id != endpoint_id or card.node_type != "api_operation":
                continue
            operation_id = str(card.facets.get("operation_id") or "").casefold()
            method = str(card.facets.get("method") or "").upper()
            path = str(card.facets.get("path") or "")
            if operation_id and method and path:
                return (operation_id, method, path)
        return None

    def required_inputs(self, endpoint_id: str) -> list[dict[str, Any]]:
        for card in self.cards:
            if card.endpoint_id != endpoint_id or card.node_type != "api_operation":
                continue
            values = card.facets.get("required_inputs") or []
            if not isinstance(values, list):
                raise ValueError(f"Endpoint {endpoint_id} has invalid required_inputs evidence.")
            output: list[dict[str, Any]] = []
            for value in values:
                if not isinstance(value, dict) or not value.get("name") or not value.get("location"):
                    raise ValueError(f"Endpoint {endpoint_id} has malformed required input evidence.")
                output.append(dict(value))
            return output
        raise KeyError(f"No api_operation card exists for endpoint {endpoint_id}")

    def retrieval_vocabulary(self) -> list[str]:
        allowed_types = {"resource", "action", "side_effect"}
        values: list[str] = []
        for node in self.graph.nodes:
            if node.node_type in allowed_types:
                values.append(node.label)
                if node.node_type == "action":
                    values.extend(str(node.facets.get(key, "")) for key in ["operation_class", "method"])
        return sorted({value.strip() for value in values if value and value.strip()})


def _propagate_heat(
    index: SemanticGraphIndex,
    seeds: dict[str, float],
    max_hops: int,
    *,
    trace_mode: str,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    heat = dict(seeds)
    frontier = dict(seeds)
    trace: list[dict[str, Any]] = []
    for hop in range(max_hops):
        next_frontier: dict[str, float] = {}
        decay = 1.0 / float(hop + 2)
        for node_id, score in frontier.items():
            for target, edge_type, weight in index.adjacency.get(node_id, []):
                propagated = float(score) * float(weight) * decay
                previous_target_score = float(heat.get(target, 0.0))
                accepted = propagated > previous_target_score
                if trace_mode == "full" or accepted:
                    trace.append(
                        {
                            "hop": hop + 1,
                            "source": node_id,
                            "target": target,
                            "edge_type": edge_type,
                            "source_score": float(score),
                            "edge_weight": float(weight),
                            "decay": decay,
                            "calculated_score": propagated,
                            "previous_target_score": previous_target_score,
                            "accepted": accepted,
                            "score": propagated,
                        }
                    )
                if not accepted:
                    continue
                heat[target] = propagated
                next_frontier[target] = propagated
        frontier = next_frontier
        if not frontier:
            break
    return heat, trace


def _endpoint_scores_from_heat(
    index: SemanticGraphIndex,
    heat: dict[str, float],
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    nodes_by_id = index.graph.nodes_by_id
    scores: dict[str, float] = defaultdict(float)
    projection_rows: list[dict[str, Any]] = []
    for node_id, score in heat.items():
        node = nodes_by_id.get(node_id)
        if node is None or not node.endpoint_id:
            continue
        projection_weight = NODE_PROJECTION_WEIGHTS.get(node.node_type, 0.50)
        projected_score = float(score) * projection_weight
        scores[node.endpoint_id] = max(scores[node.endpoint_id], projected_score)
        projection_rows.append(
            {
                "node_id": node_id,
                "node_type": node.node_type,
                "endpoint_id": node.endpoint_id,
                "heat": float(score),
                "projection_weight": float(projection_weight),
                "projected_score": projected_score,
            }
        )
    final_scores = dict(scores)
    for row in projection_rows:
        row["is_winner"] = bool(
            np.isclose(row["projected_score"], final_scores[row["endpoint_id"]])
        )
    projection_rows.sort(
        key=lambda row: (
            row["endpoint_id"],
            row["projected_score"],
            row["node_id"],
        ),
        reverse=True,
    )
    return final_scores, projection_rows


def _zero_safe_minmax(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    lo = min(values.values())
    hi = max(values.values())
    if np.isclose(lo, hi):
        fill = 0.0 if hi <= 0.0 else 1.0
        return {key: fill for key in values}
    return {key: (value - lo) / (hi - lo) for key, value in values.items()}


def _rerank_endpoint_scores(
    query: str,
    index: SemanticGraphIndex,
    endpoint_scores: dict[str, float],
    reranker: EndpointReranker,
    *,
    rerank_limit: int,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    candidates = [
        endpoint_id
        for endpoint_id, _score in sorted(endpoint_scores.items(), key=lambda item: (item[1], item[0]), reverse=True)[:rerank_limit]
    ]
    if not candidates:
        return endpoint_scores, []
    raw_scores = reranker.score(query, candidates, [index.endpoint_text(endpoint_id) for endpoint_id in candidates])
    rerank_scores = {endpoint_id: float(score) for endpoint_id, score in zip(candidates, raw_scores)}
    semantic_norm = _zero_safe_minmax({endpoint_id: endpoint_scores.get(endpoint_id, 0.0) for endpoint_id in candidates})
    rerank_norm = _zero_safe_minmax(rerank_scores)
    combined = dict(endpoint_scores)
    for endpoint_id in candidates:
        combined[endpoint_id] = 0.35 * semantic_norm.get(endpoint_id, 0.0) + 0.65 * rerank_norm.get(endpoint_id, 0.0)
    trace = [
        {
            "endpoint_id": endpoint_id,
            "semantic_score": float(endpoint_scores.get(endpoint_id, 0.0)),
            "rerank_score": float(rerank_scores.get(endpoint_id, 0.0)),
            "combined_score": float(combined.get(endpoint_id, 0.0)),
        }
        for endpoint_id in candidates
    ]
    return combined, trace


def route_semantic_only(
    query: str,
    index: SemanticGraphIndex,
    *,
    top_k: int = 5,
    card_limit: int = 12,
    max_hops: int = 3,
    reranker: EndpointReranker | None = None,
    rerank_limit: int = 25,
    query_expander: QueryExpander | None = None,
    trace_mode: str = "bounded",
) -> SemanticOnlyRouteResult:
    if trace_mode not in {"bounded", "full"}:
        raise ValueError("trace_mode must be 'bounded' or 'full'.")
    expanded_queries = query_expander.expand(query) if query_expander is not None else []
    weighted_queries = [(query, 1.0), *[(expanded, 0.88) for expanded in expanded_queries]]
    hits_by_query = [
        {
            "query": search_query,
            "weight": weight,
            "hits": index.search_cards(search_query, limit=card_limit),
        }
        for search_query, weight in weighted_queries
    ]
    seeds: dict[str, float] = {}
    for group in hits_by_query:
        weight = float(group["weight"])
        for hit in group["hits"]:
            seeds[hit.node_id] = max(seeds.get(hit.node_id, 0.0), hit.score * weight)
    hits = hits_by_query[0]["hits"] if hits_by_query else []
    heat, propagation_trace = _propagate_heat(
        index,
        seeds,
        max_hops=max_hops,
        trace_mode=trace_mode,
    )
    endpoint_scores, endpoint_projection = _endpoint_scores_from_heat(index, heat)
    pre_rerank_endpoint_scores = dict(endpoint_scores)
    rerank_trace: list[dict[str, Any]] = []
    if reranker is not None:
        endpoint_scores, rerank_trace = _rerank_endpoint_scores(
            query,
            index,
            endpoint_scores,
            reranker,
            rerank_limit=rerank_limit,
        )
    ranked = [
        EndpointScore(endpoint_id=endpoint_id, score=float(score))
        for endpoint_id, score in sorted(endpoint_scores.items(), key=lambda item: (item[1], item[0]), reverse=True)[:top_k]
    ]
    nodes_by_id = index.graph.nodes_by_id
    return SemanticOnlyRouteResult(
        query=query,
        ranked_endpoints=ranked,
        score_components={"semantic_graph": endpoint_scores},
        trace={
            "trace_mode": trace_mode,
            "configuration": {
                "card_limit": card_limit,
                "max_hops": max_hops,
                "query_expansion_enabled": query_expander is not None,
                "reranking_enabled": reranker is not None,
            },
            "top_seed_cards": [hit.__dict__ for hit in hits],
            "expanded_queries": expanded_queries,
            "seed_card_groups": [
                {
                    "query": group["query"],
                    "weight": group["weight"],
                    "hits": [
                        hit.__dict__
                        for hit in (
                            group["hits"]
                            if trace_mode == "full"
                            else group["hits"][:8]
                        )
                    ],
                }
                for group in hits_by_query
            ],
            "propagation": (
                propagation_trace
                if trace_mode == "full"
                else propagation_trace[:50]
            ),
            "endpoint_projection": endpoint_projection if trace_mode == "full" else [],
            "pre_rerank_endpoint_scores": [
                {"endpoint_id": endpoint_id, "score": float(score)}
                for endpoint_id, score in sorted(
                    pre_rerank_endpoint_scores.items(),
                    key=lambda item: (item[1], item[0]),
                    reverse=True,
                )[:top_k]
            ],
            "heated_nodes": [
                {
                    "node_id": node_id,
                    "node_type": nodes_by_id.get(node_id).node_type
                    if nodes_by_id.get(node_id) is not None
                    else None,
                    "endpoint_id": nodes_by_id.get(node_id).endpoint_id
                    if nodes_by_id.get(node_id) is not None
                    else None,
                    "score": float(score),
                }
                for node_id, score in (
                    sorted(heat.items(), key=lambda item: (item[1], item[0]), reverse=True)
                    if trace_mode == "full"
                    else sorted(heat.items(), key=lambda item: (item[1], item[0]), reverse=True)[:25]
                )
            ],
            "rerank": rerank_trace,
        },
    )


def build_runtime_semantic_graph_index(
    graph: SemanticGraph,
    embedding_provider: EmbeddingProvider,
    *,
    edge_type_weights: dict[str, float] | None = None,
) -> SemanticGraphIndex:
    return SemanticGraphIndex.build(graph, embedding_provider, edge_type_weights=edge_type_weights)
