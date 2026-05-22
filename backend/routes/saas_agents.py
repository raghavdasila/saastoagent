import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_active_user
from backend.core.database import get_async_session
from backend.core.models import AgentExecutionTrace, User, SaaSAgent, SaaSAgentDeployment, SaaSAgentMember, SaaSAgentRole
from backend.core.schemas import (
    AgentApprovalDecisionRead,
    AgentApprovalRead,
    SaaSAgentCreate,
    SaaSAgentDeploymentRead,
    SaaSAgentDeploymentUpdate,
    SaaSAgentRead,
    SaaSAgentStats,
)
from backend.core.tenancy import create_tenant_schema
from backend.services.agent.rest_operator import (
    approve_pending_execution_trace,
    cancel_pending_execution_trace,
    list_pending_approval_traces,
)
from backend.services.deployed_agents import get_or_create_deployment
from backend.services.support.stats import get_saas_agent_stats

router = APIRouter(prefix="/api/saas-agents", tags=["saas-agents"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SaaSAgentRead)
async def create_saas_agent(
    body: SaaSAgentCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    existing = await session.execute(select(SaaSAgent).where(SaaSAgent.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SaaS Agent slug already taken",
        )

    saas_agent = SaaSAgent(
        id=uuid.uuid4(),
        name=body.name,
        slug=body.slug,
        created_by=user.id,
    )
    session.add(saas_agent)

    member = SaaSAgentMember(
        user_id=user.id,
        saas_agent_id=saas_agent.id,
        role=SaaSAgentRole.owner,
    )
    session.add(member)

    await session.commit()
    await session.refresh(saas_agent)
    await create_tenant_schema(saas_agent.id)

    return SaaSAgentRead(
        id=saas_agent.id,
        name=saas_agent.name,
        slug=saas_agent.slug,
        created_by=saas_agent.created_by,
        created_at=saas_agent.created_at,
        role=SaaSAgentRole.owner.value,
    )


@router.get("", response_model=list[SaaSAgentRead])
async def list_saas_agents(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(SaaSAgent, SaaSAgentMember.role)
        .join(SaaSAgentMember, SaaSAgentMember.saas_agent_id == SaaSAgent.id)
        .where(SaaSAgentMember.user_id == user.id)
        .order_by(SaaSAgent.created_at.desc())
    )
    result = await session.execute(stmt)
    rows = result.all()

    return [
        SaaSAgentRead(
            id=saas_agent.id,
            name=saas_agent.name,
            slug=saas_agent.slug,
            created_by=saas_agent.created_by,
            created_at=saas_agent.created_at,
            role=role.value,
        )
        for saas_agent, role in rows
    ]


@router.get("/{saas_agent_id}", response_model=SaaSAgentRead)
async def get_saas_agent(
    saas_agent_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(SaaSAgent, SaaSAgentMember.role)
        .join(SaaSAgentMember, SaaSAgentMember.saas_agent_id == SaaSAgent.id)
        .where(SaaSAgent.id == saas_agent_id, SaaSAgentMember.user_id == user.id)
    )
    result = await session.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this SaaS Agent",
        )

    saas_agent, role = row
    return SaaSAgentRead(
        id=saas_agent.id,
        name=saas_agent.name,
        slug=saas_agent.slug,
        created_by=saas_agent.created_by,
        created_at=saas_agent.created_at,
        role=role.value,
    )


@router.get("/{saas_agent_id}/stats", response_model=SaaSAgentStats)
async def get_saas_agent_stats_route(
    saas_agent_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(SaaSAgentMember).where(
        SaaSAgentMember.saas_agent_id == saas_agent_id,
        SaaSAgentMember.user_id == user.id,
    )
    result = await session.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this SaaS Agent",
        )

    stats = await get_saas_agent_stats(saas_agent_id)
    return SaaSAgentStats(**stats)


@router.get("/{saas_agent_id}/deployment", response_model=SaaSAgentDeploymentRead)
async def get_saas_agent_deployment(
    saas_agent_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    await _require_saas_agent_admin(saas_agent_id, user, session)
    return await get_or_create_deployment(saas_agent_id=saas_agent_id, db=session)


@router.put("/{saas_agent_id}/deployment", response_model=SaaSAgentDeploymentRead)
async def update_saas_agent_deployment(
    saas_agent_id: uuid.UUID,
    body: SaaSAgentDeploymentUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    await _require_saas_agent_admin(saas_agent_id, user, session)
    deployment = await get_or_create_deployment(saas_agent_id=saas_agent_id, db=session)
    deployment.enabled = body.enabled
    deployment.visitor_auth_mode = body.visitor_auth_mode
    deployment.execution_mode = body.execution_mode
    deployment.default_write_policy = body.default_write_policy
    deployment.welcome_message = body.welcome_message
    await session.commit()
    await session.refresh(deployment)
    return deployment


@router.get("/{saas_agent_id}/approvals/pending", response_model=list[AgentApprovalRead])
async def list_pending_approvals(
    saas_agent_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    await _require_saas_agent_admin(saas_agent_id, user, session)
    traces = await list_pending_approval_traces(saas_agent_id=saas_agent_id, db=session)
    return [_approval_read(trace) for trace in traces]


@router.post("/{saas_agent_id}/approvals/{trace_id}/approve", response_model=AgentApprovalDecisionRead)
async def approve_pending_approval(
    saas_agent_id: uuid.UUID,
    trace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    await _require_saas_agent_admin(saas_agent_id, user, session)
    trace = await _get_agent_trace_or_404(saas_agent_id, trace_id, session)
    message, result = await approve_pending_execution_trace(trace=trace, approved_by=user.id, db=session)
    await session.refresh(trace)
    return AgentApprovalDecisionRead(
        trace_id=trace.id,
        status=trace.status,
        approval_state=trace.approval_state,
        message=message,
        result=result,
    )


@router.post("/{saas_agent_id}/approvals/{trace_id}/cancel", response_model=AgentApprovalDecisionRead)
async def cancel_pending_approval(
    saas_agent_id: uuid.UUID,
    trace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    await _require_saas_agent_admin(saas_agent_id, user, session)
    trace = await _get_agent_trace_or_404(saas_agent_id, trace_id, session)
    message = await cancel_pending_execution_trace(trace=trace, canceled_by=user.id, db=session)
    await session.refresh(trace)
    return AgentApprovalDecisionRead(
        trace_id=trace.id,
        status=trace.status,
        approval_state=trace.approval_state,
        message=message,
        result=trace.result,
    )


async def _require_saas_agent_admin(
    saas_agent_id: uuid.UUID,
    user: User,
    session: AsyncSession,
) -> SaaSAgentMember:
    result = await session.execute(
        select(SaaSAgentMember).where(
            SaaSAgentMember.saas_agent_id == saas_agent_id,
            SaaSAgentMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this SaaS Agent")
    if member.role not in (SaaSAgentRole.owner, SaaSAgentRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SaaS Agent admin role required")
    return member


async def _get_agent_trace_or_404(
    saas_agent_id: uuid.UUID,
    trace_id: uuid.UUID,
    session: AsyncSession,
) -> AgentExecutionTrace:
    trace = await session.get(AgentExecutionTrace, trace_id)
    if trace is None or trace.saas_agent_id != saas_agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    return trace


def _approval_read(trace: AgentExecutionTrace) -> AgentApprovalRead:
    return AgentApprovalRead(
        trace_id=trace.id,
        trace_token=str(trace.id)[:8],
        status=trace.status,
        approval_state=trace.approval_state,
        tool_name=trace.tool_name,
        action_name=trace.action_name,
        method=trace.method,
        path=trace.path,
        risk_level=trace.risk_level,
        inputs=trace.inputs or {},
        requested_by=trace.requested_by,
        created_at=trace.created_at,
    )
