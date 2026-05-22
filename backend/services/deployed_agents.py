from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Connection, SaaSAgent, SaaSAgentDeployment
from backend.core.schemas import DeployedAgentProfile


VISITOR_AUTH_INHERIT = "inherit_from_connection"
VISITOR_AUTH_ANONYMOUS = "anonymous"
VISITOR_AUTH_LOGIN_REQUIRED = "login_required"
POLICY_ALLOWED_READ = "allowed_read"
POLICY_NEEDS_VISITOR_AUTH = "needs_visitor_auth"
POLICY_NEEDS_OWNER_APPROVAL = "needs_owner_approval"
POLICY_BLOCKED = "blocked"
POLICY_FAILED_WITH_RECOVERY = "failed_with_recovery"


def deployment_requires_login(deployment: Any, connections: Iterable[Any]) -> bool:
    mode = str(getattr(deployment, "visitor_auth_mode", VISITOR_AUTH_INHERIT) or VISITOR_AUTH_INHERIT)
    if mode == VISITOR_AUTH_ANONYMOUS:
        return False
    if mode == VISITOR_AUTH_LOGIN_REQUIRED:
        return True
    return any(_connection_requires_auth(connection) for connection in connections)


def deployment_policy_state(*, enabled: bool, auth_required: bool) -> str:
    if not enabled:
        return POLICY_BLOCKED
    if auth_required:
        return POLICY_NEEDS_VISITOR_AUTH
    return POLICY_ALLOWED_READ


def build_deployed_handoff_context(
    *,
    slug: str,
    auth_required: bool,
    visitor_auth_mode: str,
    execution_mode: str,
    default_write_policy: str,
) -> dict[str, Any]:
    return {
        "channel": "deployed_web",
        "deployment_slug": slug,
        "policy_snapshot": {
            "auth_required": auth_required,
            "visitor_auth_mode": visitor_auth_mode,
            "execution_mode": execution_mode,
            "default_write_policy": default_write_policy,
            "policy_state": deployment_policy_state(enabled=True, auth_required=auth_required),
        },
    }


async def get_or_create_deployment(
    *,
    saas_agent_id: uuid.UUID,
    db: AsyncSession,
) -> SaaSAgentDeployment:
    result = await db.execute(
        select(SaaSAgentDeployment).where(SaaSAgentDeployment.saas_agent_id == saas_agent_id)
    )
    deployment = result.scalar_one_or_none()
    if deployment is not None:
        return deployment
    deployment = SaaSAgentDeployment(saas_agent_id=saas_agent_id)
    db.add(deployment)
    await db.commit()
    await db.refresh(deployment)
    return deployment


async def deployment_profile_for_slug(
    *,
    slug: str,
    db: AsyncSession,
) -> tuple[SaaSAgent, Any, DeployedAgentProfile] | None:
    agent_result = await db.execute(select(SaaSAgent).where(SaaSAgent.slug == slug))
    agent = agent_result.scalar_one_or_none()
    if agent is None:
        return None
    deployment_result = await db.execute(
        select(SaaSAgentDeployment).where(SaaSAgentDeployment.saas_agent_id == agent.id)
    )
    deployment = deployment_result.scalar_one_or_none() or _disabled_default_deployment()
    connections = (
        await db.execute(select(Connection).where(Connection.saas_agent_id == agent.id))
    ).scalars().all()
    auth_required = deployment_requires_login(deployment, connections)
    profile = DeployedAgentProfile(
        saas_agent_id=agent.id,
        slug=agent.slug,
        name=agent.name,
        enabled=deployment.enabled,
        auth_required=auth_required,
        visitor_auth_mode=deployment.visitor_auth_mode,
        execution_mode=deployment.execution_mode,
        default_write_policy=deployment.default_write_policy,
        policy_state=deployment_policy_state(enabled=bool(deployment.enabled), auth_required=auth_required),
        welcome_message=deployment.welcome_message,
    )
    return agent, deployment, profile


def _disabled_default_deployment() -> Any:
    return SimpleNamespace(
        enabled=False,
        visitor_auth_mode=VISITOR_AUTH_INHERIT,
        execution_mode="sandbox",
        default_write_policy="confirm",
        welcome_message="How can I help?",
    )


def _connection_requires_auth(connection: Any) -> bool:
    auth_type = getattr(connection, "auth_type", None)
    if hasattr(auth_type, "value"):
        auth_type = auth_type.value
    return str(auth_type or "none") != "none"
