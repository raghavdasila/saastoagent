"""RAG search tool — bound to the active workspace at graph build time."""

from __future__ import annotations

import uuid

from langchain_core.tools import tool

_rag_service = None
_workspace_id: uuid.UUID | None = None


def set_rag_context(service, *, workspace_id: uuid.UUID) -> None:
    global _rag_service, _workspace_id
    _rag_service = service
    _workspace_id = workspace_id


@tool
async def rag_search(query: str, top_k: int = 5) -> str:
    """Search this workspace's uploaded documents for relevant passages.

    Use this when the user asks about workspace knowledge, attached files,
    or any content they've uploaded into this workspace.

    Args:
        query: The search query.
        top_k: Maximum chunks to return (default 5).
    """
    if _rag_service is None or _workspace_id is None:
        return "RAG service is not initialised for this workspace."

    results = await _rag_service.search(query, workspace_id=_workspace_id, top_k=top_k)
    if not results:
        return "No relevant documents found for your query."

    parts = [f"Found {len(results)} relevant passage(s):\n"]
    for i, r in enumerate(results, 1):
        parts.append(
            f"[{i}] From: {r['document_name']} (relevance: {r['score']:.2f})\n"
            f"{r['content']}\n"
        )
    return "\n".join(parts)
