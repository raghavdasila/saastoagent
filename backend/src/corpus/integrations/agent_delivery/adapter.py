from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from agent_delivery_runtime.domain import (
    DeployableAgentBundle, DeploymentMode, DeploymentTarget, InteractionRecord,
    SessionPurpose, new_id, now_iso,
)
from agent_delivery_runtime.ports import (
    DeliveryStorePort,
    DeployedAgentRuntimePort,
    DeploymentJobPort,
)
from agent_delivery_runtime.service import (
    AgentHostService,
    ChannelHostService,
    DeploymentService,
    OperationsService,
)

from corpus.shared.agent_delivery import (
    AgentSessionProjection,
    ActivationProjection,
    ChannelProjection,
    DeployableBundleSpec,
    DeploymentProjection,
    DeploymentTargetProjection,
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

    def ensure_sandbox_target(
        self,
        *,
        target_id: str,
        owner_scope: str,
        name: str,
    ) -> DeploymentTargetProjection:
        existing = self.store.target(target_id)
        if existing is None:
            self.store.create_target(DeploymentTarget(
                target_id=target_id,
                mode=DeploymentMode.SANDBOX,
                owner_scope=owner_scope,
                channel_id=None,
                name=name,
                created_at=now_iso(),
            ))
            existing = self.store.target(target_id)
        if existing is None or existing.mode is not DeploymentMode.SANDBOX or existing.owner_scope != owner_scope:
            raise RuntimeError("sandbox_target_identity_conflict")
        return _target(existing)

    def request_sandbox_deployment(
        self,
        target_id: str,
        spec: DeployableBundleSpec,
        *,
        request_key: str,
    ) -> DeploymentProjection:
        return _deployment(self._deployments().request(
            target_id,
            _bundle(spec),
            mode=DeploymentMode.SANDBOX,
            request_key=request_key,
        ))

    def retry_sandbox_deployment(
        self,
        deployment_id: str,
        *,
        request_key: str,
    ) -> DeploymentProjection:
        return _deployment(self._deployments().retry(
            deployment_id,
            request_key=request_key,
        ))

    def sandbox_deployments(self, target_id: str) -> tuple[DeploymentProjection, ...]:
        return tuple(_deployment(value) for value in self.store.deployments_for_target(target_id))

    def active_deployment(self, target_id: str) -> DeploymentProjection | None:
        activation = self.store.current_activation(target_id)
        if activation is None:
            return None
        value = self.store.deployment(activation.deployment_id)
        return _deployment(value) if value is not None else None

    def create_agent_session(
        self,
        target_id: str,
        purpose: str,
        *,
        owner_scope: str,
        expected_deployment_id: str | None = None,
    ) -> tuple[AgentSessionProjection, PublicAgentProjection]:
        session, projection = self._host().create_session(
            target_id,
            SessionPurpose(purpose),
            owner_scope=owner_scope,
            expected_deployment_id=expected_deployment_id,
        )
        return _agent_session(session), _public(projection)

    def agent_projection(
        self,
        target_id: str,
        session_id: str,
        *,
        owner_scope: str,
    ) -> PublicAgentProjection:
        return _public(self._host().projection(
            target_id, session_id, owner_scope=owner_scope
        ))

    def invoke_agent_session(
        self,
        target_id: str,
        session_id: str,
        text: str,
        request_id: str,
        *,
        owner_scope: str,
    ) -> tuple[PublicAgentProjection, InteractionProjection]:
        projection, interaction = self._host().invoke(
            target_id, session_id, text, request_id, owner_scope=owner_scope
        )
        return _public(projection), _interaction(interaction)

    def resolve_agent_review(
        self,
        target_id: str,
        session_id: str,
        review_id: str,
        accepted: bool,
        request_id: str,
        *,
        owner_scope: str,
    ) -> PublicAgentProjection:
        return _public(self._host().resolve_review(
            target_id, session_id, review_id, accepted, request_id,
            owner_scope=owner_scope,
        ))

    def agent_sessions(
        self,
        target_id: str,
        *,
        purpose: str | None = None,
    ) -> tuple[AgentSessionProjection, ...]:
        parsed = SessionPurpose(purpose) if purpose is not None else None
        return tuple(
            _agent_session(value)
            for value in self.store.sessions_for_target(target_id, purpose=parsed)
        )

    def session_interactions(self, session_id: str) -> tuple[InteractionProjection, ...]:
        return tuple(
            _interaction(value)
            for value in self.store.session_interactions(session_id)
        )

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

    def _host(self) -> AgentHostService:
        return AgentHostService(self.store, self.runtime)

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
    target = getattr(value, "target_id", value.channel_id)
    mode = getattr(value, "mode", DeploymentMode.DELIVERY)
    return DeploymentProjection(
        value.deployment_id,
        value.channel_id if mode is DeploymentMode.DELIVERY else None,
        value.bundle.bundle_id,
        value.bundle.content_hash,
        value.status.value,
        value.failure_code,
        value.failure_message,
        target,
        mode.value,
        getattr(value, "request_key", None),
    )


def _target(value: Any) -> DeploymentTargetProjection:
    return DeploymentTargetProjection(
        value.target_id,
        value.mode.value,
        value.owner_scope,
        value.channel_id,
        value.name,
    )


def _agent_session(value: Any) -> AgentSessionProjection:
    return AgentSessionProjection(
        value.session_id,
        value.target_id,
        value.activation_id,
        value.deployment_id,
        value.mode.value,
        value.purpose.value,
        value.created_at,
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
