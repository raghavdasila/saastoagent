from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

from backend.core.config import settings


@dataclass(frozen=True)
class PlatformKBChunk:
    id: str
    title: str
    source_path: str
    content: str


@dataclass(frozen=True)
class PlatformKBResult:
    chunk: PlatformKBChunk
    score: float


PLATFORM_KB_CHUNKS: tuple[PlatformKBChunk, ...] = (
    PlatformKBChunk(
        id="vision-v01",
        title="SaaStoAgent v0.1 Vision",
        source_path="saastoagent-v0.1/critical_prompt.md",
        content=(
            "SaaStoAgent v0.1 is a REST-only SaaSAgent agent product. One SaaSAgent owns one SaaS operator. "
            "The SaaSAgent contains connected REST sources, inferred entities, generated actions/tools, chat runtime, "
            "QA, failure capture, tuning, and governed learnings."
        ),
    ),
    PlatformKBChunk(
        id="success-path",
        title="End-to-end success path",
        source_path="saastoagent-v0.1/critical_prompt.md",
        content=(
            "A user should be able to create a SaaSAgent, connect a REST API, inspect inferred entities and actions, "
            "ask which actions are relevant, execute real REST workflows, run QA, and persist validated learnings."
        ),
    ),
    PlatformKBChunk(
        id="source-runtime",
        title="Source SaaStoAgent runtime",
        source_path="saastoagent/docs/saastoagent-runtime-source-of-truth-short.md",
        content=(
            "The source SaaStoAgent runtime uses a conversational outer model, a run_task meta-tool, decomposition, "
            "dynamic tool binding, sequential subagent execution, approval gates, event streaming, and persistence."
        ),
    ),
    PlatformKBChunk(
        id="knowledgebase",
        title="Knowledgebase rules",
        source_path="saastoagent/knowledgebase/README.md",
        content=(
            "The source knowledgebase stores verified research findings, framework learnings, and proven solutions. "
            "Important areas include action nodes, OpenAPI parsing, embeddings, pgvector search, LangGraph streaming, "
            "state management, tool patterns, auth, Docker, and runtime bugs."
        ),
    ),
    PlatformKBChunk(
        id="onboarding",
        title="SaaSAgent and API setup",
        source_path="saastoagent-v0.1/context.md",
        content=(
            "The current v0.1 entry path is backend-owned over SSE. It covers sign in or create account, SaaSAgent "
            "select/create, REST API setup, connection confirmation, activation progress, and operator chat handoff."
        ),
    ),
)


class PlatformKB:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._embeddings: list[list[float]] | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def search(self, query: str, *, top_k: int = 3) -> list[PlatformKBResult]:
        cleaned = query.strip()
        if not cleaned:
            return [
                PlatformKBResult(chunk=chunk, score=1.0)
                for chunk in PLATFORM_KB_CHUNKS[:top_k]
            ]
        if settings.openai_api_key:
            try:
                return await self._embedding_search(cleaned, top_k=top_k)
            except Exception:
                pass
        return self._keyword_search(cleaned, top_k=top_k)

    async def _embedding_search(self, query: str, *, top_k: int) -> list[PlatformKBResult]:
        if self._embeddings is None:
            corpus_response = await self.client.embeddings.create(
                model=settings.embedding_model,
                input=[chunk.content for chunk in PLATFORM_KB_CHUNKS],
            )
            self._embeddings = [item.embedding for item in corpus_response.data]

        query_response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=[query],
        )
        query_embedding = query_response.data[0].embedding
        scored = [
            PlatformKBResult(
                chunk=chunk,
                score=_cosine_similarity(query_embedding, embedding),
            )
            for chunk, embedding in zip(PLATFORM_KB_CHUNKS, self._embeddings)
        ]
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]

    def _keyword_search(self, query: str, *, top_k: int) -> list[PlatformKBResult]:
        query_terms = _terms(query)
        scored: list[PlatformKBResult] = []
        for chunk in PLATFORM_KB_CHUNKS:
            chunk_terms = _terms(f"{chunk.title} {chunk.content}")
            overlap = query_terms & chunk_terms
            score = len(overlap) / max(len(query_terms), 1)
            if score > 0:
                scored.append(PlatformKBResult(chunk=chunk, score=score))
        if not scored:
            scored = [
                PlatformKBResult(chunk=chunk, score=0.1)
                for chunk in PLATFORM_KB_CHUNKS[:top_k]
            ]
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


def _terms(value: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z0-9]+", value.lower())
        if len(term) > 2
    }


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def citation_payload(results: list[PlatformKBResult]) -> list[dict[str, Any]]:
    return [
        {
            "title": result.chunk.title,
            "source_path": result.chunk.source_path,
            "score": round(result.score, 3),
            "excerpt": result.chunk.content[:260],
        }
        for result in results
    ]


platform_kb = PlatformKB()
