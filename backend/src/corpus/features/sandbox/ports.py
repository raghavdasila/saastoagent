from __future__ import annotations

import uuid
from typing import Protocol

from corpus.features.builder.domain import BuilderRecord

from .domain import RuntimeSandboxRun, SandboxRecord


class SandboxUnavailable(RuntimeError):
    pass


class SandboxRunFailed(SandboxUnavailable):
    """A Sandbox attempt failed after its durable run identity was created."""

    def __init__(self, message: str, *, run_id: uuid.UUID) -> None:
        super().__init__(message)
        self.run_id = run_id


class SandboxConflict(RuntimeError):
    pass


class SandboxRuntimeGateway(Protocol):
    async def start(self, *, organization_id: uuid.UUID, session_id: str, run_id: str, build: BuilderRecord, message: str) -> RuntimeSandboxRun: ...
    async def resume(self, *, organization_id: uuid.UUID, record: SandboxRecord, build: BuilderRecord, message: str, selected_operation_id: str | None, answers: dict[str, str]) -> RuntimeSandboxRun: ...
    async def resolve_review(self, *, organization_id: uuid.UUID, record: SandboxRecord, build: BuilderRecord, review_id: str, accepted: bool, request_id: str) -> RuntimeSandboxRun: ...


class SandboxRepository(Protocol):
    async def begin(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build: BuilderRecord, message: str) -> SandboxRecord: ...
    async def complete(self, organization_id: uuid.UUID, record_id: uuid.UUID, result: RuntimeSandboxRun) -> SandboxRecord: ...
    async def begin_resume(self, organization_id: uuid.UUID, agent_id: uuid.UUID, record_id: uuid.UUID) -> SandboxRecord: ...
    async def fail(self, organization_id: uuid.UUID, record_id: uuid.UUID, *, code: str) -> SandboxRecord: ...
    async def list(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> tuple[SandboxRecord, ...]: ...
