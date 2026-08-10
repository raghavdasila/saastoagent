from __future__ import annotations

import asyncio
import contextvars
import threading
import uuid
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping, Protocol

from agent_execution_runtime import ApiCallResult
from routedeck_core.app import FeatureBindings, bind_app
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import (
    DeliveryPhase,
    OperationDisposition,
    OperationOutcome,
    OperationRequest,
    OperationResult,
    OperationSource,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.session import PrivateSessionState
from routedeck_core.ports import SessionStoreError, SessionStoreErrorCode
from routedeck_core.ports.executor import ExecutionContext
from routedeck_core.state.session import create_session
from routedeck_sqlalchemy import open_sqlalchemy_routedeck_runtime

from corpus.features.builder.domain import BuilderRecord
from corpus.features.builder.navgraph import load_agent_navgraph
from corpus.features.builder.ports import BuilderConflict, BuilderUnavailable


_SESSION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar("corpus_agent_routedeck_session", default=None)


class DirectAgentApiExecutor(Protocol):
    async def execute_direct(
        self,
        *,
        build: BuilderRecord,
        tenant_id: str,
        operation_id: str,
        inputs: Mapping[str, Any],
        execution_id: str,
        approved_write: bool,
    ) -> ApiCallResult: ...


@dataclass(frozen=True)
class AgentRouteDeckResult:
    operation: OperationResult
    api_result: ApiCallResult | None
    projection: dict[str, object]


@contextmanager
def agent_route_session(session_id: str):
    if not session_id:
        raise BuilderUnavailable("The Agent RouteDeck session identity is required.")
    token = _SESSION_ID.set(session_id)
    try:
        yield
    finally:
        _SESSION_ID.reset(token)


def current_agent_route_session() -> str:
    value = _SESSION_ID.get()
    if value is None:
        raise BuilderUnavailable("The Agent execution is not bound to an isolated RouteDeck session.")
    return value


class AgentRouteDeckSupervisor:
    def __init__(self, root: Path, encryption_key: str, direct: DirectAgentApiExecutor) -> None:
        self.root = root.resolve()
        self.encryption_key = encryption_key
        self.direct = direct
        self._runtime_locks_guard = threading.Lock()
        self._runtime_locks: dict[str, threading.Lock] = {}

    async def execute(
        self,
        *,
        build: BuilderRecord,
        tenant_id: str,
        operation_id: str,
        inputs: Mapping[str, Any],
        execution_id: str,
    ) -> AgentRouteDeckResult:
        session_id = current_agent_route_session()
        async with self._runtime_lock(build):
            runtime, captured = await self._open(build, tenant_id)
            try:
                snapshot = await self._load_or_create(runtime, session_id)
                operation = _operation_for_source_id(runtime.services.app.app, operation_id)
                result = await runtime.services.runner.run(OperationRequest(
                    session_id=session_id,
                    request_id=execution_id,
                    expected_session_version=snapshot.session_version,
                    operation_id=operation.id,
                    source=OperationSource.AGENT,
                    arguments=FrozenJsonObject(dict(inputs)),
                ))
                projection = await self._projection(runtime, session_id)
                return AgentRouteDeckResult(result, captured.pop(execution_id, None), projection)
            finally:
                await runtime.close()

    async def projection(self, build: BuilderRecord, session_id: str, tenant_id: str) -> dict[str, object]:
        async with self._runtime_lock(build):
            runtime, _captured = await self._open(build, tenant_id)
            try:
                await self._load_or_create(runtime, session_id)
                return await self._projection(runtime, session_id)
            finally:
                await runtime.close()

    async def accept(self, *, build: BuilderRecord, tenant_id: str, session_id: str, review_id: str, request_id: str) -> AgentRouteDeckResult:
        async with self._runtime_lock(build):
            runtime, captured = await self._open(build, tenant_id)
            try:
                snapshot = await self._load_or_create(runtime, session_id)
                result = await runtime.services.runner.accept_review(
                    review_id,
                    request_id=request_id,
                    expected_session_version=snapshot.session_version,
                    session_id=session_id,
                )
                projection = await self._projection(runtime, session_id)
                return AgentRouteDeckResult(result, captured.pop(request_id, None), projection)
            finally:
                await runtime.close()

    @asynccontextmanager
    async def _runtime_lock(self, build: BuilderRecord):
        if build.navgraph_hash is None:
            raise BuilderUnavailable("The selected build has no immutable RouteDeck NavGraph.")
        with self._runtime_locks_guard:
            lock = self._runtime_locks.setdefault(
                build.navgraph_hash, threading.Lock()
            )
        await asyncio.to_thread(lock.acquire)
        try:
            yield
        finally:
            lock.release()

    async def _open(self, build: BuilderRecord, tenant_id: str):
        if build.navgraph_hash is None or not build.compiled_navgraph:
            raise BuilderUnavailable("The selected build has no immutable RouteDeck NavGraph.")
        compiled = load_agent_navgraph(build.navgraph_hash, build.compiled_navgraph)
        captured: dict[str, ApiCallResult] = {}
        handlers = {
            operation.ref: _AgentToolHandler(
                build=build,
                tenant_id=tenant_id,
                source_operation_id=str(operation.public_metadata_value()["source_operation_id"]),
                write=operation.safety_class.value == "write_external",
                direct=self.direct,
                captured=captured,
            )
            for operation in compiled.operations.values()
        }
        self.root.mkdir(parents=True, exist_ok=True)
        database_path = self.root / f"{build.navgraph_hash}.sqlite3"
        runtime = await open_sqlalchemy_routedeck_runtime(
            compiled_app=compiled,
            application_factory=lambda _resources: bind_app(compiled, FeatureBindings(handlers=handlers, providers={}, guards={})),
            session_factory=lambda app, session_id: create_session(app=app, session_id=session_id, private_state=PrivateSessionState()),
            session_initializer=lambda _services, snapshot: snapshot,
            public_key_validator_factory=lambda _session: None,
            agent_driver_factory=None,
            database_url=f"sqlite+pysqlite:///{database_path.as_posix()}",
            encryption_key=self.encryption_key,
            instance_id=f"agent-{build.navgraph_hash[:16]}",
            review_ttl=timedelta(minutes=15),
            resume_capability_ttl=timedelta(hours=1),
            worker_count=1,
        )
        return runtime, captured

    async def _load_or_create(self, runtime, session_id: str):
        try:
            return await runtime.services.store.load(session_id)
        except SessionStoreError as error:
            if error.code not in {SessionStoreErrorCode.SESSION_NOT_FOUND, SessionStoreErrorCode.SESSION_EXPIRED}:
                raise
        return await runtime.provision_session(session_id=session_id, request_id=f"provision:{session_id}")

    async def _projection(self, runtime, session_id: str) -> dict[str, object]:
        snapshot = await runtime.services.store.load(session_id)
        return runtime.services.projector.project(snapshot.state).model_dump(mode="json")


@dataclass(frozen=True)
class _AgentToolHandler:
    build: BuilderRecord
    tenant_id: str
    source_operation_id: str
    write: bool
    direct: DirectAgentApiExecutor
    captured: dict[str, ApiCallResult]

    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        result = await self.direct.execute_direct(
            build=self.build,
            tenant_id=self.tenant_id,
            operation_id=self.source_operation_id,
            inputs=arguments,
            execution_id=context.request_id,
            approved_write=self.write,
        )
        self.captured[context.request_id] = result
        delivery = _delivery_phase(result)
        if result.status == "succeeded":
            return OperationOutcome(
                outcome="observed",
                delivery_phase=delivery,
                observation=FrozenJsonObject({
                    "operation_id": result.operation_id,
                    "status": result.status,
                    "http_status": result.http_status,
                    "outcome_verified": result.outcome_verified,
                }),
            )
        unknown = result.status == "outcome_unknown"
        return OperationOutcome(
            failure=RouteDeckFailure(
                kind=FailureKind.EXTERNAL_OUTCOME_UNKNOWN if unknown else FailureKind.BUSINESS,
                code=result.error_code or "agent_tool_failed",
                phase="agent_runtime",
                correlation_id=context.request_id,
                operation_id=None,
                request_id=context.request_id,
                public_message=result.public_message or "The Agent tool did not complete.",
                recovery_directive=(
                    "Do not retry automatically. Inspect the retained delivery state and prepare a new reviewed action."
                    if unknown else None
                ),
                safe_details=FailureSafeDetails(
                    http_status=result.http_status,
                    delivery_phase=delivery.value,
                ),
            ),
            delivery_phase=delivery,
        )


def _operation_for_source_id(app, operation_id: str):
    values = tuple(
        operation
        for operation in app.operations.values()
        if operation.public_metadata_value().get("source_operation_id") == operation_id
    )
    if len(values) != 1:
        raise BuilderConflict("The Agent tool does not resolve to one compiled RouteDeck operation.")
    return values[0]


def _delivery_phase(result: ApiCallResult) -> DeliveryPhase:
    if result.http_status is not None:
        return DeliveryPhase.RESPONSE_RECEIVED
    if result.status == "outcome_unknown":
        return DeliveryPhase.POSSIBLY_SENT
    return DeliveryPhase.NOT_SENT


__all__ = [
    "AgentRouteDeckResult",
    "AgentRouteDeckSupervisor",
    "agent_route_session",
    "current_agent_route_session",
]
