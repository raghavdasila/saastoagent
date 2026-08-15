from __future__ import annotations

import uuid

from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import ProviderInvocationContext, ProviderResult

from corpus.auth.contracts import AgentOwnerScopeGateway

from .service import EvaluationService


_ORIGIN_BY_SOURCE_KIND = {
    "toolrouter": "generated",
    "sandbox": "sandbox",
    "operations": "operations",
}


class CurrentEvaluationProvider:
    def __init__(
        self,
        service: EvaluationService,
        owner_scope: AgentOwnerScopeGateway,
    ) -> None:
        self.service = service
        self.owner_scope = owner_scope

    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        bindings = tuple(
            binding
            for binding in context.session.private_state.entity_bindings
            if binding.entity_kind == "agent"
        )
        if len(bindings) != 1:
            raise RuntimeError(
                "One exact selected Agent is required for current evaluation context."
            )
        organization_id = await self.owner_scope.organization_id_for_route(
            context.session.session_id
        )
        agent_id = uuid.UUID(bindings[0].private_id)
        collection = await self.service.list(organization_id, agent_id)
        pending_counts = {origin: 0 for origin in _ORIGIN_BY_SOURCE_KIND.values()}
        active_count = 0
        for evaluation_set in collection.evaluation_sets:
            for case in evaluation_set.cases:
                attempt = case.latest_run_attempt
                if attempt is not None and attempt.status in {"queued", "running"}:
                    active_count += 1
                origin = _ORIGIN_BY_SOURCE_KIND.get(case.source_kind)
                if (
                    origin is not None
                    and case.latest_status is None
                    and not case.removed
                    and (attempt is None or attempt.status == "failed")
                ):
                    pending_counts[origin] += 1
        return ProviderResult(
            values=FrozenJsonObject(
                {
                    "evaluation_set_count": len(collection.evaluation_sets),
                    "pending_generated_case_count": pending_counts["generated"],
                    "pending_sandbox_case_count": pending_counts["sandbox"],
                    "pending_operations_case_count": pending_counts["operations"],
                    "active_case_run_count": active_count,
                }
            )
        )


__all__ = ["CurrentEvaluationProvider"]
