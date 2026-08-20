from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from corpus.features.deployment.domain import DeploymentRecord, DeploymentTargetRecord
from corpus.features.sandbox.deployment_service import SandboxDeploymentService


class Builds:
    def __init__(self, owner_id, agent_id, build) -> None:
        self.owner_id, self.agent_id, self.build = owner_id, agent_id, build

    async def require_immutable_built(self, owner_id, agent_id, build_id):
        assert (owner_id, agent_id, build_id) == (
            self.owner_id, self.agent_id, self.build.id,
        )
        return self.build


class Repository:
    def __init__(self, owner_id, agent_id, active_deployment_id=None) -> None:
        self.owner_id, self.agent_id = owner_id, agent_id
        self.target = DeploymentTargetRecord(
            uuid.uuid4(), owner_id, agent_id, "sandbox", None,
            active_deployment_id, datetime.now(UTC),
        )
        self.records: dict[uuid.UUID, DeploymentRecord] = {}

    async def ensure_sandbox_target(self, owner_id, agent_id):
        assert (owner_id, agent_id) == (self.owner_id, self.agent_id)
        return self.target

    async def reserve_sandbox(
        self, owner_id, agent_id, *, target_id, build_id, bundle_hash,
        request_key, retry_of_deployment_id,
    ):
        assert (owner_id, agent_id, target_id) == (
            self.owner_id, self.agent_id, self.target.id,
        )
        now = datetime.now(UTC)
        record = DeploymentRecord(
            id=uuid.uuid4(), organization_id=owner_id, agent_id=agent_id,
            channel_id=None, build_id=build_id, eligibility_id=None,
            runtime_deployment_id=None, status="queued", bundle_hash=bundle_hash,
            failure_code=None, failure_message=None, created_at=now, updated_at=now,
            retry_of_deployment_id=retry_of_deployment_id, target_id=target_id,
            mode="sandbox", request_key=request_key,
        )
        self.records[record.id] = record
        return record

    async def mark_running_inline(self, owner_id, deployment_id):
        assert owner_id == self.owner_id
        record = replace(
            self.records[deployment_id], status="running", updated_at=datetime.now(UTC)
        )
        self.records[deployment_id] = record
        return record

    async def complete(
        self, owner_id, deployment_id, *, runtime_deployment_id, status,
        failure_code, failure_message,
    ):
        assert owner_id == self.owner_id
        record = replace(
            self.records[deployment_id], runtime_deployment_id=runtime_deployment_id,
            status=status, failure_code=failure_code, failure_message=failure_message,
            updated_at=datetime.now(UTC),
        )
        self.records[deployment_id] = record
        if status == "ready":
            self.target = replace(self.target, active_deployment_id=deployment_id)
        return record


class Delivery:
    def __init__(self, *, failure: Exception | None = None) -> None:
        self.failure = failure
        self.owner_scope = None
        self.spec = None

    def ensure_sandbox_target(self, *, target_id, owner_scope, name):
        self.owner_scope = owner_scope
        return SimpleNamespace(target_id=target_id, name=name)

    def request_sandbox_deployment(self, target_id, spec, *, request_key):
        self.spec = spec
        if self.failure is not None:
            raise self.failure
        return SimpleNamespace(
            deployment_id=f"runtime-{spec.bundle_id}", status="ready",
            failure_code=None, failure_message=None,
        )

    def agent_sessions(self, target_id, *, purpose):
        return []


class Bindings:
    def __init__(self) -> None:
        self.bound = None

    def bind(self, build) -> None:
        self.bound = build


def build_record(build_id):
    return SimpleNamespace(
        id=build_id, agent_version=4, runtime_build_hash="b" * 64,
        model="pinned-model", navgraph_hash="n" * 64,
        compiled_navgraph={"nodes": [{"id": "agent.home"}]},
        frontend_contract={"surfaces": ["catalog"]},
    )


@pytest.mark.asyncio
async def test_sandbox_deploys_ready_build_without_evaluation_eligibility() -> None:
    owner_id, agent_id, build_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    build = build_record(build_id)
    repository = Repository(owner_id, agent_id)
    delivery, bindings = Delivery(), Bindings()
    service = SandboxDeploymentService(
        repository, Builds(owner_id, agent_id, build), delivery, bindings,
    )

    result = await service.deploy(
        owner_id, agent_id, build_id=build_id, request_key="explicit-deploy",
    )

    assert result.status == "ready"
    assert result.mode == "sandbox"
    assert result.runtime_deployment_id == f"runtime-{result.id}"
    assert repository.target.active_deployment_id == result.id
    assert result.request_key == "explicit-deploy"
    assert delivery.owner_scope == str(owner_id)
    assert delivery.spec.runtime_config["evaluation_eligibility_required"] is False
    assert bindings.bound is build


@pytest.mark.asyncio
async def test_failed_replacement_preserves_previous_active_deployment() -> None:
    owner_id, agent_id, build_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    previous_id = uuid.uuid4()
    repository = Repository(owner_id, agent_id, active_deployment_id=previous_id)
    service = SandboxDeploymentService(
        repository, Builds(owner_id, agent_id, build_record(build_id)),
        Delivery(failure=RuntimeError("provider unavailable")), Bindings(),
    )

    result = await service.deploy(
        owner_id, agent_id, build_id=build_id, request_key="replacement",
    )

    assert result.status == "failed"
    assert result.failure_code == "RuntimeError"
    assert repository.target.active_deployment_id == previous_id


@pytest.mark.asyncio
async def test_listing_empty_playground_history_after_first_deployment() -> None:
    owner_id, agent_id, build_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    repository = Repository(owner_id, agent_id)
    service = SandboxDeploymentService(
        repository, Builds(owner_id, agent_id, build_record(build_id)),
        Delivery(), Bindings(),
    )

    sessions = await service._sessions(
        owner_id, agent_id, repository.target.id, purpose="playground"
    )

    assert sessions == ()
