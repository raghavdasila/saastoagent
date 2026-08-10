from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Mapping

import httpx

from .compiler import PreparedRequest, compile_request
from .contracts import (
    CONTRACT_VERSION,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    SafetyClass,
    TraceEvent,
    utc_now,
)
from .errors import (
    ApiExecutionError,
    ContractError,
    CredentialError,
    ResponseTooLargeError,
)
from .plugins import PluginRegistry
from .ports import (
    ApprovalVerifier,
    CredentialResolver,
    OpenAPIDocumentProvider,
    OutcomeVerifier,
    TraceSink,
)
from .security import enforce_network_policy
from .validation import OpenAPIValidator


class ApiExecutionRuntime:
    def __init__(
        self,
        *,
        document_provider: OpenAPIDocumentProvider,
        approval_verifier: ApprovalVerifier,
        trace_sink: TraceSink,
        credential_resolver: CredentialResolver | None = None,
        outcome_verifiers: Mapping[str, OutcomeVerifier] | None = None,
        plugins: PluginRegistry | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._documents = document_provider
        self._approval = approval_verifier
        self._trace = trace_sink
        self._credentials = credential_resolver
        self._outcome_verifiers = dict(outcome_verifiers or {})
        self._plugins = plugins or PluginRegistry()
        self._transport = transport
        self._validator = OpenAPIValidator()
        self._clients: dict[tuple[str, str, int], httpx.AsyncClient] = {}
        self._client_lock = asyncio.Lock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        await self.aclose()

    async def aclose(self) -> None:
        async with self._client_lock:
            clients = tuple(self._clients.values())
            self._clients.clear()
        await asyncio.gather(*(client.aclose() for client in clients))

    async def execute(self, request: ExecutionRequest, *, attempt: int = 1) -> ExecutionResult:
        started_at = utc_now()
        self._assert_contract(request)
        await self._emit(request, "execution_started", {"attempt": attempt})
        try:
            await self._approval.verify(request.envelope, request.operation)
            prepared = compile_request(request, plugins=self._plugins)
            await enforce_network_policy(prepared.url, request.connection.network_policy)
            credential = await self._credential(request)
            self._plugins.auth(request.connection.auth_plugin_id).apply(
                prepared.headers,
                prepared.query,
                prepared.cookies,
                credential,
            )
            prepared = _with_query(prepared)
            document = await self._documents.get_document(
                request.connection.openapi_document_hash
            )
            request_issues = self._validator.request_issues(
                request.connection.openapi_document_hash,
                document,
                prepared,
                request.connection.base_url,
            )
            if request_issues:
                return await self._failure(
                    request,
                    started_at,
                    attempt,
                    "request_validation_failed",
                    "The API request does not conform to its OpenAPI contract.",
                    validation_issues=request_issues,
                )
            await self._emit(request, "request_validated", {})
            response = await self._send(request, prepared)
            body = response[3]
            response_issues = self._validator.response_issues(
                request.connection.openapi_document_hash,
                document,
                prepared,
                request.connection.base_url,
                status_code=response[0],
                content_type=response[1],
                headers=response[2],
                body=body,
            )
            if response_issues:
                decoded_failure_body, failure_response_bytes = self._decode_response(
                    request, response[1], body
                )
                write_outcome_unknown = (
                    request.operation.safety_class is not SafetyClass.READ
                )
                return await self._failure(
                    request,
                    started_at,
                    attempt,
                    (
                        "response_contract_outcome_unknown"
                        if write_outcome_unknown
                        else "response_validation_failed"
                    ),
                    (
                        "The API write returned a response, but the response violates "
                        "its contract, so the write outcome is unknown."
                        if write_outcome_unknown
                        else "The API response does not conform to its OpenAPI contract."
                    ),
                    status=(
                        ExecutionStatus.OUTCOME_UNKNOWN
                        if write_outcome_unknown
                        else ExecutionStatus.FAILED
                    ),
                    status_code=response[0],
                    response_media_type=response[1],
                    response_body=decoded_failure_body,
                    response_bytes=failure_response_bytes,
                    validation_issues=response_issues,
                )
            if response[0] < 200 or response[0] >= 300:
                return await self._failure(
                    request,
                    started_at,
                    attempt,
                    "api_error_response",
                    "The API rejected the request.",
                    status_code=response[0],
                    response_media_type=response[1],
                )
            decoded, response_bytes = self._decode_response(
                request, response[1], body
            )
            outcome_verified: bool | None = None
            if request.outcome_verifier_id is not None:
                verifier = self._outcome_verifiers.get(request.outcome_verifier_id)
                if verifier is None:
                    raise ContractError(
                        "outcome_verifier_missing",
                        "The requested outcome verifier is unavailable.",
                    )
                outcome_verified = await verifier.verify(
                    request, response[0], decoded if response_bytes is None else response_bytes
                )
                if not outcome_verified:
                    return await self._failure(
                        request,
                        started_at,
                        attempt,
                        "outcome_verification_failed",
                        "The API response did not prove the intended outcome.",
                        status_code=response[0],
                        response_media_type=response[1],
                    )
            result = ExecutionResult(
                execution_id=request.envelope.execution_id,
                status=ExecutionStatus.SUCCEEDED,
                started_at=started_at,
                finished_at=utc_now(),
                attempt=attempt,
                status_code=response[0],
                response_media_type=response[1],
                response_body=decoded,
                response_bytes=response_bytes,
                outcome_verified=outcome_verified,
            )
            await self._emit(
                request,
                "execution_succeeded",
                {"status_code": response[0], "outcome_verified": outcome_verified},
            )
            return result
        except ApiExecutionError as error:
            return await self._failure(
                request,
                started_at,
                attempt,
                error.code,
                error.public_message,
            )
        except httpx.RequestError as error:
            uncertain = (
                request.operation.safety_class is not SafetyClass.READ
                and not isinstance(error, (httpx.ConnectError, httpx.ConnectTimeout))
            )
            return await self._failure(
                request,
                started_at,
                attempt,
                "transport_outcome_unknown" if uncertain else "transport_failed",
                (
                    "The API write may have been accepted, but its outcome is unknown."
                    if uncertain
                    else "The API could not be reached."
                ),
                status=(
                    ExecutionStatus.OUTCOME_UNKNOWN
                    if uncertain
                    else ExecutionStatus.FAILED
                ),
            )

    def _assert_contract(self, request: ExecutionRequest) -> None:
        if request.contract_version != CONTRACT_VERSION:
            raise ContractError(
                "contract_version_unsupported",
                "The execution contract version is unsupported.",
            )
        envelope = request.envelope
        connection = request.connection
        operation = request.operation
        facts = (
            envelope.tenant_id == connection.tenant_id,
            envelope.connection_id == connection.connection_id,
            envelope.connection_revision == connection.revision,
            envelope.openapi_document_hash == connection.openapi_document_hash,
            envelope.operation_id == operation.operation_id,
        )
        if not all(facts):
            raise ContractError(
                "capability_scope_mismatch",
                "The execution request exceeds its capability scope.",
            )
        now = datetime.now(timezone.utc)
        expires = envelope.expires_at
        if expires.tzinfo is None or expires <= now:
            raise ContractError(
                "capability_expired",
                "The execution capability has expired.",
            )
        if request.operation.safety_class is not SafetyClass.READ:
            if request.idempotency_key and not request.operation.idempotent:
                raise ContractError(
                    "idempotency_not_declared",
                    "This operation does not declare idempotent execution.",
                )

    async def _credential(self, request: ExecutionRequest) -> Mapping[str, str] | None:
        reference = request.connection.credential_ref
        if reference is None:
            return None
        if self._credentials is None:
            raise CredentialError(
                "credential_resolver_missing",
                "The API credential resolver is unavailable.",
            )
        return await self._credentials.resolve(reference)

    async def _send(
        self, request: ExecutionRequest, prepared: PreparedRequest
    ) -> tuple[int, str, Mapping[str, str], bytes]:
        policy = request.connection.network_policy
        timeout = httpx.Timeout(
            connect=policy.connect_timeout_seconds,
            read=policy.read_timeout_seconds,
            write=policy.write_timeout_seconds,
            pool=policy.pool_timeout_seconds,
        )
        client = await self._client(request, timeout)
        outbound = client.build_request(
            prepared.method,
            prepared.url,
            headers=prepared.headers,
            cookies=prepared.cookies,
            content=prepared.body,
        )
        async with client.stream(
            outbound.method,
            str(outbound.url),
            headers=outbound.headers,
            cookies=prepared.cookies,
            content=prepared.body,
        ) as response:
            chunks: list[bytes] = []
            size = 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > policy.max_response_bytes:
                    raise ResponseTooLargeError(
                        "response_too_large",
                        "The API response exceeds the configured size limit.",
                    )
                chunks.append(chunk)
            body = b"".join(chunks)
            content_type = response.headers.get("content-type", "").lower()
            return response.status_code, content_type, dict(response.headers), body

    async def _client(
        self, request: ExecutionRequest, timeout: httpx.Timeout
    ) -> httpx.AsyncClient:
        key = (
            request.connection.tenant_id,
            request.connection.connection_id,
            request.connection.revision,
        )
        async with self._client_lock:
            client = self._clients.get(key)
            if client is None:
                client = httpx.AsyncClient(
                    transport=self._transport,
                    timeout=timeout,
                    follow_redirects=False,
                    trust_env=False,
                )
                self._clients[key] = client
            return client

    def _decode_response(
        self, request: ExecutionRequest, content_type: str, body: bytes
    ) -> tuple[Any, bytes | None]:
        if not body:
            return None, None
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type not in {
            value.split(";", 1)[0].strip().lower()
            for value in request.operation.response_media_types
        }:
            raise ContractError(
                "response_media_type_unexpected",
                "The API response media type is not declared for this operation.",
            )
        plugin = self._plugins.media(media_type)
        return plugin.decode(body, content_type), None

    async def _failure(
        self,
        request: ExecutionRequest,
        started_at,
        attempt: int,
        code: str,
        message: str,
        *,
        status: ExecutionStatus = ExecutionStatus.FAILED,
        status_code: int | None = None,
        response_media_type: str | None = None,
        response_body: Any = None,
        response_bytes: bytes | None = None,
        validation_issues=(),
    ) -> ExecutionResult:
        result = ExecutionResult(
            execution_id=request.envelope.execution_id,
            status=status,
            started_at=started_at,
            finished_at=utc_now(),
            attempt=attempt,
            status_code=status_code,
            response_media_type=response_media_type,
            response_body=response_body,
            response_bytes=response_bytes,
            validation_issues=tuple(validation_issues),
            error_code=code,
            public_message=message,
        )
        await self._emit(
            request,
            "execution_failed" if status is ExecutionStatus.FAILED else status.value,
            {"error_code": code, "status_code": status_code},
        )
        return result

    async def _emit(self, request: ExecutionRequest, event: str, details) -> None:
        await self._trace.emit(
            TraceEvent(
                execution_id=request.envelope.execution_id,
                tenant_id=request.envelope.tenant_id,
                connection_id=request.envelope.connection_id,
                operation_id=request.envelope.operation_id,
                event=event,
                occurred_at=utc_now(),
                safe_details=details,
            )
        )


def _with_query(prepared: PreparedRequest) -> PreparedRequest:
    from urllib.parse import urlencode, urlsplit, urlunsplit

    parsed = urlsplit(prepared.url)
    return PreparedRequest(
        **{
            **prepared.__dict__,
            "url": urlunsplit(
                (parsed.scheme, parsed.netloc, parsed.path, urlencode(prepared.query, doseq=True), "")
            ),
        }
    )
