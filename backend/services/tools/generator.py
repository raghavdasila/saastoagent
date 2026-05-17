from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import ActionNode, ActionNodeStatus, GeneratedTool

_NAME_RE = re.compile(r"[^a-z0-9_]")


def sanitize_tool_name(action_node: ActionNode) -> str:
    raw = action_node.name if action_node.name and " " not in action_node.name and "/" not in action_node.name else f"{action_node.method}_{action_node.path}"
    raw = raw.lower().replace("-", "_").replace("/", "_").replace(".", "_")
    raw = _NAME_RE.sub("", raw)
    raw = re.sub(r"_+", "_", raw).strip("_")
    if raw and not raw[0].isalpha():
        raw = f"fn_{raw}"
    return raw[:64] or "unnamed_tool"


def build_function_schema(action_node: ActionNode) -> dict:
    properties: dict[str, dict] = {}
    required: list[str] = []

    for param in action_node.parameters or []:
        if not isinstance(param, dict) or not param.get("name"):
            continue
        name = str(param["name"])
        schema = param.get("schema") if isinstance(param.get("schema"), dict) else {}
        properties[name] = _map_schema(schema)
        if param.get("description"):
            properties[name]["description"] = str(param["description"])[:240]
        if param.get("required") or param.get("in") == "path":
            required.append(name)

    request_body = action_node.request_body or {}
    if isinstance(request_body, dict):
        content = request_body.get("content")
        if isinstance(content, dict):
            json_content = content.get("application/json") or next(iter(content.values()), {})
            if isinstance(json_content, dict):
                schema = json_content.get("schema")
                if isinstance(schema, dict):
                    for prop_name, prop_schema in list((schema.get("properties") or {}).items())[:30]:
                        properties[str(prop_name)] = _map_schema(prop_schema if isinstance(prop_schema, dict) else {})
                    for name in schema.get("required") or []:
                        required.append(str(name))

    for path_param in re.findall(r"\{(\w+)\}", action_node.path or ""):
        properties.setdefault(path_param, {"type": "string", "description": f"Path parameter {path_param}"})
        required.append(path_param)

    return {
        "name": sanitize_tool_name(action_node),
        "description": (action_node.description or action_node.name or "")[:1024],
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": list(dict.fromkeys(required)),
        },
    }


def _map_schema(schema: dict) -> dict:
    if "enum" in schema:
        return {"type": "string", "enum": schema["enum"][:30]}
    raw_type = schema.get("type") or "string"
    if isinstance(raw_type, list):
        raw_type = next((item for item in raw_type if item != "null"), "string")
    if raw_type == "array":
        return {"type": "array", "items": _map_schema(schema.get("items") if isinstance(schema.get("items"), dict) else {})}
    if raw_type == "object":
        return {"type": "object"}
    return {"type": raw_type if raw_type in {"string", "integer", "number", "boolean"} else "string"}


async def generate_tools_for_connection(connection_id, saas_agent_id, session: AsyncSession) -> dict[str, int]:
    existing_result = await session.execute(
        select(GeneratedTool).where(GeneratedTool.connection_id == connection_id)
    )
    existing = {tool.action_node_id: tool for tool in existing_result.scalars().all()}
    node_result = await session.execute(
        select(ActionNode).where(
            ActionNode.connection_id == connection_id,
            ActionNode.status != ActionNodeStatus.deprecated,
        )
    )
    nodes = node_result.scalars().all()
    generated = 0
    updated = 0
    seen_names: set[str] = set()

    for node in nodes:
        schema = build_function_schema(node)
        base_name = schema["name"]
        name = base_name
        counter = 2
        while name in seen_names:
            suffix = f"_{counter}"
            name = f"{base_name[:64 - len(suffix)]}{suffix}"
            counter += 1
        schema["name"] = name
        seen_names.add(name)

        tool = existing.get(node.id)
        if tool is None:
            session.add(
                GeneratedTool(
                    action_node_id=node.id,
                    connection_id=connection_id,
                    saas_agent_id=saas_agent_id,
                    name=name,
                    description=schema["description"],
                    function_schema=schema,
                    risk_level=node.risk_level,
                    requires_approval=node.risk_level.value in {"write", "destructive", "financial"},
                )
            )
            generated += 1
        else:
            tool.name = name
            tool.description = schema["description"]
            tool.function_schema = schema
            tool.risk_level = node.risk_level
            tool.requires_approval = node.risk_level.value in {"write", "destructive", "financial"}
            updated += 1

    await session.commit()
    return {"generated": generated, "updated": updated, "total": len(nodes)}
