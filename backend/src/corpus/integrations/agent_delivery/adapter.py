from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from agent_delivery_runtime.domain import (
    DeployableAgentBundle, InteractionRecord, new_id, now_iso,
)
from agent_delivery_runtime.ports import (
    DeliveryStorePort,
    DeployedAgentRuntimePort,
    DeploymentJobPort,
)
from agent_delivery_runtime.service import (
    ChannelHostService,
    DeploymentService,
    OperationsService,
)

from corpus.shared.agent_delivery import (
    ActivationProjection,
    ChannelProjection,
    DeployableBundleSpec,
    DeploymentProjection,
    EvaluationCandidateProjection,
    InteractionProjection,
    PublicAgentProjection,
    PublicSessionProjection,
)


@dataclass(frozen=True)
class NeutralAgentDeliveryAdapter:
    """Corpus boundary over the neutral delivery domain.

    Corpus supplies owner authorization, persistence, jobs, and the deployed
    runtime. Proof-only SQLite, bearer-token, catalogue, and HTTP adapters are
    deliberately outside this boundary.
    """

    store: DeliveryStorePort
    runtime: DeployedAgentRuntimePort
    jobs: DeploymentJobPort | None = None

    def create_channel(self, name: str, slug: str) -> ChannelProjection:
        return _channel(self._channels().create_channel(name, slug))

    def set_channel_enabled(self, channel_id: str, enabled: bool) -> ChannelProjection:
        return _channel(self._channels().set_enabled(channel_id, enabled))

    def request_deployment(
        self,
        channel_id: str,
        spec: DeployableBundleSpec,
    ) -> DeploymentProjection:
        return _deployment(self._deployments().request(channel_id, _bundle(spec)))

    def verify_deployment(self, deployment_id: str) -> DeploymentProjection:
        return _deployment(self._deployments().verify(deployment_id))

    def retry_deployment(self, deployment_id: str) -> DeploymentProjection:
        return _deployment(self._deployments().retry(deployment_id))

    def rollback(self, channel_id: str, deployment_id: str) -> ActivationProjection:
        value = self._deployments().rollback(channel_id, deployment_id)
        return ActivationProjection(
            value.activation_id,
            value.channel_id,
            value.deployment_id,
            value.reason,
        )

    def create_public_session(
        self,
        slug: str,
    ) -> tuple[PublicSessionProjection, PublicAgentProjection]:
        session, projection = self._channels().create_session(slug)
        return _session(session), _public(projection)

    def public_projection(self, slug: str, session_id: str) -> PublicAgentProjection:
        return _public(self._channels().projection(slug, session_id))

    def invoke(
        self,
        slug: str,
        session_id: str,
        text: str,
        request_id: str,
    ) -> tuple[PublicAgentProjection, InteractionProjection]:
        projection, interaction = self._channels().invoke(slug, session_id, text, request_id)
        return _public(projection), _interaction(interaction)

    def resolve_review(
        self,
        slug: str,
        session_id: str,
        review_id: str,
        accepted: bool,
        request_id: str,
    ) -> tuple[PublicAgentProjection, InteractionProjection]:
        channel_service = self._channels()
        session, deployment = channel_service._public_context(slug, session_id)
        started = now_iso()
        projection = self.runtime.resolve_review(
            deployment.bundle,
            session.runtime_session_id,
            review_id,
            accepted,
            request_id,
        )
        assistant = next(
            (
                str(turn.get("content", ""))
                for turn in reversed(projection.messages)
                if turn.get("role") == "assistant"
            ),
            "",
        )
        interaction = InteractionRecord(
            new_id("int"), session.session_id, deployment.deployment_id,
            "Approved the pending Agent action." if accepted else "Rejected the pending Agent action.",
            assistant[:1000], "completed", started, now_iso(),
            {"request_id": request_id, "projection_revision": projection.revision, "surface_count": len(projection.surfaces)},
        )
        self.store.save_interaction(interaction)
        return _public(projection), _interaction(interaction)

    def interactions(self) -> tuple[InteractionProjection, ...]:
        return tuple(_interaction(value) for value in self._operations().list())

    def interaction(self, interaction_id: str) -> InteractionProjection:
        return _interaction(self._operations().get(interaction_id))

    def evaluation_candidate(self, interaction_id: str) -> EvaluationCandidateProjection:
        value = self._operations().evaluation_candidate(interaction_id)
        return EvaluationCandidateProjection(
            value.candidate_id,
            value.interaction_id,
            value.deployment_id,
            value.input_summary,
            value.output_summary,
            _safe_mapping(value.trace),
        )

    def _channels(self) -> ChannelHostService:
        return ChannelHostService(self.store, self.runtime)

    def _deployments(self) -> DeploymentService:
        return DeploymentService(self.store, self.runtime, self.jobs)

    def _operations(self) -> OperationsService:
        return OperationsService(self.store)


def _bundle(spec: DeployableBundleSpec) -> DeployableAgentBundle:
    return DeployableAgentBundle(
        spec.bundle_id,
        spec.name,
        spec.version,
        spec.content_hash,
        spec.routedeck_app_hash,
        spec.surface_contract_hash,
        spec.eligibility_hash,
        spec.runtime_kind,
        _safe_mapping(spec.runtime_config),
    )


def _channel(value: Any) -> ChannelProjection:
    return ChannelProjection(value.channel_id, value.name, value.slug, value.enabled)


def _deployment(value: Any) -> DeploymentProjection:
    return DeploymentProjection(
        value.deployment_id,
        value.channel_id,
        value.bundle.bundle_id,
        value.bundle.content_hash,
        value.status.value,
        value.failure_code,
        value.failure_message,
    )


def _session(value: Any) -> PublicSessionProjection:
    return PublicSessionProjection(
        value.session_id,
        value.channel_id,
        value.activation_id,
        value.deployment_id,
    )


def _public(value: Any) -> PublicAgentProjection:
    return PublicAgentProjection(
        value.revision,
        tuple(_safe_mapping(item) for item in value.messages),
        tuple(_safe_mapping(item) for item in value.surfaces),
        tuple(_safe_mapping(item) for item in value.suggested_actions),
    )


def _interaction(value: Any) -> InteractionProjection:
    return InteractionProjection(
        value.interaction_id,
        value.session_id,
        value.deployment_id,
        value.input_summary,
        value.output_summary,
        value.status,
        _safe_mapping(value.trace),
    )


def _safe_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _safe_value(item) for key, item in value.items()}


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return _safe_mapping(value)
    if isinstance(value, (tuple, list)):
        return [_safe_value(item) for item in value]
    return str(type(value).__name__)


__all__ = ["NeutralAgentDeliveryAdapter"]
