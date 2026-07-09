from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, status

from backend.core.credentials import encrypt_value
from backend.core.models import AuthType, Connection, ConnectionActivationState, ConnectionType, EncryptedCredential
from backend.core.schemas import CorpusGraphState, EntryGraphMessage
from backend.services.corpus.manifest import CorpusActionIds, CorpusNodeIds
from backend.services.catalog import SaaSAgent_catalog, preview_openapi_spec
from backend.services.discovery.activation import ActivationService

from .types import CorpusActionContext, CorpusActionResult


async def navigate_connection_configure(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.CONNECTION_CONFIGURE
    return CorpusActionResult(state=state)


async def connection_preview(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    preview = await preview_openapi_spec(spec_url=str(payload.get("spec_url") or ""), raw_spec=payload.get("raw_spec"))
    state.node = CorpusNodeIds.SCHEMA_PREVIEW
    state.graph_context["schema_preview"] = preview.model_dump()
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content=f"Previewed `{preview.title}` with {preview.endpoint_count} endpoints.")],
        evidence=[{"type": "schema_preview", **preview.model_dump()}],
    )


async def connection_activate(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    await context.queries.require_member(state.active_saas_agent_id, context.user, context.db)
    connection_id = payload.get("connection_id")
    if connection_id:
        connection = await context.db.get(Connection, uuid.UUID(str(connection_id)))
        if connection is None or connection.saas_agent_id != state.active_saas_agent_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    else:
        auth_type = str(payload.get("auth_type") or "none")
        connection = Connection(
            saas_agent_id=state.active_saas_agent_id,
            name=str(payload.get("name") or "Primary API"),
            type=ConnectionType.rest_api,
            provider="rest_api",
            config={
                "base_url": payload.get("base_url"),
                "spec_url": payload.get("spec_url"),
                "raw_spec": payload.get("raw_spec"),
                "auth_type": auth_type,
            },
            auth_type=AuthType(auth_type),
        )
        context.db.add(connection)
        await context.db.flush()
        credential_value = str(payload.get("credential_value") or "")
        if credential_value:
            context.db.add(EncryptedCredential(connection_id=connection.id, credential_type="credential_value", encrypted_value=encrypt_value(credential_value), metadata_={key: payload.get(key) for key in ("header_name", "query_param_name") if payload.get(key)}))
        context.db.add(ConnectionActivationState(connection_id=connection.id, saas_agent_id=state.active_saas_agent_id))
        await context.db.commit()
        await context.db.refresh(connection)
    state.active_connection_id = connection.id
    state.node = CorpusNodeIds.CATALOG_ACTIVATION
    events = []
    async for event in ActivationService().activate(connection_id=connection.id, saas_agent_id=state.active_saas_agent_id, session=context.db):
        events.append(event)
    state.node = CorpusNodeIds.CATALOG
    state.graph_context["activation_events"] = events
    state.graph_context["router_index"] = router_index_from_activation_events(events)
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content="The API catalog is activated and ready to inspect.")],
        evidence=[{"type": "activation", "events": events}],
    )


async def catalog_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if state.active_saas_agent_id:
        catalog = await SaaSAgent_catalog(context.db, state.active_saas_agent_id)
        state.graph_context["catalog"] = catalog
        state.graph_context["router_index"] = catalog.get("router_index")
    state.node = CorpusNodeIds.CATALOG
    return CorpusActionResult(state=state)


async def entities_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.ENTITIES
    return CorpusActionResult(state=state)


async def actions_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.ACTIONS
    return CorpusActionResult(state=state)


def router_index_from_activation_events(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("type") != "step" or event.get("step") != "router_index" or event.get("status") != "done":
            continue
        return {
            "status": event.get("router_index_status") or "ready",
            "router_version": event.get("router_version"),
            "document_count": int(event.get("router_documents_count") or 0),
            "endpoint_count": int(event.get("router_endpoint_count") or 0),
            "catalog_fingerprint": event.get("catalog_fingerprint"),
        }
    return None


def build_connection_handlers():
    return {
        CorpusActionIds.CONNECTION_CONFIGURE: navigate_connection_configure,
        CorpusActionIds.CONNECTION_PREVIEW: connection_preview,
        CorpusActionIds.CONNECTION_ACTIVATE: connection_activate,
        CorpusActionIds.CATALOG_OPEN: catalog_open,
        CorpusActionIds.ENTITIES_OPEN: entities_open,
        CorpusActionIds.ACTIONS_OPEN: actions_open,
    }
