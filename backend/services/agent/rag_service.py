"""Workspace-scoped RAG service.

Adapted from foundation-agent — every read/write filters on workspace_id so
documents uploaded in workspace A are invisible to workspace B.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd
from openai import AsyncOpenAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.models import AgentDocument, AgentDocumentChunk

CHUNK_SIZE = 500  # tokens (approximate)
CHUNK_OVERLAP = 50
CHARS_PER_TOKEN = 4


class RAGService:
    def __init__(self):
        self._client: AsyncOpenAI | None = None
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    # ── Ingestion ────────────────────────────────────────────────

    async def ingest_document(
        self,
        *,
        workspace_id: uuid.UUID,
        uploaded_by: uuid.UUID | None,
        file_content: bytes,
        original_name: str,
        content_type: str,
        db: AsyncSession,
    ) -> AgentDocument:
        file_id = str(uuid.uuid4())
        ext = Path(original_name).suffix
        filename = f"{file_id}{ext}"
        filepath = self.upload_dir / filename
        filepath.write_bytes(file_content)

        text_content = self._parse_document(filepath, content_type)
        chunks = self._chunk_text(text_content)
        embeddings = await self._embed_texts(chunks) if chunks else []

        doc = AgentDocument(
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            filename=filename,
            original_name=original_name,
            content_type=content_type,
            size_bytes=len(file_content),
            chunk_count=len(chunks),
        )
        db.add(doc)
        await db.flush()

        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            db.add(
                AgentDocumentChunk(
                    document_id=doc.id,
                    workspace_id=workspace_id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=embedding,
                    metadata_={"source": original_name, "chunk_index": i},
                )
            )

        await db.commit()
        await db.refresh(doc)
        return doc

    def _parse_document(self, filepath: Path, content_type: str) -> str:
        suffix = filepath.suffix.lower()

        if suffix == ".pdf" or "pdf" in content_type:
            doc = fitz.open(str(filepath))
            try:
                pages = [page.get_text() for page in doc]
            finally:
                doc.close()
            return "\n\n".join(pages)

        if suffix == ".csv" or "csv" in content_type:
            df = pd.read_csv(filepath)
            summary = (
                f"CSV with {len(df)} rows and {len(df.columns)} columns.\n"
                f"Columns: {', '.join(df.columns.tolist())}\n\n"
                f"{df.to_string(max_rows=100, max_cols=20)}"
            )
            return summary

        return filepath.read_text(encoding="utf-8", errors="replace")

    def _chunk_text(self, body: str) -> list[str]:
        if not body.strip():
            return []
        chunk_chars = CHUNK_SIZE * CHARS_PER_TOKEN
        overlap_chars = CHUNK_OVERLAP * CHARS_PER_TOKEN

        paragraphs = body.split("\n\n")
        chunks: list[str] = []
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) + 2 <= chunk_chars:
                current = f"{current}\n\n{para}" if current else para
            else:
                if current:
                    chunks.append(current.strip())
                if len(para) > chunk_chars:
                    for i in range(0, len(para), chunk_chars - overlap_chars):
                        chunks.append(para[i : i + chunk_chars].strip())
                    current = ""
                else:
                    current = para
        if current.strip():
            chunks.append(current.strip())
        return chunks if chunks else [body[:chunk_chars].strip()]

    # ── Embedding ────────────────────────────────────────────────

    async def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = await self.client.embeddings.create(
            input=texts, model=settings.embedding_model
        )
        return [item.embedding for item in resp.data]

    async def _embed_query(self, query: str) -> list[float]:
        result = await self._embed_texts([query])
        return result[0]

    # ── Search ───────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        *,
        workspace_id: uuid.UUID,
        db: AsyncSession | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        from backend.core.database import async_session as session_factory

        embedding = await self._embed_query(query)
        if db is None:
            async with session_factory() as session:
                return await self._do_search(session, workspace_id, embedding, top_k)
        return await self._do_search(db, workspace_id, embedding, top_k)

    async def _do_search(
        self,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        embedding: list[float],
        top_k: int,
    ) -> list[dict]:
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        query = text(
            """
            SELECT dc.id, dc.content, dc.chunk_index, dc.metadata,
                   d.original_name AS document_name, d.id AS document_id,
                   dc.embedding <=> CAST(:embedding AS vector) AS distance
            FROM agent_document_chunks dc
            JOIN agent_documents d ON d.id = dc.document_id
            WHERE dc.embedding IS NOT NULL
              AND dc.workspace_id = :workspace_id
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
            """
        )
        result = await db.execute(
            query,
            {
                "embedding": embedding_str,
                "top_k": top_k,
                "workspace_id": str(workspace_id),
            },
        )
        rows = result.fetchall()
        return [
            {
                "chunk_id": str(row.id),
                "content": row.content,
                "chunk_index": row.chunk_index,
                "document_name": row.document_name,
                "document_id": str(row.document_id),
                "score": round(1 - row.distance, 3),
            }
            for row in rows
        ]

    # ── Delete ───────────────────────────────────────────────────

    async def delete_document(
        self,
        document_id: uuid.UUID,
        workspace_id: uuid.UUID,
        db: AsyncSession,
    ) -> bool:
        result = await db.execute(
            select(AgentDocument).where(
                AgentDocument.id == document_id,
                AgentDocument.workspace_id == workspace_id,
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            return False
        filepath = self.upload_dir / doc.filename
        if filepath.exists():
            filepath.unlink()
        await db.delete(doc)
        await db.commit()
        return True


rag_service = RAGService()
