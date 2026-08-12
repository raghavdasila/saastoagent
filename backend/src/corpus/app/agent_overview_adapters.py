from __future__ import annotations

import uuid
from dataclasses import dataclass

from corpus.features.agents.domain import AgentProductOverview
from corpus.features.agents.service import AgentService
from corpus.features.builder.service import BuilderService
from corpus.features.channels.service import ChannelService
from corpus.features.deployment.service import DeploymentService
from corpus.features.designer.ports import DesignerUnavailable
from corpus.features.designer.service import DesignerService
from corpus.features.evaluation.service import EvaluationService
from corpus.features.operations.service import OperationsService


@dataclass(frozen=True)
class CorpusAgentProductOverviewGateway:
    agents: AgentService
    designer: DesignerService
    builder: BuilderService
    evaluation: EvaluationService
    channels: ChannelService
    deployments: DeploymentService
    operations: OperationsService

    async def overview(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentProductOverview:
        agent = await self.agents.get(organization_id, agent_id)
        attachments = await self.agents.repository.list_source_attachments(
            organization_id, agent_id
        )
        try:
            design = await self.designer.get(organization_id, agent_id)
        except DesignerUnavailable:
            design = None
        builds = (await self.builder.list(organization_id, agent_id)).builds
        evaluations = (
            await self.evaluation.list(organization_id, agent_id)
        ).evaluation_sets
        channels = await self.channels.list(organization_id, agent_id)
        deployments = await self.deployments.list(organization_id, agent_id)
        interactions = (
            await self.operations.list(organization_id, agent_id)
        ).interactions

        design_status = "missing"
        design_revision = None
        if design is not None:
            design_status = "accepted" if design.accepted_revision_id else "draft"
            if design.revisions:
                design_revision = design.revisions[-1].revision

        latest_build = max(builds, key=lambda item: item.created_at, default=None)
        latest_evaluation = max(
            evaluations, key=lambda item: item.created_at, default=None
        )
        evaluation_status = None
        evaluation_case_count = 0
        evaluation_eligible = None
        if latest_evaluation is not None:
            evaluation_case_count = len(latest_evaluation.cases)
            evaluation_eligible = latest_evaluation.eligible
            evaluation_status = _evaluation_status(latest_evaluation)

        channel = max(channels, key=lambda item: item.created_at, default=None)
        delivery_status, hosted_path = _delivery_status(channel, deployments)

        return AgentProductOverview(
            agent_id=agent.id,
            agent_version=agent.current_version,
            source_count=len(attachments),
            design_status=design_status,
            design_revision=design_revision,
            build_status=latest_build.status if latest_build else None,
            build_runtime_lifecycle=(
                latest_build.runtime_lifecycle if latest_build else None
            ),
            evaluation_status=evaluation_status,
            evaluation_case_count=evaluation_case_count,
            evaluation_eligible=evaluation_eligible,
            delivery_status=delivery_status,
            hosted_path=hosted_path,
            operations_count=len(interactions),
            next_step=_next_step(
                design_status=design_status,
                build=latest_build,
                evaluation_status=evaluation_status,
                evaluation_eligible=evaluation_eligible,
                delivery_status=delivery_status,
                operations_count=len(interactions),
            ),
        )


def _evaluation_status(value) -> str:
    if value.generation_status in {"queued", "running", "failed"}:
        return f"generation_{value.generation_status}"
    attempts = [
        case.latest_run_attempt.status
        for case in value.cases
        if case.latest_run_attempt is not None
    ]
    if any(status in {"queued", "running"} for status in attempts):
        return "running"
    if any(status == "failed" for status in attempts):
        return "failed"
    if value.eligible is True:
        return "eligible"
    if value.eligible is False:
        return "ineligible"
    return "ready" if value.cases else "empty"


def _delivery_status(channel, deployments) -> tuple[str, str | None]:
    if channel is None:
        return "none", None
    hosted_path = f"/{channel.slug}" if channel.status == "ready" else None
    active = next(
        (
            item
            for item in deployments
            if channel.active_deployment_id is not None
            and item.id == channel.active_deployment_id
            and item.status == "ready"
        ),
        None,
    )
    if active is not None:
        return ("live" if channel.enabled else "disabled"), hosted_path
    deployment = max(deployments, key=lambda item: item.created_at, default=None)
    if deployment is not None and deployment.status in {"queued", "running"}:
        return "deploying", hosted_path
    if deployment is not None and deployment.status == "failed":
        return "failed", hosted_path
    return "channel_only", hosted_path


def _next_step(
    *, design_status, build, evaluation_status, evaluation_eligible,
    delivery_status, operations_count,
) -> str:
    if design_status == "missing":
        return "Describe and review this Agent in Designer."
    if design_status == "draft":
        return "Review the current Designer proposal."
    if build is None:
        return "Request and assemble the accepted design in Builds."
    if build.status == "failed":
        return "Inspect the failed build and choose whether to retry it."
    if build.status != "ready":
        return "Wait for the durable build attempt to finish."
    if build.runtime_lifecycle != "running":
        return "Start the exact build, then try it privately in Sandbox."
    if evaluation_status in {None, "empty", "generation_queued", "generation_running"}:
        return "Review the exact-build evaluation coverage as it becomes ready."
    if evaluation_eligible is not True:
        return "Run or repair the exact-build evaluation cases."
    if delivery_status not in {"live", "disabled"}:
        return "Configure and review hosted delivery for the eligible build."
    if operations_count == 0:
        return "Try the hosted Agent, then inspect its interaction evidence."
    return "Inspect deployed interaction evidence in Operations."


__all__ = ["CorpusAgentProductOverviewGateway"]
