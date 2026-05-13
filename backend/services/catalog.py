from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import ActionNode, ActionNodeStatus, Connection, GeneratedTool, RiskLevel
from backend.core.schemas import ActionNodeRead, ConnectionPreviewRead, EntityRead, ToolRead
from backend.providers.rest.parser import extract_endpoints, fetch_spec, parse_and_validate_spec


async def preview_openapi_spec(*, spec_url: str | None, raw_spec: str | None) -> ConnectionPreviewRead:
    warnings: list[str] = []
    if raw_spec and raw_spec.strip():
        raw = raw_spec
    elif spec_url and spec_url.strip():
        raw = await fetch_spec(spec_url.strip())
    else:
        raise ValueError("Provide an OpenAPI URL or paste the schema body.")

    spec = parse_and_validate_spec(raw)
    endpoints = extract_endpoints(spec)
    info = spec.get("info") if isinstance(spec.get("info"), dict) else {}
    methods = Counter(endpoint["method"] for endpoint in endpoints)
    tags: Counter[str] = Counter()
    sample_actions: list[dict[str, Any]] = []

    for endpoint in endpoints:
        operation = endpoint.get("operation") or {}
        endpoint_tags = operation.get("tags") if isinstance(operation.get("tags"), list) else []
        if endpoint_tags:
            for tag in endpoint_tags:
                tags[str(tag)] += 1
        else:
            tags[_entity_key_from_path(endpoint["path"])] += 1
        if len(sample_actions) < 8:
            sample_actions.append(
                {
                    "method": endpoint["method"],
                    "path": endpoint["path"],
                    "name": operation.get("operationId") or f"{endpoint['method']} {endpoint['path']}",
                    "description": operation.get("summary") or operation.get("description") or "",
                    "tags": endpoint_tags,
                }
            )

    servers = []
    for server in spec.get("servers") or []:
        if isinstance(server, dict) and server.get("url"):
            servers.append(str(server["url"]))
    if not servers and spec_url:
        warnings.append("No OpenAPI servers were declared; the connection base URL will be used.")
    if not endpoints:
        warnings.append("No REST operations were found in this OpenAPI document.")

    return ConnectionPreviewRead(
        title=str(info.get("title") or "OpenAPI API"),
        version=str(info.get("version")) if info.get("version") else None,
        servers=servers[:8],
        endpoint_count=len(endpoints),
        methods=dict(sorted(methods.items())),
        tags=dict(tags.most_common(20)),
        sample_actions=sample_actions,
        warnings=warnings,
    )


async def workspace_catalog(session: AsyncSession, workspace_id: uuid.UUID) -> dict[str, Any]:
    actions = await list_workspace_actions(session, workspace_id)
    tools = await list_workspace_tools(session, workspace_id)
    entities = infer_entities(actions)
    totals = {
        "actions": len(actions),
        "tools": len(tools),
        "entities": len(entities),
        "read_actions": sum(1 for action in actions if _risk_value(action.risk_level) == RiskLevel.read.value),
        "approval_actions": sum(1 for action in actions if _risk_value(action.risk_level) != RiskLevel.read.value),
    }
    return {"actions": actions, "tools": tools, "entities": entities, "totals": totals}


async def list_workspace_actions(session: AsyncSession, workspace_id: uuid.UUID) -> list[ActionNodeRead]:
    result = await session.execute(
        select(ActionNode)
        .where(ActionNode.workspace_id == workspace_id, ActionNode.status != ActionNodeStatus.deprecated)
        .order_by(ActionNode.source_index, ActionNode.method, ActionNode.path)
    )
    return [ActionNodeRead.model_validate(row, from_attributes=True) for row in result.scalars().all()]


async def list_workspace_tools(session: AsyncSession, workspace_id: uuid.UUID) -> list[ToolRead]:
    result = await session.execute(
        select(GeneratedTool)
        .where(GeneratedTool.workspace_id == workspace_id)
        .order_by(GeneratedTool.name)
    )
    return [ToolRead.model_validate(row, from_attributes=True) for row in result.scalars().all()]


async def ready_connection_count(session: AsyncSession, workspace_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count(Connection.id)).where(Connection.workspace_id == workspace_id)
    )
    return int(result.scalar_one() or 0)


def infer_entities(actions: list[ActionNodeRead]) -> list[EntityRead]:
    buckets: dict[str, list[ActionNodeRead]] = defaultdict(list)
    for action in actions:
        entity_id = _entity_id(action)
        buckets[entity_id].append(action)

    entities: list[EntityRead] = []
    for entity_id, rows in buckets.items():
        read_count = sum(1 for row in rows if _risk_value(row.risk_level) == RiskLevel.read.value)
        write_count = sum(1 for row in rows if _risk_value(row.risk_level) == RiskLevel.write.value)
        risky_count = len(rows) - read_count - write_count
        label = _label_from_entity_id(entity_id)
        entities.append(
            EntityRead(
                id=entity_id,
                label=label,
                description=f"{label} operations inferred from OpenAPI tags and paths.",
                action_count=len(rows),
                read_count=read_count,
                write_count=write_count,
                risky_count=risky_count,
                sample_paths=list(dict.fromkeys(row.path for row in rows))[:5],
            )
        )
    return sorted(entities, key=lambda item: (-item.action_count, item.label))


def _entity_id(action: ActionNodeRead) -> str:
    tags = [str(tag).strip() for tag in (action.tags or []) if str(tag).strip()]
    if tags:
        return _slug(tags[0])
    return _slug(_entity_key_from_path(action.path))


def _entity_key_from_path(path: str) -> str:
    segments = [segment for segment in (path or "").split("/") if segment and not segment.startswith("{")]
    return segments[0] if segments else "api"


def _label_from_entity_id(entity_id: str) -> str:
    return " ".join(part.capitalize() for part in entity_id.split("-")) or "API"


def _slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in cleaned.split("-") if part) or "api"


def _risk_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)
