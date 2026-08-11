from __future__ import annotations

import uuid
import json
from datetime import UTC, datetime

import pytest
import asyncio
from types import SimpleNamespace
from agent_delivery_runtime.domain import DeployableAgentBundle, DeliveryError
from agent_delivery_runtime.ports import RuntimeProjection, RuntimeReadiness

from corpus.app.delivery_runtime_store import CorpusLocalDeliveryStore
from corpus.app.delivery_runtime_adapters import CorpusDeployedAgentRuntimePort
from corpus.app.agent_runtime_adapters import CorpusExecutionBindingRegistry
from corpus.features.builder.domain import BuilderRecord
from corpus.features.channels.domain import ChannelRecord
from corpus.features.channels.service import ChannelService
from corpus.features.channels.http import _public_agent, _require_public_channel
from corpus.features.channels.declarations import SET_CHANNEL_ENABLED
from corpus.features.channels.policies import FEATURE_PROMPT
from corpus.features.deployment.declarations import DEPLOY_AGENT
from corpus.features.deployment.domain import DeploymentRecord, EligibleBuild
from corpus.features.deployment.service import DeploymentService
from corpus.integrations.agent_delivery import NeutralAgentDeliveryAdapter
from corpus.integrations.agent_execution import SandboxEventProjection, SandboxRunProjection


def test_publishing_and_channel_availability_have_distinct_agent_contracts() -> None:
    assert "does not select, activate, or publish" in SET_CHANNEL_ENABLED.description
    assert (
        "publish one exact eligible immutable agent build"
        in DEPLOY_AGENT.description.lower()
    )
    assert "never satisfies a request to publish" in FEATURE_PROMPT.instruction


class Runtime:
    def verify(self, bundle):
        return RuntimeReadiness(True, "test", "pinned", {"build_hash": bundle.content_hash})
    def create_session(self, _bundle): return "runtime-session"
    def projection(self, _bundle, _session): return RuntimeProjection(0, (), (), ())
    def invoke(self, _bundle, _session, _text, _request):
        return RuntimeProjection(1, ({"role": "assistant", "content": "real result"},), (), ())


def test_public_projection_keeps_owner_runtime_diagnostics_private() -> None:
    projection = SimpleNamespace(
        revision=4,
        messages=({"role": "assistant", "content": "Which operation should I use?"},),
        surfaces=(
            {
                "component": "agent_runtime.clarification",
                "props": {
                    "state": "needs_operation_choice",
                    "candidate_operation_ids": ["GetProductTagsId", "GetProductTypesId"],
                },
            },
            {
                "component": "agent_runtime.toolrouter_status",
                "props": {"state": "waiting", "last_resolution": "operation_choice_required"},
            },
        ),
        suggested_actions=({"action_id": "catalog", "label": "Read catalog"},),
    )

    public = _public_agent(projection)

    assert public == {
        "revision": 4,
        "messages": projection.messages,
        "awaiting_clarification": True,
    }
    serialized = json.dumps(public)
    assert "agent_runtime" not in serialized
    assert "ToolRouter" not in serialized
    assert "GetProductTypesId" not in serialized


class Agents:
    async def get(self, *_): return object()


class Channels:
    def __init__(self, owner, agent):
        self.owner, self.agent, self.values = owner, agent, {}
    async def reserve(self, owner, agent, *, name, slug):
        now = datetime.now(UTC)
        value = ChannelRecord(uuid.uuid4(), owner, agent, None, name, slug, "creating", False, None, None, None, now, now)
        self.values[value.id] = value
        return value
    async def complete(self, owner, channel_id, *, runtime_channel_id):
        old = self.values[channel_id]
        value = ChannelRecord(old.id, owner, old.agent_id, runtime_channel_id, old.name, old.slug, "ready", True, None, None, None, old.created_at, datetime.now(UTC))
        self.values[channel_id] = value
        return value
    async def fail(self, *_args, **_kwargs): raise AssertionError("unexpected channel failure")
    async def get(self, owner, agent, channel_id):
        value = self.values[channel_id]
        assert value.organization_id == owner and value.agent_id == agent
        return value
    async def set_active(self, owner, channel_id, deployment_id):
        old = self.values[channel_id]
        value = ChannelRecord(old.id, owner, old.agent_id, old.runtime_channel_id, old.name, old.slug, old.status, old.enabled, deployment_id, None, None, old.created_at, datetime.now(UTC))
        self.values[channel_id] = value
        return value
    async def set_enabled(self, owner, agent, channel_id, *, enabled):
        old = await self.get(owner, agent, channel_id)
        value = ChannelRecord(old.id, owner, old.agent_id, old.runtime_channel_id, old.name, old.slug, old.status, enabled, old.active_deployment_id, None, None, old.created_at, datetime.now(UTC))
        self.values[channel_id] = value
        return value
    async def list(self, *_): return tuple(self.values.values())


class Builds:
    def __init__(self, value): self.value = value
    async def require_running(self, owner, agent, build_id):
        assert (owner, agent, build_id) == (self.value.organization_id, self.value.agent_id, self.value.id)
        return self.value
    async def require_immutable_built(self, owner, agent, build_id):
        assert (owner, agent, build_id) == (self.value.organization_id, self.value.agent_id, self.value.id)
        return self.value


class Eligibility:
    def __init__(self, build): self.value = EligibleBuild(uuid.uuid4(), build.runtime_build_hash, "e" * 64)
    async def require_eligible(self, *_): return self.value


class Deployments:
    def __init__(self): self.values = {}
    async def reserve(self, owner, agent, **values):
        now = datetime.now(UTC)
        record = DeploymentRecord(uuid.uuid4(), owner, agent, values["channel_id"], values["build_id"], values["eligibility_id"], None, "verifying", values["bundle_hash"], None, None, now, now)
        self.values[record.id] = record
        return record
    async def complete(self, owner, deployment_id, **values):
        old = self.values[deployment_id]
        record = DeploymentRecord(old.id, owner, old.agent_id, old.channel_id, old.build_id, old.eligibility_id, values["runtime_deployment_id"], values["status"], old.bundle_hash, values.get("failure_code"), values.get("failure_message"), old.created_at, datetime.now(UTC))
        self.values[record.id] = record
        return record
    async def get(self, owner, agent, deployment_id):
        value = self.values[deployment_id]
        assert value.organization_id == owner and value.agent_id == agent
        return value
    async def list(self, *_): return tuple(self.values.values())


class Bindings:
    def __init__(self): self.values = {}
    def bind(self, build): self.values[build.runtime_build_hash] = build
    def get(self, build_hash): return self.values[build_hash]


@pytest.mark.asyncio
async def test_channel_deploy_public_session_and_restart_binding_are_exact(tmp_path):
    owner, agent = uuid.uuid4(), uuid.uuid4()
    now = datetime.now(UTC)
    build = BuilderRecord(
        uuid.uuid4(), owner, agent, uuid.uuid4(), uuid.uuid4(), 4, "ready",
        "running", "b" * 64, "model", "digest", ({"source_id": "source-1"},),
        ("GetProductTypes",), "n" * 64, {"nodes": []}, {"nodes": {}}, None, None, now, now,
    )
    delivery = NeutralAgentDeliveryAdapter(CorpusLocalDeliveryStore(tmp_path / "delivery.sqlite3"), Runtime())
    channel_repository = Channels(owner, agent)
    channels = ChannelService(channel_repository, delivery, Agents())
    bindings = Bindings()
    deployments = DeploymentService(
        Deployments(), channels, Builds(build), Eligibility(build), delivery, bindings
    )

    channel = await channels.create(owner, agent, name="Store Agent", slug="store-agent")
    deployment = await deployments.deploy(owner, agent, channel_id=channel.id, build_id=build.id)
    active = channel_repository.values[channel.id]

    assert deployment.status == "ready"
    assert active.active_deployment_id == deployment.id
    assert bindings.get(build.runtime_build_hash).id == build.id
    bindings.values.clear()
    await deployments.prepare_public(active)
    assert bindings.get(build.runtime_build_hash).id == build.id
    session, projection = delivery.create_public_session("store-agent")
    assert session.deployment_id == deployment.runtime_deployment_id
    assert projection.messages == ()

    disabled = await channels.set_enabled(owner, agent, channel.id, enabled=False)

    assert disabled.enabled is False
    assert channel_repository.values[channel.id].enabled is False
    with pytest.raises(Exception, match="This public Agent is unavailable"):
        _require_public_channel(disabled)
    with pytest.raises(DeliveryError) as projection_error:
        delivery.public_projection("store-agent", session.session_id)
    assert projection_error.value.code == "channel_disabled"
    with pytest.raises(DeliveryError) as invoke_error:
        delivery.invoke("store-agent", session.session_id, "still there?", "after-disable")
    assert invoke_error.value.code == "channel_disabled"


class Execution:
    def __init__(self, build_hash): self.build_hash = build_hash
    def load_build(self, build_hash):
        assert build_hash == self.build_hash
        return SimpleNamespace(content_hash=build_hash, operation_ids=("GetProductTypes",))


class RouteDeckProjection:
    async def projection(self, _build, _session_id, _tenant_id):
        return {
            "current": {"node_id": "agent_runtime.home"},
            "legal_operations": [],
            "suggested_actions": [],
            "surfaces": {
                "active": {"surface_id": "agent_runtime.home", "component": "agent_runtime.home", "props": {}},
                "detail": [{"surface_id": "agent_runtime.clarification", "component": "agent_runtime.clarification", "props": {}}],
                "review": [],
                "status": [{"surface_id": "agent_runtime.toolrouter_status", "component": "agent_runtime.toolrouter_status", "props": {}}],
                "error": [],
            },
        }


@pytest.mark.asyncio
async def test_deployed_runtime_restores_exact_durable_build_binding_after_restart():
    owner, agent, build_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    now = datetime.now(UTC)
    build = BuilderRecord(
        build_id, owner, agent, uuid.uuid4(), uuid.uuid4(), 1, "ready",
        "stopped", "c" * 64, "model", "digest", ({"source_id": "source-1"},),
        ("GetProductTypes",), "n" * 64, {"nodes": []}, {"nodes": {}}, None, None, now, now,
    )
    bindings = Bindings()
    port = CorpusDeployedAgentRuntimePort(Execution(build.runtime_build_hash), bindings, Builds(build), RouteDeckProjection())
    bundle = DeployableAgentBundle(
        "bundle", "Agent", "1", build.runtime_build_hash,
        "r" * 64, "s" * 64, "e" * 64, "corpus-agent-execution-v1",
        {"runtime_build_hash": build.runtime_build_hash, "organization_id": str(owner), "agent_id": str(agent), "build_id": str(build_id)},
    )

    readiness = await asyncio.to_thread(port.verify, bundle)

    assert readiness.ready is True
    assert bindings.get(build.runtime_build_hash).id == build_id


class ClarifyingExecution:
    def __init__(self, build_hash):
        self.build_hash = build_hash
        self.current = None
        self.commands = []
        self.messages = []

    def load_build(self, build_hash):
        assert build_hash == self.build_hash
        return SimpleNamespace(
            content_hash=build_hash,
            operation_ids=("GetProductTagsId", "GetProductTypesId"),
        )

    def waiting_run(self, tenant_id, session_id, build_hash):
        assert build_hash == self.build_hash
        return self.current

    def session_messages(self, tenant_id, session_id, build_hash):
        assert build_hash == self.build_hash
        return tuple(self.messages)

    async def run(self, spec):
        self.commands.append(spec)
        self.messages.append({"role": "user", "content": spec.message})
        if spec.command == "start":
            self.current = _waiting_projection(
                self.build_hash,
                "runtime-run",
                "Which operation should I use: GetProductTagsId or GetProductTypesId?",
                ("GetProductTagsId", "GetProductTypesId"),
                (),
            )
            self.messages.append({"role": "assistant", "content": self.current.final_response})
            return self.current
        assert spec.command == "resume"
        assert spec.run_id == "runtime-run"
        if len(self.commands) == 2:
            assert spec.selected_operation_id == "GetProductTypesId"
            assert spec.provided_inputs == {
                "__selected_operation_id": "GetProductTypesId"
            }
            self.current = _waiting_projection(
                self.build_hash,
                "runtime-run",
                "What value should I use for id?",
                ("GetProductTypesId",),
                ("id",),
            )
            self.messages.append({"role": "assistant", "content": self.current.final_response})
            return self.current
        assert spec.selected_operation_id == "GetProductTypesId"
        assert spec.provided_inputs == {
            "__selected_operation_id": "GetProductTypesId",
            "id": "pt_exact",
            "path": {"id": "pt_exact"},
        }
        self.current = None
        completed = SandboxRunProjection(
            "runtime-run",
            self.build_hash,
            "succeeded",
            None,
            "Product type loaded.",
            1,
            (),
        )
        self.messages.append({"role": "assistant", "content": completed.final_response})
        return completed


def _waiting_projection(build_hash, run_id, question, candidates, missing):
    return SandboxRunProjection(
        run_id,
        build_hash,
        "waiting",
        "router",
        question,
        0,
        (
            SandboxEventProjection(
                1,
                "router.decision",
                datetime.now(UTC).isoformat(),
                {
                    "candidates": tuple(
                        {"operation_id": item, "score": 1.0}
                        for item in candidates
                    ),
                    "missing_params": missing,
                    "resolution": (
                        "operation_choice_required" if len(candidates) > 1
                        else "input_required"
                    ),
                },
            ),
        ),
    )


@pytest.mark.asyncio
async def test_deployed_runtime_resumes_one_waiting_run_without_lookup_or_internal_copy(tmp_path):
    owner, agent, build_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    document_path = tmp_path / "openapi.json"
    document_path.write_text(
        json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "Store", "version": "1"},
                "paths": {
                    "/store/product-types/{id}": {
                        "get": {
                            "operationId": "GetProductTypesId",
                            "parameters": [
                                {
                                    "name": "id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {"type": "string"},
                                }
                            ],
                            "responses": {"200": {"description": "ok"}},
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    now = datetime.now(UTC)
    build = BuilderRecord(
        build_id,
        owner,
        agent,
        uuid.uuid4(),
        uuid.uuid4(),
        1,
        "ready",
        "stopped",
        "d" * 64,
        "model",
        "digest",
        (
            {
                "source_id": "source-1",
                "document_path": str(document_path),
                "included_operation_ids": (
                    "GetProductTagsId",
                    "GetProductTypesId",
                ),
            },
        ),
        ("GetProductTagsId", "GetProductTypesId"),
        "n" * 64,
        {"nodes": []},
        {"nodes": {}},
        None,
        None,
        now,
        now,
    )
    execution = ClarifyingExecution(build.runtime_build_hash)
    port = CorpusDeployedAgentRuntimePort(
        execution, CorpusExecutionBindingRegistry(), Builds(build), RouteDeckProjection()
    )
    bundle = DeployableAgentBundle(
        "bundle",
        "Agent",
        "1",
        build.runtime_build_hash,
        "r" * 64,
        "s" * 64,
        "e" * 64,
        "corpus-agent-execution-v1",
        {
            "runtime_build_hash": build.runtime_build_hash,
            "organization_id": str(owner),
            "agent_id": str(agent),
            "build_id": str(build_id),
        },
    )

    first = await asyncio.to_thread(
        port.invoke, bundle, "public-session", "get product taxonomy", "request-1"
    )
    second = await asyncio.to_thread(
        port.invoke, bundle, "public-session", "Use product types.", "request-2"
    )
    invalid = await asyncio.to_thread(
        port.invoke, bundle, "public-session", "x-api-key=credential-canary", "request-3"
    )
    final = await asyncio.to_thread(
        port.invoke, bundle, "public-session", "pt_exact", "request-4"
    )

    assert first.messages == (
        {"role": "user", "content": "get product taxonomy"},
        {"role": "assistant", "content": "Which operation should I use: GetProductTagsId or GetProductTypesId?"},
    )
    assert any(item["component"] == "agent_runtime.clarification" for item in first.surfaces)
    clarification = next(item for item in first.surfaces if item["component"] == "agent_runtime.clarification")
    assert clarification["props"]["state"] == "needs_operation_choice"
    assert second.messages[-2:] == (
        {"role": "user", "content": "Use product types."},
        {"role": "assistant", "content": "What value should I use for id?"},
    )
    assert invalid.messages == second.messages
    assert final.messages[-2:] == (
        {"role": "user", "content": "pt_exact"},
        {"role": "assistant", "content": "Product type loaded."},
    )
    assert len(execution.commands) == 3
    public_copy = str((first, second, invalid, final))
    assert "ASK_DISAMBIGUATE" not in public_copy
    assert "credential-canary" not in public_copy
