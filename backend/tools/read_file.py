"""Read uploaded document tool — SaaSAgent-scoped."""

from __future__ import annotations

import uuid

from langchain_core.tools import tool
from sqlalchemy import select

from backend.core.database import async_session
from backend.core.models import AgentDocument, AgentDocumentChunk
from backend.tools.rag_search import _saas_agent_id  # set at graph build time


@tool
async def read_file(document_id: str) -> str:
    """Read the contents of an uploaded document by its ID.

    Args:
        document_id: The UUID of the document to read.
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        return f"Invalid document ID: {document_id}"
    if _saas_agent_id is None:
        return "SaaSAgent context not initialised."

    async with async_session() as db:
        result = await db.execute(
            select(AgentDocument).where(
                AgentDocument.id == doc_uuid,
                AgentDocument.saas_agent_id == _saas_agent_id,
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            return f"Document not found in this SaaS Agent: {document_id}"

        chunks_q = await db.execute(
            select(AgentDocumentChunk)
            .where(AgentDocumentChunk.document_id == doc_uuid)
            .order_by(AgentDocumentChunk.chunk_index)
        )
        chunks = chunks_q.scalars().all()
        if not chunks:
            return f"Document '{doc.original_name}' has no content chunks."

        content = "\n\n".join(c.content for c in chunks)
        return (
            f"Document: {doc.original_name}\n"
            f"Type: {doc.content_type}\n"
            f"Size: {doc.size_bytes:,} bytes\n"
            f"Chunks: {len(chunks)}\n\n"
            f"--- Content ---\n{content[:20_000]}"
        )
