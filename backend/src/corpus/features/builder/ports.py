from __future__ import annotations

import uuid
from typing import Protocol

from .domain import BuilderInputSnapshot, BuilderRecord, RuntimeBuildArtifact


class BuilderUnavailable(RuntimeError):
    pass


class BuilderConflict(RuntimeError):
    pass


class BuilderInputGateway(Protocol):
    async def current_build_request_id(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> uuid.UUID: ...

    async def snapshot(self, organization_id: uuid.UUID, record: BuilderRecord) -> BuilderInputSnapshot: ...


class BuilderRuntimeGateway(Protocol):
    async def assemble(self, snapshot: BuilderInputSnapshot) -> RuntimeBuildArtifact: ...
    async def validate_immutable_build(self, runtime_build_hash: str) -> None: ...


class BuilderRepository(Protocol):
    async def begin(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_request_id: uuid.UUID) -> BuilderRecord: ...
    async def complete(self, organization_id: uuid.UUID, build_id: uuid.UUID, *, artifact: RuntimeBuildArtifact, source_bindings: tuple[dict[str, object], ...]) -> BuilderRecord: ...
    async def fail(self, organization_id: uuid.UUID, build_id: uuid.UUID, *, code: str, message: str) -> BuilderRecord: ...
    async def get_for_agent(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> tuple[BuilderRecord, ...]: ...
    async def get(self, organization_id: uuid.UUID, agent_id: uuid.UUID, build_id: uuid.UUID) -> BuilderRecord: ...
    async def set_runtime_lifecycle(self, organization_id: uuid.UUID, agent_id: uuid.UUID, build_id: uuid.UUID, *, lifecycle: str) -> BuilderRecord: ...
