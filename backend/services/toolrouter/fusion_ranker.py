from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import log
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.models import ActionNode, ActionNodeStatus, Connection, GeneratedTool, ToolRouterDocument, ToolStatus
from backend.services.toolrouter.documents import endpoint_key_for, tokenize
from backend.services.toolrouter.index_builder import latest_ready_index

PRODUCT_SCORE_WEIGHTS = {
    "rag_all_max": 0.25,
    "bm25_all_max": 0.25,
    "grag_expand": 0.15,
    "grag_rerank": 0.10,
    "grag_constrained": 0.08,
    "graph_sparse": 0.05,
    "schema_param": 0.07,
    "trigram": 0.05,
}
MIN_ENDPOINT_SCORE = 0.08


@dataclass(frozen=True)
class EndpointScore:
    endpoint_key: str
    score: float
    components: dict[str, float]
    reason: str


@dataclass(frozen=True)
class RankedToolRow:
    tool: GeneratedTool
    action: ActionNode
    connection: Connection
    score: int
    reason: str


def rank_endpoint_scores(query: str, documents: Iterable[Any], *, min_score: float = MIN_ENDPOINT_SCORE) -> list[EndpointScore]:
    scores = fused_scores_from_documents(query, documents)
    ranked = [
        EndpointScore(endpoint_key=endpoint_key, score=payload["score"], components=payload["components"], reason=payload["reason"])
        for endpoint_key, payload in scores.items()
        if float(payload["score"]) >= min_score
    ]
    return sorted(ranked, key=lambda item: (-item.score, item.endpoint_key))


def fused_scores_from_documents(query: str, documents: Iterable[Any]) -> dict[str, dict[str, Any]]:
    docs = list(documents)
    query_tokens = tokenize(query)
    endpoint_docs: dict[str, list[Any]] = defaultdict(list)
    for doc in docs:
        endpoint_docs[str(doc.endpoint_key)].append(doc)
    doc_freq = _document_frequency(docs)
    all_scores: dict[str, dict[str, Any]] = {}
    for endpoint_key, endpoint_group in endpoint_docs.items():
        components = {
            "rag_all_max": max((_tfidf_like(query_tokens, doc, doc_freq, len(docs)) for doc in endpoint_group), default=0.0),
            "bm25_all_max": max((_bm25(query_tokens, doc, doc_freq, docs) for doc in endpoint_group), default=0.0),
            "schema_param": max(
                (
                    _tfidf_like(query_tokens, doc, doc_freq, len(docs))
                    for doc in endpoint_group
                    if str(getattr(doc, "doc_kind", "")) in {"parameter", "request", "response", "auth"}
                ),
                default=0.0,
            ),
            "grag_expand": _graph_expand(query_tokens, endpoint_group),
            "grag_rerank": _graph_rerank(query_tokens, endpoint_group),
            "grag_constrained": _graph_constrained(query_tokens, endpoint_group),
            "graph_sparse": _graph_sparse(query_tokens, endpoint_group),
            "trigram": max((_trigram_similarity(query, str(getattr(doc, "search_text", ""))) for doc in endpoint_group), default=0.0),
        }
        score = sum(PRODUCT_SCORE_WEIGHTS[name] * components.get(name, 0.0) for name in PRODUCT_SCORE_WEIGHTS)
        all_scores[endpoint_key] = {
            "score": score,
            "components": {key: round(float(value), 4) for key, value in components.items()},
            "reason": _reason(components),
        }
    return all_scores


async def rank_generated_tools(
    *,
    message: str,
    saas_agent_id,
    db: AsyncSession,
    limit: int = 5,
) -> list[RankedToolRow]:
    index = await latest_ready_index(session=db, saas_agent_id=saas_agent_id)
    if index is None:
        return []
    doc_rows = (
        await db.execute(
            select(ToolRouterDocument).where(ToolRouterDocument.index_id == index.id)
        )
    ).scalars().all()
    ranked_endpoints = rank_endpoint_scores(message, doc_rows)
    if not ranked_endpoints:
        return []
    indexed_tool_ids = {doc.generated_tool_id for doc in doc_rows if getattr(doc, "generated_tool_id", None)}
    indexed_action_ids = {doc.action_node_id for doc in doc_rows if getattr(doc, "action_node_id", None)}
    if not indexed_tool_ids or not indexed_action_ids:
        return []
    rows = (
        await db.execute(
            select(GeneratedTool, ActionNode, Connection)
            .join(ActionNode, GeneratedTool.action_node_id == ActionNode.id)
            .join(Connection, GeneratedTool.connection_id == Connection.id)
            .options(selectinload(Connection.credentials))
            .where(
                GeneratedTool.saas_agent_id == saas_agent_id,
                GeneratedTool.id.in_(indexed_tool_ids),
                ActionNode.id.in_(indexed_action_ids),
                GeneratedTool.status == ToolStatus.active,
                ActionNode.status != ActionNodeStatus.deprecated,
            )
        )
    ).all()
    by_key = {endpoint_key_for(action): (tool, action, connection) for tool, action, connection in rows}
    ranked: list[RankedToolRow] = []
    for endpoint in ranked_endpoints:
        match = by_key.get(endpoint.endpoint_key)
        if match is None:
            continue
        tool, action, connection = match
        ranked.append(
            RankedToolRow(
                tool=tool,
                action=action,
                connection=connection,
                score=max(1, int(round(endpoint.score * 100))),
                reason=endpoint.reason,
            )
        )
    return ranked[:limit]


def _document_frequency(docs: list[Any]) -> Counter[str]:
    freq: Counter[str] = Counter()
    for doc in docs:
        freq.update(set(str(token) for token in (getattr(doc, "tokens", None) or [])))
    return freq


def _tfidf_like(query_tokens: list[str], doc: Any, doc_freq: Counter[str], total_docs: int) -> float:
    tokens = list(getattr(doc, "tokens", None) or [])
    if not query_tokens or not tokens:
        return 0.0
    counts = Counter(tokens)
    score = 0.0
    for token in query_tokens:
        if token not in counts:
            continue
        idf = log((1 + total_docs) / (1 + doc_freq[token])) + 1.0
        score += counts[token] * idf
    return min(1.0, score / max(3.0, len(query_tokens)))


def _bm25(query_tokens: list[str], doc: Any, doc_freq: Counter[str], docs: list[Any], *, k1: float = 1.2, b: float = 0.75) -> float:
    tokens = list(getattr(doc, "tokens", None) or [])
    if not query_tokens or not tokens:
        return 0.0
    counts = Counter(tokens)
    avg_len = sum(len(getattr(item, "tokens", None) or []) for item in docs) / max(1, len(docs))
    score = 0.0
    for token in query_tokens:
        tf = counts[token]
        if not tf:
            continue
        df = max(1, doc_freq[token])
        idf = log(1 + ((len(docs) - df + 0.5) / (df + 0.5)))
        denom = tf + k1 * (1 - b + b * (len(tokens) / max(avg_len, 1.0)))
        score += idf * ((tf * (k1 + 1)) / denom)
    return min(1.0, score / max(1.5, len(query_tokens)))


def _graph_expand(query_tokens: list[str], docs: list[Any]) -> float:
    refs = _merged_refs(docs)
    return _fraction_overlap(query_tokens, set(refs.get("resources", [])) | set(refs.get("tags", [])))


def _graph_rerank(query_tokens: list[str], docs: list[Any]) -> float:
    refs = _merged_refs(docs)
    return _fraction_overlap(query_tokens, set(refs.get("resources", [])) | set(refs.get("params", [])) | set(refs.get("methods", [])))


def _graph_constrained(query_tokens: list[str], docs: list[Any]) -> float:
    refs = _merged_refs(docs)
    return _fraction_overlap(query_tokens, set(refs.get("params", [])))


def _graph_sparse(query_tokens: list[str], docs: list[Any]) -> float:
    refs = _merged_refs(docs)
    values = set().union(*(set(items) for items in refs.values())) if refs else set()
    return _fraction_overlap(query_tokens, values)


def _trigram_similarity(query: str, text_value: str) -> float:
    query_trigrams = _trigrams(query)
    text_trigrams = _trigrams(text_value)
    if not query_trigrams or not text_trigrams:
        return 0.0
    return len(query_trigrams & text_trigrams) / len(query_trigrams | text_trigrams)


def _trigrams(value: str) -> set[str]:
    normalized = " ".join(tokenize(value))
    if not normalized:
        return set()
    padded = f"  {normalized}  "
    return {padded[index : index + 3] for index in range(max(0, len(padded) - 2))}


def _merged_refs(docs: list[Any]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = defaultdict(list)
    for doc in docs:
        refs = getattr(doc, "graph_refs", None) or {}
        if not isinstance(refs, dict):
            continue
        for key, values in refs.items():
            if isinstance(values, list):
                merged[key].extend(str(value).lower() for value in values)
    return {key: list(dict.fromkeys(values)) for key, values in merged.items()}


def _fraction_overlap(query_tokens: list[str], values: set[str]) -> float:
    if not query_tokens or not values:
        return 0.0
    expanded_values: set[str] = set()
    for value in values:
        expanded_values.update(tokenize(value))
    if not expanded_values:
        return 0.0
    return min(1.0, len(set(query_tokens) & expanded_values) / max(1, len(set(query_tokens))))


def _reason(components: dict[str, float]) -> str:
    top = [(name, value) for name, value in sorted(components.items(), key=lambda item: item[1], reverse=True) if value > 0][:3]
    if not top:
        return "fusion:no_signal"
    return "fusion:" + ",".join(f"{name}={value:.2f}" for name, value in top)
