from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from corpus.clarification import ClarificationInputRejected, screen_clarification_values
from corpus.features.agents.http import AgentsHttpProblem

from .schemas import ChannelCollectionView, ChannelView
from corpus.features.deployment.schemas import DeploymentCollectionView, DeploymentView


class PublicMessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=4000)


def create_channels_router(channels, deployments, owner_scope, delivery) -> APIRouter:
    router = APIRouter(tags=["agent-channels"])

    @router.get("/api/agents/{agent_id}/channels")
    async def list_channels(agent_id: uuid.UUID, request: Request):
        organization_id = await _owner(request, owner_scope)
        values = await channels.list(organization_id, agent_id)
        result = ChannelCollectionView(
            agent_id=agent_id,
            channels=tuple(ChannelView.model_validate(value) for value in values),
        )
        return _private(result)

    @router.get("/api/agents/{agent_id}/deployments")
    async def list_deployments(agent_id: uuid.UUID, request: Request):
        organization_id = await _owner(request, owner_scope)
        values = await deployments.list(organization_id, agent_id)
        result = DeploymentCollectionView(
            agent_id=agent_id,
            deployments=tuple(DeploymentView.model_validate(value) for value in values),
        )
        return JSONResponse(
            content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"}
        )

    @router.post("/api/public/agents/{slug}/sessions")
    async def create_public_session(slug: str):
        channel = await channels.get_public(slug)
        _require_public_channel(channel)
        await deployments.prepare_public(channel)
        session, projection = await asyncio.to_thread(delivery.create_public_session, channel.slug)
        return JSONResponse(
            content=jsonable_encoder({"session": session, "agent": _public_agent(projection)}),
            headers={"Cache-Control": "no-store"},
        )

    @router.get("/api/public/agents/{slug}/sessions/{session_id}")
    async def public_projection(slug: str, session_id: str):
        channel = await channels.get_public(slug)
        _require_public_channel(channel)
        await deployments.prepare_public(channel)
        projection = await asyncio.to_thread(delivery.public_projection, channel.slug, session_id)
        return JSONResponse(
            content=jsonable_encoder(_public_agent(projection)),
            headers={"Cache-Control": "no-store"},
        )

    @router.post("/api/public/agents/{slug}/sessions/{session_id}/messages")
    async def invoke_public_agent(slug: str, session_id: str, payload: PublicMessageInput):
        try:
            screen_clarification_values(payload.message)
        except ClarificationInputRejected as error:
            raise AgentsHttpProblem(400, "secret_input_rejected", str(error)) from error
        channel = await channels.get_public(slug)
        _require_public_channel(channel)
        await deployments.prepare_public(channel)
        projection, interaction = await asyncio.to_thread(
            delivery.invoke, channel.slug, session_id, payload.message, uuid.uuid4().hex
        )
        return JSONResponse(
            content=jsonable_encoder(
                {"agent": _public_agent(projection), "interaction": interaction}
            ),
            headers={"Cache-Control": "no-store"},
        )

    return router


def _require_public_channel(channel) -> None:
    if not channel.enabled or not channel.active_deployment_id:
        raise AgentsHttpProblem(
            503, "public_agent_unavailable", "This public Agent is unavailable."
        )


async def _owner(request: Request, owner_scope):
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.casefold() != "bearer" or not token:
        raise AgentsHttpProblem(401, "authentication_required", "Authentication is required.")
    return await owner_scope.organization_id_for_access_token(token)


def _private(value):
    return JSONResponse(
        content=jsonable_encoder(value), headers={"Cache-Control": "private, no-store"}
    )


def _public_agent(projection) -> dict[str, object]:
    """Project only end-user conversation state; runtime diagnostics are owner-only."""
    awaiting_clarification = False
    for surface in projection.surfaces:
        if surface.get("component") != "agent_runtime.clarification":
            continue
        props = surface.get("props")
        if isinstance(props, dict) and props.get("state") in {
            "needs_input",
            "needs_operation_choice",
        }:
            awaiting_clarification = True
            break
    return {
        "revision": projection.revision,
        "messages": projection.messages,
        "awaiting_clarification": awaiting_clarification,
    }


__all__ = ["create_channels_router"]
