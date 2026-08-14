from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal, Mapping
from urllib.parse import urlsplit

import httpx

from corpus.credentials import CredentialVaultPort
from corpus.shared.api_execution import (
    RoutedApiExecutionError,
    RoutedApiExecutionOutcome,
    RoutedApiExecutionTarget,
    RoutedApiTraceRecord,
)

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
from ._snapshot.errors import ApprovalError
from ._snapshot.runtime import ApiExecutionRuntime
from .adapters import (
    _ExactDocumentProvider,
    _TraceCollector,
    _VaultCredentialResolver,
    _auth_plugin_id,
    _normalize_base_url,
    _plugins,
)


class RoutedApiExecutionAdapter:
    """Execute one exact plan-selected operation through the neutral snapshot."""

    def __init__(
        self,
        *,
        credentials: CredentialVaultPort,
        allowed_base_urls: tuple[str, ...],
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._credentials = credentials
        self._allowed_base_urls = frozenset(
            _normalize_base_url(value) for value in allowed_base_urls
        )
        self._transport = transport

    async def execute(self, target: RoutedApiExecutionTarget) -> RoutedApiExecutionOutcome:
        outcome, _response_body = await self.execute_for_agent(target)
        return outcome

    async def execute_for_agent(
        self,
        target: RoutedApiExecutionTarget,
    ) -> tuple[RoutedApiExecutionOutcome, Any]:
        """Return the validated response to the in-process Agent only.

        The first tuple item is the normal redacted persistence boundary. The
        second item must remain in memory for response generation and must
        never be serialized into Corpus records, traces, or public DTOs.
        """
        base_url = _normalize_base_url(target.base_url)
        if base_url not in self._allowed_base_urls:
            raise RoutedApiExecutionError("The selected API endpoint is not enabled.")
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
        counting_transport = _RoutedCountingTransport(self._transport)
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
                allow_private_networks=True,
            ),
        )
        approved = target.approved_write and operation.safety_class is not SafetyClass.READ
        envelope = CapabilityEnvelope(
            execution_id=target.execution_id,
            tenant_id=str(target.owner_id),
            connection_id=target.connection_profile_id,
            connection_revision=connection.revision,
            openapi_document_hash=target.document_hash,
            operation_id=target.operation_id,
            expires_at=utc_now() + timedelta(minutes=2),
            approval_token="corpus-reviewed-write" if approved else None,
        )
        read_verifier_id = "corpus-read-response" if operation.safety_class is SafetyClass.READ else None
        runtime = ApiExecutionRuntime(
            document_provider=_ExactDocumentProvider(
                expected_hash=target.document_hash,
                document=target.document,
            ),
            approval_verifier=_RoutedApprovalVerifier(),
            trace_sink=trace,
            credential_resolver=_VaultCredentialResolver(
                vault=self._credentials,
                owner_id=target.owner_id,
                expected_id=target.credential_reference_id,
                expected_version=target.credential_version,
            ),
            outcome_verifiers=(
                {read_verifier_id: _ValidatedReadVerifier()}
                if read_verifier_id is not None
                else {}
            ),
            plugins=_plugins(),
            transport=counting_transport,
        )
        try:
            result = await runtime.execute(
                ExecutionRequest(
                    envelope=envelope,
                    connection=connection,
                    operation=operation,
                    inputs=ExecutionInputs(
                        path=target.path,
                        query=target.query,
                        header=target.header,
                        cookie=target.cookie,
                        body=(
                            {}
                            if target.body is None
                            and operation.request_media_type == "application/json"
                            else target.body
                        ),
                    ),
                    outcome_verifier_id=read_verifier_id,
                )
            )
        finally:
            await runtime.aclose()
        if counting_transport.attempt_count > 1:
            raise RoutedApiExecutionError("A routed API execution attempted more than one call.")
        return (
            _redact_result(
                result,
                traces=tuple(trace.events),
                http_call_count=counting_transport.http_call_count,
                transport_delivery=counting_transport.failure_delivery,
            ),
            result.response_body,
        )


class _RoutedCountingTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport: httpx.AsyncBaseTransport | None) -> None:
        self._transport = transport or httpx.AsyncHTTPTransport()
        self.attempt_count = 0
        self.http_call_count = 0
        self.failure_delivery: RoutedDelivery | None = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.attempt_count += 1
        if self.attempt_count > 1:
            raise httpx.RequestError(
                "A routed API execution cannot issue more than one request.",
                request=request,
            )
        try:
            response = await self._transport.handle_async_request(request)
        except (httpx.ConnectError, httpx.ConnectTimeout):
            self.http_call_count = 0
            self.failure_delivery = "not_sent"
            raise
        except httpx.RequestError:
            self.http_call_count = 1
            self.failure_delivery = "possibly_sent"
            raise
        self.http_call_count = 1
        return response

    async def aclose(self) -> None:
        await self._transport.aclose()


class _RoutedApprovalVerifier:
    async def verify(
        self, envelope: CapabilityEnvelope, operation: OperationContract
    ) -> None:
        if operation.safety_class is SafetyClass.READ:
            return
        if envelope.approval_token != "corpus-reviewed-write":
            raise ApprovalError(
                "write_approval_required",
                "This API write requires explicit owner review.",
            )


class _ValidatedReadVerifier:
    async def verify(
        self,
        request: ExecutionRequest,
        status_code: int,
        response_body: Any,
    ) -> bool:
        del request, response_body
        return 200 <= status_code < 300


def _operation_contract(
    document: Mapping[str, Any],
    operation_id: str,
    *,
    authentication_method: str,
    credential_name: str | None,
) -> OperationContract:
    matches: list[tuple[str, str, Mapping[str, Any], Mapping[str, Any]]] = []
    for raw_path, raw_item in (document.get("paths") or {}).items():
        if not isinstance(raw_path, str) or not isinstance(raw_item, Mapping):
            continue
        for method in ("get", "head", "options", "post", "put", "patch", "delete"):
            raw_operation = raw_item.get(method)
            if isinstance(raw_operation, Mapping) and raw_operation.get("operationId") == operation_id:
                matches.append((method.upper(), raw_path, raw_item, raw_operation))
    if len(matches) != 1:
        raise RoutedApiExecutionError("The selected operation is unavailable in the approved contract.")
    method, path_template, path_item, operation = matches[0]
    parameters: list[ParameterContract] = []
    for raw in [*(path_item.get("parameters") or ()), *(operation.get("parameters") or ())]:
        value = _resolve_local_reference(document, raw)
        if not isinstance(value, Mapping):
            raise RoutedApiExecutionError("The selected operation has an invalid parameter contract.")
        location = str(value.get("in", ""))
        name = str(value.get("name", ""))
        if location not in {"path", "query", "header", "cookie"} or not name:
            continue
        parameters.append(
            ParameterContract(
                name=name,
                location=location,
                required=bool(value.get("required", False)),
                managed_by_auth=(
                    authentication_method == "api_key"
                    and location == "header"
                    and credential_name is not None
                    and name.casefold() == credential_name.casefold()
                ),
            )
        )
    request_body = operation.get("requestBody") or {}
    request_content = request_body.get("content") if isinstance(request_body, Mapping) else {}
    request_media_type = (
        "application/json"
        if isinstance(request_content, Mapping) and "application/json" in request_content
        else None
    )
    response_media_types = tuple(
        sorted(
            {
                media_type
                for response in (operation.get("responses") or {}).values()
                if isinstance(response, Mapping)
                for media_type in (response.get("content") or {})
            }
        )
    ) or ("application/json",)
    return OperationContract(
        operation_id=operation_id,
        method=method,
        path_template=path_template,
        safety_class=(
            SafetyClass.READ if method in {"GET", "HEAD", "OPTIONS"} else SafetyClass.WRITE
        ),
        parameters=tuple(parameters),
        request_media_type=request_media_type,
        response_media_types=response_media_types,
        idempotent=False,
    )


def _resolve_local_reference(
    document: Mapping[str, Any], value: Any
) -> Mapping[str, Any] | Any:
    if not isinstance(value, Mapping) or "$ref" not in value:
        return value
    reference = value.get("$ref")
    if not isinstance(reference, str) or not reference.startswith("#/"):
        raise RoutedApiExecutionError("Only local parameter references are supported.")
    selected: Any = document
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(selected, Mapping) or part not in selected:
            raise RoutedApiExecutionError("The selected operation has an unresolved parameter.")
        selected = selected[part]
    return selected


def _redact_result(
    result: ExecutionResult,
    *,
    traces: tuple[TraceEvent, ...],
    http_call_count: int,
    transport_delivery: RoutedDelivery | None,
) -> RoutedApiExecutionOutcome:
    response_bytes = _canonical_response_bytes(result)
    delivery: RoutedDelivery
    if result.status_code is not None:
        delivery = "response_received"
    elif transport_delivery is not None:
        delivery = transport_delivery
    elif result.error_code == "transport_outcome_unknown":
        delivery = "possibly_sent"
    elif http_call_count == 0:
        delivery = "not_sent"
    else:
        delivery = "possibly_sent"
    allowed = {
        "execution_started": frozenset({"attempt"}),
        "request_validated": frozenset(),
        "execution_succeeded": frozenset({"status_code", "outcome_verified"}),
        "execution_failed": frozenset({"error_code", "status_code"}),
        "outcome_unknown": frozenset({"error_code", "status_code"}),
    }
    safe_traces: list[RoutedApiTraceRecord] = []
    for event in traces:
        keys = allowed.get(event.event)
        if keys is None:
            continue
        details = {
            key: value
            for key in keys
            if (value := event.safe_details.get(key)) is None
            or isinstance(value, (str, int, bool))
        }
        safe_traces.append(
            RoutedApiTraceRecord(
                event=event.event,
                occurred_at=event.occurred_at.isoformat(),
                safe_details=details,
            )
        )
    return RoutedApiExecutionOutcome(
        status=result.status.value,
        delivery=delivery,
        status_code=result.status_code,
        response_media_type=result.response_media_type,
        response_byte_count=len(response_bytes),
        response_body_sha256=(
            hashlib.sha256(response_bytes).hexdigest() if response_bytes else None
        ),
        error_code=result.error_code,
        public_message=result.public_message,
        validation_issue_count=len(result.validation_issues),
        validation_phases=tuple(sorted({item.phase for item in result.validation_issues})),
        outcome_verified=result.outcome_verified,
        http_call_count=http_call_count,
        started_at=result.started_at.isoformat(),
        finished_at=result.finished_at.isoformat(),
        traces=tuple(safe_traces),
    )


def _canonical_response_bytes(result: ExecutionResult) -> bytes:
    if result.response_bytes is not None:
        return result.response_bytes
    if result.response_body is None:
        return b""
    return json.dumps(
        result.response_body,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


__all__ = [
    "RoutedApiExecutionAdapter",
    "RoutedApiExecutionError",
    "RoutedApiExecutionOutcome",
    "RoutedApiExecutionTarget",
    "RoutedApiTraceRecord",
    "RoutedDelivery",
]
