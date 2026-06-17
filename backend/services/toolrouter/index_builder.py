from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import (
    ActionNode,
    ActionNodeStatus,
    GeneratedTool,
    ToolRouterDocument,
    ToolRouterIndex,
    ToolRouterIndexStatus,
    ToolStatus,
)
from backend.services.toolrouter.documents import RouterDocument, build_router_documents, catalog_fingerprint

ROUTER_VERSION = "fusion_rag_v1"


def build_router_index_payload(rows: Iterable[tuple[GeneratedTool, ActionNode]]) -> dict[str, Any]:
    row_list = list(rows)
    documents = build_router_documents(row_list)
    endpoint_keys = {document.endpoint_key for document in documents}
    kind_counts = Counter(document.doc_kind for document in documents)
    return {
        "router_version": ROUTER_VERSION,
        "catalog_fingerprint": catalog_fingerprint(row_list),
        "document_count": len(documents),
        "endpoint_count": len(endpoint_keys),
        "documents": documents,
        "stats": {
            "doc_kinds": dict(sorted(kind_counts.items())),
            "tool_count": len(row_list),
        },
    }


def router_index_stats(index: ToolRouterIndex | None) -> dict[str, Any] | None:
    if index is None:
        return None
    status = index.status.value if hasattr(index.status, "value") else str(index.status)
    return {
        "status": status,
        "router_version": index.router_version,
        "document_count": int(index.document_count or 0),
        "endpoint_count": int(index.endpoint_count or 0),
        "catalog_fingerprint": str(index.catalog_fingerprint or "")[:12],
        "built_at": index.built_at.isoformat() if index.built_at else None,
    }


async def build_toolrouter_index_for_agent(*, saas_agent_id, session: AsyncSession) -> dict[str, Any]:
    rows = await _load_catalog_rows(session=session, saas_agent_id=saas_agent_id)
    payload = build_router_index_payload(rows)
    index = await _existing_index_for_fingerprint(session=session, saas_agent_id=saas_agent_id, catalog_fingerprint=payload["catalog_fingerprint"])
    if index is None:
        index = ToolRouterIndex(
            saas_agent_id=saas_agent_id,
            router_version=ROUTER_VERSION,
            catalog_fingerprint=payload["catalog_fingerprint"],
            status=ToolRouterIndexStatus.building,
            document_count=0,
            endpoint_count=0,
            stats=payload["stats"],
        )
        session.add(index)
    else:
        index.status = ToolRouterIndexStatus.building
        index.document_count = 0
        index.endpoint_count = 0
        index.error = None
        index.stats = payload["stats"]
    await session.flush()
    await _mark_prior_indexes_stale(session=session, saas_agent_id=saas_agent_id, keep_index_id=index.id)
    await _replace_index_documents(index=index, saas_agent_id=saas_agent_id, documents=payload["documents"], session=session)
    index.status = ToolRouterIndexStatus.ready
    index.document_count = payload["document_count"]
    index.endpoint_count = payload["endpoint_count"]
    index.stats = payload["stats"]
    index.built_at = datetime.now(timezone.utc)
    await session.commit()
    return {
        "router_index_status": ToolRouterIndexStatus.ready.value,
        "router_version": ROUTER_VERSION,
        "router_documents_count": payload["document_count"],
        "router_endpoint_count": payload["endpoint_count"],
        "catalog_fingerprint": payload["catalog_fingerprint"][:12],
    }


async def latest_ready_index(*, session: AsyncSession, saas_agent_id, router_version: str = ROUTER_VERSION) -> ToolRouterIndex | None:
    result = await session.execute(
        select(ToolRouterIndex)
        .where(
            ToolRouterIndex.saas_agent_id == saas_agent_id,
            ToolRouterIndex.router_version == router_version,
            ToolRouterIndex.status == ToolRouterIndexStatus.ready,
        )
        .order_by(ToolRouterIndex.built_at.desc(), ToolRouterIndex.created_at.desc())
        .limit(1)
    )
    index = result.scalar_one_or_none()
    if index is None:
        return None
    rows = await _load_catalog_rows(session=session, saas_agent_id=saas_agent_id)
    if index.catalog_fingerprint != catalog_fingerprint(rows):
        return None
    return index


async def _load_catalog_rows(*, session: AsyncSession, saas_agent_id) -> list[tuple[GeneratedTool, ActionNode]]:
    result = await session.execute(
        select(GeneratedTool, ActionNode)
        .join(ActionNode, GeneratedTool.action_node_id == ActionNode.id)
        .where(
            GeneratedTool.saas_agent_id == saas_agent_id,
            GeneratedTool.status == ToolStatus.active,
            ActionNode.status != ActionNodeStatus.deprecated,
        )
        .order_by(ActionNode.source_index, ActionNode.method, ActionNode.path, GeneratedTool.name)
    )
    return list(result.all())


async def _existing_index_for_fingerprint(*, session: AsyncSession, saas_agent_id, catalog_fingerprint: str) -> ToolRouterIndex | None:
    result = await session.execute(
        select(ToolRouterIndex)
        .where(
            ToolRouterIndex.saas_agent_id == saas_agent_id,
            ToolRouterIndex.router_version == ROUTER_VERSION,
            ToolRouterIndex.catalog_fingerprint == catalog_fingerprint,
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _mark_prior_indexes_stale(*, session: AsyncSession, saas_agent_id, keep_index_id=None) -> None:
    result = await session.execute(
        select(ToolRouterIndex).where(
            ToolRouterIndex.saas_agent_id == saas_agent_id,
            ToolRouterIndex.router_version == ROUTER_VERSION,
            ToolRouterIndex.status.in_([ToolRouterIndexStatus.ready, ToolRouterIndexStatus.building]),
        )
    )
    for index in result.scalars().all():
        if keep_index_id is not None and index.id == keep_index_id:
            continue
        index.status = ToolRouterIndexStatus.stale


async def _replace_index_documents(*, index: ToolRouterIndex, saas_agent_id, documents: list[RouterDocument], session: AsyncSession) -> None:
    await session.execute(delete(ToolRouterDocument).where(ToolRouterDocument.index_id == index.id))
    for document in documents:
        session.add(_document_row(index=index, saas_agent_id=saas_agent_id, document=document))


def _document_row(*, index: ToolRouterIndex, saas_agent_id, document: RouterDocument) -> ToolRouterDocument:
    return ToolRouterDocument(
        index_id=index.id,
        saas_agent_id=saas_agent_id,
        action_node_id=document.action_node_id,
        generated_tool_id=document.generated_tool_id,
        endpoint_key=document.endpoint_key,
        doc_kind=document.doc_kind,
        search_text=document.search_text,
        tokens=document.tokens,
        graph_refs=document.graph_refs,
    )
