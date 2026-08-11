from __future__ import annotations

import uuid
from dataclasses import dataclass

from corpus.features.evaluation.service import EvaluationService
from corpus.integrations.agent_delivery import (
    InteractionProjection,
    NeutralAgentDeliveryAdapter,
)

from .domain import OperationsLineage
from .ports import OperationsLineageGateway, OperationsUnavailable
from .schemas import OperationsCollectionView, OperationsEventView, OperationsInteractionView


@dataclass
class _RunInteraction:
    initial: InteractionProjection
    latest: InteractionProjection
    lineage: OperationsLineage
    continuation_count: int = 0


class OperationsService:
    def __init__(self, delivery: NeutralAgentDeliveryAdapter, lineage: OperationsLineageGateway, evaluation: EvaluationService) -> None:
        self.delivery, self.lineage, self.evaluation = delivery, lineage, evaluation

    async def list(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID | None = None,
    ) -> OperationsCollectionView:
        runs: list[_RunInteraction] = []
        active_by_session: dict[tuple[str, str], _RunInteraction] = {}
        runs_by_identity: dict[tuple[str, str, str], _RunInteraction] = {}
        for interaction in reversed(self.delivery.interactions()):
            request_id = interaction.trace.get("request_id")
            lineage = (
                await self.lineage.resolve(
                    organization_id, interaction.deployment_id, request_id
                )
                if isinstance(request_id, str)
                else None
            )
            session_key = (interaction.session_id, interaction.deployment_id)
            if lineage is not None:
                run_key = (*session_key, lineage.runtime_run_id)
                current = runs_by_identity.get(run_key)
                if current is None:
                    current = _RunInteraction(interaction, interaction, lineage)
                    runs.append(current)
                    runs_by_identity[run_key] = current
                else:
                    current.latest = interaction
                    current.lineage = lineage
                active_by_session[session_key] = current
                continue
            current = active_by_session.get(session_key)
            if current is None or interaction.status != "completed":
                continue
            answer_count = sum(
                event.get("kind") == "clarification.user_answer"
                for event in current.lineage.safe_events
            )
            if current.continuation_count >= answer_count:
                continue
            current.latest = interaction
            current.continuation_count += 1

        values = []
        for current in reversed(runs):
            lineage = current.lineage
            if agent_id is not None and lineage.agent_id != agent_id:
                continue
            values.append(OperationsInteractionView(
                interaction_id=current.initial.interaction_id,
                agent_id=lineage.agent_id, build_id=lineage.build_id,
                deployment_id=lineage.deployment_id,
                session_id=current.initial.session_id,
                input_summary=current.initial.input_summary,
                output_summary=current.latest.output_summary,
                status=current.latest.status,
                events=tuple(OperationsEventView(
                    sequence=int(item["sequence"]), kind=str(item["kind"]),
                    safe_data=dict(item.get("safe_data", {})),
                ) for item in lineage.safe_events),
            ))
        return OperationsCollectionView(interactions=tuple(values))

    async def promote(self, organization_id: uuid.UUID, *, interaction_id: str, set_name: str, title: str, category: str, difficulty: str, mandatory: bool):
        interaction = self.delivery.interaction(interaction_id)
        if interaction.status != "completed":
            raise OperationsUnavailable(
                "The interaction did not complete successfully."
            )
        request_id = interaction.trace.get("request_id")
        if not isinstance(request_id, str):
            raise OperationsUnavailable("The interaction does not have runnable evaluation lineage.")
        lineage = await self.lineage.resolve(organization_id, interaction.deployment_id, request_id)
        if lineage is None:
            raise OperationsUnavailable("The interaction is unavailable for this owner.")
        operations = tuple(dict.fromkeys(
            str(item["safe_data"]["operation_id"])
            for item in lineage.safe_events
            if item.get("kind") in {"api.result", "api.verification_result"}
            and isinstance(item.get("safe_data"), dict)
            and item["safe_data"].get("status") == "succeeded"
            and item["safe_data"].get("operation_id")
        ))
        if not operations:
            raise OperationsUnavailable("The interaction has no completed API operation to evaluate.")
        return await self.evaluation.create_case_from_operations(
            organization_id, lineage.agent_id, build_id=lineage.build_id,
            runtime_run_id=lineage.runtime_run_id, interaction_id=interaction.interaction_id,
            message=interaction.input_summary, set_name=set_name, title=title,
            category=category, difficulty=difficulty,
            expected_operation_ids=operations, mandatory=mandatory,
        )

    async def promote_current(
        self,
        organization_id: uuid.UUID,
        *,
        set_name: str,
        title: str,
        category: str,
        difficulty: str,
        mandatory: bool,
    ):
        interactions = (await self.list(organization_id)).interactions
        if len(interactions) != 1:
            raise OperationsUnavailable(
                "Promotion requires one exact owner interaction."
            )
        return await self.promote(
            organization_id,
            interaction_id=interactions[0].interaction_id,
            set_name=set_name,
            title=title,
            category=category,
            difficulty=difficulty,
            mandatory=mandatory,
        )


__all__ = ["OperationsService"]
