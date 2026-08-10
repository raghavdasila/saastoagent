from __future__ import annotations

from typing import Any, Mapping, Protocol

from .contracts import CapabilityEnvelope, ExecutionRequest, OperationContract, TraceEvent


class OpenAPIDocumentProvider(Protocol):
    async def get_document(self, document_hash: str) -> Mapping[str, Any]: ...


class CredentialResolver(Protocol):
    async def resolve(self, credential_ref: str) -> Mapping[str, str]: ...


class ApprovalVerifier(Protocol):
    async def verify(
        self, envelope: CapabilityEnvelope, operation: OperationContract
    ) -> None: ...


class TraceSink(Protocol):
    async def emit(self, event: TraceEvent) -> None: ...


class OutcomeVerifier(Protocol):
    async def verify(
        self, request: ExecutionRequest, status_code: int, response_body: Any
    ) -> bool: ...

