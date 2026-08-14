from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Mapping
from urllib.parse import urlsplit

import httpx

from corpus.credentials import CredentialVaultPort
from corpus.shared.api_execution import SafeApiExecutionError, SafeApiExecutionTarget

from ._snapshot.contracts import (
    CapabilityEnvelope,
    ConnectionRevision,
    ExecutionInputs,
    ExecutionRequest,
    ExecutionResult,
    NetworkPolicy,
    OperationContract,
    ParameterContract,
    SafetyClass,
    TraceEvent,
    utc_now,
)
from ._snapshot.errors import ContractError, CredentialError
from ._snapshot.plugins import PluginRegistry
from ._snapshot.runtime import ApiExecutionRuntime


SAFE_API_OPERATIONS: Mapping[str, tuple[str, str]] = {
    "GetProductTypes": ("GET", "/store/product-types"),
    "GetProductTags": ("GET", "/store/product-tags"),
}


@dataclass(frozen=True)
class SafeApiExecutionOutcome:
    result: ExecutionResult
    traces: tuple[TraceEvent, ...]
    http_call_count: int


class SafeApiExecutionAdapter:
    """Execute one explicitly selected read through the unchanged snapshot."""

    def __init__(
        self,
        *,
        credentials: CredentialVaultPort,
        allowed_base_urls: tuple[str, ...],
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        normalized = tuple(_normalize_base_url(value) for value in allowed_base_urls)
        self._credentials = credentials
        self._allowed_base_urls = frozenset(normalized)
        self._transport = transport

    async def execute(self, target: SafeApiExecutionTarget) -> SafeApiExecutionOutcome:
        base_url = _normalize_base_url(target.base_url)
        if base_url not in self._allowed_base_urls:
            raise SafeApiExecutionError(
                "The selected API endpoint is not enabled for safe connection checks."
            )
        operation = _operation_contract(
            target.document,
            target.operation_id,
            authentication_method=target.authentication_method,
            credential_name=target.credential_name,
        )
        auth_plugin_id = _auth_plugin_id(
            target.authentication_method,
            target.credential_reference_id,
            target.credential_version,
        )
        trace = _TraceCollector()
        credential_resolver = _VaultCredentialResolver(
            vault=self._credentials,
            owner_id=target.owner_id,
            expected_id=target.credential_reference_id,
            expected_version=target.credential_version,
        )
        counting_transport = _CountingTransport(self._transport)
        connection = ConnectionRevision(
            connection_id=target.connection_profile_id,
            revision=1,
            tenant_id=str(target.owner_id),
            base_url=base_url,
            openapi_document_hash=target.document_hash,
            auth_plugin_id=auth_plugin_id,
            credential_ref=(
                str(target.credential_reference_id)
                if target.credential_reference_id is not None
                else None
            ),
            network_policy=NetworkPolicy(
                allow_http=urlsplit(base_url).scheme.lower() == "http",
                # A private destination is permitted only after its complete
                # normalized base URL matched the operator-owned allowlist.
                allow_private_networks=True,
            ),
        )
        envelope = CapabilityEnvelope(
            execution_id=target.execution_id,
            tenant_id=str(target.owner_id),
            connection_id=target.connection_profile_id,
            connection_revision=connection.revision,
            openapi_document_hash=target.document_hash,
            operation_id=target.operation_id,
            expires_at=utc_now() + timedelta(minutes=2),
        )
        runtime = ApiExecutionRuntime(
            document_provider=_ExactDocumentProvider(
                expected_hash=target.document_hash,
                document=target.document,
            ),
            approval_verifier=_ReadOnlyVerifier(),
            trace_sink=trace,
            credential_resolver=credential_resolver,
            plugins=_plugins(),
            transport=counting_transport,
        )
        try:
            result = await runtime.execute(
                ExecutionRequest(
                    envelope=envelope,
                    connection=connection,
                    operation=operation,
                    inputs=ExecutionInputs(),
                )
            )
        finally:
            await runtime.aclose()
        if counting_transport.call_count > 1:
            raise SafeApiExecutionError("A safe API check attempted more than one HTTP call.")
        return SafeApiExecutionOutcome(
            result=result,
            traces=tuple(trace.events),
            http_call_count=counting_transport.call_count,
        )

    async def execute_redacted(self, target: SafeApiExecutionTarget):
        from .redaction import redact_execution

        return redact_execution(await self.execute(target))


class _ExactDocumentProvider:
    def __init__(self, *, expected_hash: str, document: Mapping[str, Any]) -> None:
        self._expected_hash = expected_hash
        self._document = document

    async def get_document(self, document_hash: str) -> Mapping[str, Any]:
        if document_hash != self._expected_hash:
            raise ContractError(
                "openapi_document_mismatch",
                "The selected API definition is unavailable.",
            )
        return self._document


class _ReadOnlyVerifier:
    async def verify(
        self, envelope: CapabilityEnvelope, operation: OperationContract
    ) -> None:
        if operation.safety_class is not SafetyClass.READ:
            raise ContractError(
                "safe_check_not_read_only",
                "Only a read operation can be used for a connection check.",
            )
        if envelope.operation_id not in SAFE_API_OPERATIONS:
            raise ContractError(
                "safe_check_operation_unavailable",
                "The selected safe API operation is unavailable.",
            )


@dataclass(frozen=True)
class _VaultCredentialResolver:
    vault: CredentialVaultPort
    owner_id: uuid.UUID
    expected_id: uuid.UUID | None
    expected_version: int | None

    async def resolve(self, credential_ref: str) -> Mapping[str, str]:
        if self.expected_id is None or credential_ref != str(self.expected_id):
            raise CredentialError(
                "credential_reference_mismatch",
                "The selected API credential is unavailable.",
            )
        try:
            resolved = await self.vault.resolve(
                owner_id=self.owner_id,
                credential_id=self.expected_id,
            )
        except Exception as error:
            raise CredentialError(
                "credential_unavailable",
                "The selected API credential is unavailable.",
            ) from error
        reference = resolved.reference
        if (
            reference.id != self.expected_id
            or reference.owner_id != self.owner_id
            or reference.version != self.expected_version
        ):
            raise CredentialError(
                "credential_version_mismatch",
                "The selected API credential changed before the check began.",
            )
        return dict(resolved.values)


class _TraceCollector:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    async def emit(self, event: TraceEvent) -> None:
        self.events.append(event)


class _CountingTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport: httpx.AsyncBaseTransport | None) -> None:
        self._transport = transport or httpx.AsyncHTTPTransport()
        self.call_count = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.call_count += 1
        if self.call_count > 1:
            raise httpx.RequestError(
                "A safe API check cannot issue more than one request.",
                request=request,
            )
        return await self._transport.handle_async_request(request)

    async def aclose(self) -> None:
        await self._transport.aclose()


class _BearerTokenPlugin:
    id = "bearer"

    def apply(self, headers, query, cookies, credential) -> None:
        token = "" if credential is None else credential.get("token", "")
        if not token:
            raise CredentialError(
                "credential_invalid",
                "The API credential configuration is invalid.",
            )
        headers["Authorization"] = f"Bearer {token}"


def _plugins() -> PluginRegistry:
    from ._snapshot.plugins import ApiKeyHeaderPlugin, NoAuthPlugin

    return PluginRegistry(auth=(NoAuthPlugin(), ApiKeyHeaderPlugin(), _BearerTokenPlugin()))


def _auth_plugin_id(
    method: str,
    credential_id: uuid.UUID | None,
    credential_version: int | None,
) -> str:
    if method == "none":
        if credential_id is not None or credential_version is not None:
            raise SafeApiExecutionError(
                "An unauthenticated API profile cannot reference a credential."
            )
        return "none"
    if credential_id is None or credential_version is None:
        raise SafeApiExecutionError("The selected API credential is unavailable.")
    if method == "api_key":
        return "api_key_header"
    if method == "bearer":
        return "bearer"
    raise SafeApiExecutionError("The selected API authentication method is unsupported.")


def _operation_contract(
    document: Mapping[str, Any],
    operation_id: str,
    *,
    authentication_method: str,
    credential_name: str | None,
) -> OperationContract:
    expected = SAFE_API_OPERATIONS.get(operation_id)
    if expected is None:
        raise SafeApiExecutionError("The selected safe API operation is unavailable.")
    expected_method, path_template = expected
    try:
        operation = document["paths"][path_template][expected_method.lower()]
    except (KeyError, TypeError) as error:
        raise SafeApiExecutionError(
            "The selected safe API operation is missing from the approved contract."
        ) from error
    if operation.get("operationId") != operation_id:
        raise SafeApiExecutionError(
            "The selected safe API operation does not match the approved contract."
        )
    parameters: list[ParameterContract] = []
    for value in operation.get("parameters", ()):
        if not isinstance(value, Mapping) or "$ref" in value:
            continue
        location = str(value.get("in", ""))
        name = str(value.get("name", ""))
        if location in {"path", "query", "header", "cookie"} and name:
            managed_by_auth = (
                authentication_method == "api_key"
                and location == "header"
                and credential_name is not None
                and name.casefold() == credential_name.casefold()
            )
            parameters.append(
                ParameterContract(
                    name=name,
                    location=location,
                    required=bool(value.get("required", False)),
                    managed_by_auth=managed_by_auth,
                )
            )
    response_media_types = tuple(
        sorted(
            {
                media_type
                for response in operation.get("responses", {}).values()
                if isinstance(response, Mapping)
                for media_type in response.get("content", {})
            }
        )
    ) or ("application/json",)
    return OperationContract(
        operation_id=operation_id,
        method=expected_method,
        path_template=path_template,
        safety_class=SafetyClass.READ,
        parameters=tuple(parameters),
        response_media_types=response_media_types,
        idempotent=True,
    )


def _normalize_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlsplit(normalized)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Safe API-check base URLs must be absolute HTTP(S) URLs.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Safe API-check base URLs cannot contain credentials or query data.")
    return normalized


__all__ = [
    "SAFE_API_OPERATIONS",
    "SafeApiExecutionAdapter",
    "SafeApiExecutionError",
    "SafeApiExecutionOutcome",
    "SafeApiExecutionTarget",
]
