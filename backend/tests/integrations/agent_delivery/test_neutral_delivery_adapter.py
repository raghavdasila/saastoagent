from __future__ import annotations

from pathlib import Path

from agent_delivery_runtime.ports import RuntimeProjection, RuntimeReadiness
from agent_delivery_runtime.store import DeliveryStore

from corpus.integrations.agent_delivery import (
    DeployableBundleSpec,
    NeutralAgentDeliveryAdapter,
)


class RuntimeProbe:
    def __init__(self) -> None:
        self.sessions = 0
        self.messages: dict[str, list[dict[str, str]]] = {}

    def verify(self, bundle):
        return RuntimeReadiness(True, "corpus", "model-v1", {"ready": True})

    def create_session(self, bundle):
        self.sessions += 1
        session_id = f"runtime-{self.sessions}"
        self.messages[session_id] = []
        return session_id

    def projection(self, bundle, runtime_session_id):
        return RuntimeProjection(
            len(self.messages[runtime_session_id]),
            tuple(self.messages[runtime_session_id]),
            (),
            (),
        )

    def invoke(self, bundle, runtime_session_id, text, request_id):
        self.messages[runtime_session_id].extend((
            {"role": "user", "content": text},
            {"role": "assistant", "content": f"Observed: {text}"},
        ))
        return self.projection(bundle, runtime_session_id)


def _bundle(version: str) -> DeployableBundleSpec:
    return DeployableBundleSpec(
        bundle_id=f"bundle-{version}",
        name="Store helper",
        version=version,
        content_hash=version * 64,
        routedeck_app_hash="a" * 64,
        surface_contract_hash="b" * 64,
        eligibility_hash="c" * 64,
        runtime_kind="corpus-neutral",
        runtime_config={"build_hash": "d" * 64},
    )


def test_neutral_delivery_adapter_pins_sessions_and_exports_operations(tmp_path: Path) -> None:
    adapter = NeutralAgentDeliveryAdapter(DeliveryStore(tmp_path / "delivery.db"), RuntimeProbe())
    channel = adapter.create_channel("Store helper", "store-helper")
    first = adapter.request_deployment(channel.channel_id, _bundle("1"))
    session, projection = adapter.create_public_session(channel.slug)
    second = adapter.request_deployment(channel.channel_id, _bundle("2"))

    assert first.status == "ready"
    assert second.status == "ready"
    assert session.deployment_id == first.deployment_id
    assert projection.messages == ()

    public, interaction = adapter.invoke(channel.slug, session.session_id, "List product types", "request-1")
    assert public.messages[-1]["content"] == "Observed: List product types"
    assert adapter.interaction(interaction.interaction_id) == interaction
    assert adapter.interactions() == (interaction,)
    candidate = adapter.evaluation_candidate(interaction.interaction_id)
    assert candidate.interaction_id == interaction.interaction_id
    assert candidate.deployment_id == first.deployment_id

    activation = adapter.rollback(channel.channel_id, first.deployment_id)
    assert activation.deployment_id == first.deployment_id
    assert activation.reason == "rollback"

    disabled = adapter.set_channel_enabled(channel.channel_id, False)
    assert disabled.enabled is False
