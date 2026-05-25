from __future__ import annotations

import json
import uuid
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from routedeck_core import RouteDeckDispatchInput, RouteDeckDispatchResult, RouteDeckRuntimeState
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_optional_active_user
from backend.core.database import get_async_session
from backend.core.models import User
from backend.core.schemas import AppGraphRequest, AppGraphState, CorpusActionRequest, CorpusActionResponse, CorpusStateResponse, EntryGraphMessage
from backend.services.app_graph import corpus_graph_runtime, route_deck_runtime

router = APIRouter(tags=["corpus-graph"])

@router.get("/api/corpus/state", response_model=CorpusStateResponse)
async def get_corpus_state(
    node_id: str | None = None,
    saas_agent_id: uuid.UUID | None = None,
    projection_version: int = 1,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    runtime_state = await route_deck_runtime.snapshot(
        {
            "request": AppGraphRequest(node_id=node_id, saas_agent_id=saas_agent_id),
            "user": user,
            "db": db,
            "projection_version": projection_version,
        }
    )
    return _corpus_state_response_from_routedeck_state(runtime_state)


@router.get("/api/corpus/stream")
async def stream_corpus_turn(
    user_input: str = "",
    node_id: str | None = None,
    saas_agent_id: uuid.UUID | None = None,
    projection_version: int = 1,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    turn_id = str(uuid.uuid4())

    async def events() -> AsyncIterator[str]:
        if not user_input.strip():
            async for event in route_deck_runtime.stream(
                {
                    "request": AppGraphRequest(node_id=node_id, saas_agent_id=saas_agent_id),
                    "user": user,
                    "db": db,
                    "projection_version": projection_version,
                }
            ):
                yield _sse(event.event_type, {"turn_id": turn_id, **event.model_dump(mode="json")})
            return

        async for event in corpus_graph_runtime.stream_corpus_turn(
            request=AppGraphRequest(user_input=user_input, node_id=node_id, saas_agent_id=saas_agent_id),
            user=user,
            db=db,
            projection_version=projection_version,
        ):
            yield _sse(event["event_type"], {"turn_id": turn_id, **event})

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/api/corpus/action", response_model=CorpusActionResponse)
async def corpus_action(
    body: CorpusActionRequest,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    graph_state = body.state or AppGraphState(
        node=body.node_id or "home",
        active_saas_agent_id=body.saas_agent_id,
    )
    result = await route_deck_runtime.dispatch(
        RouteDeckDispatchInput(
            operation_id=body.operation_id,
            args=body.args,
            graph_state=graph_state.model_dump(mode="json"),
            projection_version=body.projection_version or 1,
        ),
        {
            "request": AppGraphRequest(
                state=body.state,
                node_id=body.node_id,
                saas_agent_id=body.saas_agent_id,
            ),
            "user": user,
            "db": db,
            "node_id": body.node_id,
            "saas_agent_id": body.saas_agent_id,
            "projection_version": body.projection_version or 1,
        },
    )
    return _corpus_action_response_from_routedeck_result(result)


@router.get("/api/diagnostics/stream")
async def stream_diagnostics(
    node_id: str | None = None,
    saas_agent_id: uuid.UUID | None = None,
    projection_version: int = 1,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    context = {
        "request": AppGraphRequest(node_id=node_id, saas_agent_id=saas_agent_id),
        "user": user,
        "db": db,
        "projection_version": projection_version,
    }
    state = await route_deck_runtime.snapshot(context)
    introspection = await route_deck_runtime.inspect(context=context)
    runtime_snapshot = introspection.diagnostics.get("runtime_snapshot") if introspection.diagnostics else {}
    snapshot = {
        "graph_manifest": route_deck_runtime.manifest.model_dump(by_alias=True),
        "runtime_snapshot": runtime_snapshot or {},
        "introspection": introspection.model_dump(mode="json"),
        "projection": state.projection.model_dump(mode="json"),
    }
    return StreamingResponse(
        _single_event(
            "diagnostic_event",
            {
                "turn_id": str(uuid.uuid4()),
                "projection_version": state.projection.projection_version,
                "snapshot": snapshot,
            },
        ),
        media_type="text/event-stream",
    )


async def _single_event(event_type: str, payload: dict[str, Any]) -> AsyncIterator[str]:
    yield _sse(event_type, payload)


def _corpus_state_response_from_routedeck_state(state: RouteDeckRuntimeState) -> CorpusStateResponse:
    return CorpusStateResponse(
        state=AppGraphState.model_validate(state.graph_state or {}),
        projection=state.projection,
        replace_path=state.location,
    )


def _corpus_action_response_from_routedeck_result(result: RouteDeckDispatchResult) -> CorpusActionResponse:
    return CorpusActionResponse(
        state=AppGraphState.model_validate(result.state.graph_state or {}),
        projection=result.state.projection,
        active_surface=result.active_surface,
        messages=[EntryGraphMessage.model_validate(message) for message in result.messages],
        replace_path=result.state.location or result.metadata.get("replace_path"),
    )


def _sse(event_type: str, payload: dict[str, Any]) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
