from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

import httpx
import yaml

from corpus.integrations.api_execution._snapshot.contract_revision import (
    openapi_document_hash,
)
from corpus.integrations.api_execution._snapshot.contracts import (
    CapabilityEnvelope,
    ConnectionRevision,
    ExecutionRequest,
    ExecutionStatus,
    NetworkPolicy,
    OperationContract,
    ParameterContract,
    SafetyClass,
    TraceEvent,
    utc_now,
)
from corpus.integrations.api_execution._snapshot.runtime import ApiExecutionRuntime


DEFAULT_SPEC = Path(
    r"D:\Dev\AI Projects\agent-core\research\openapi_toolrouter_benchmark"
    r"\data\openapi\medusa_store.yaml"
)
DEFAULT_CREDENTIALS = Path(
    r"D:\Dev\AI Projects\routedeck\examples\medusa-agent\.env.local"
)
DEFAULT_OUTPUT = Path(
    ".runtime/audits/20260807-api-execution-phase-a/get-product-types.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one redacted read through the restricted API execution snapshot."
    )
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--credentials", type=Path, default=DEFAULT_CREDENTIALS)
    parser.add_argument("--base-url", default="http://127.0.0.1:9100")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


async def run(args: argparse.Namespace) -> dict[str, Any]:
    spec_bytes = args.spec.read_bytes()
    document = yaml.safe_load(spec_bytes)
    if not isinstance(document, Mapping):
        raise RuntimeError("The Medusa OpenAPI source is not an object.")
    document_hash = openapi_document_hash(document)
    operation = _operation(document)
    credential_value = _env_value(args.credentials, "MEDUSA_PUBLISHABLE_KEY")
    traces = _TraceSink()
    connection = ConnectionRevision(
        connection_id="phase-a-reference-connection",
        revision=1,
        tenant_id="phase-a-reference-tenant",
        base_url=args.base_url,
        openapi_document_hash=document_hash,
        auth_plugin_id="api_key_header",
        credential_ref="phase-a-reference-credential",
        network_policy=NetworkPolicy(
            allow_http=True,
            allow_private_networks=True,
        ),
    )
    envelope = CapabilityEnvelope(
        execution_id="phase-a-get-product-types",
        tenant_id=connection.tenant_id,
        connection_id=connection.connection_id,
        connection_revision=connection.revision,
        openapi_document_hash=document_hash,
        operation_id=operation.operation_id,
        expires_at=utc_now() + timedelta(minutes=5),
    )
    transport = _CountingTransport()
    runtime = ApiExecutionRuntime(
        document_provider=_DocumentProvider(document_hash, document),
        credential_resolver=_CredentialResolver(credential_value),
        approval_verifier=_ReadApprovalVerifier(),
        trace_sink=traces,
        transport=transport,
    )
    try:
        async with runtime:
            result = await runtime.execute(
                ExecutionRequest(
                    envelope=envelope,
                    connection=connection,
                    operation=operation,
                )
            )
    except Exception as error:
        await transport.aclose()
        evidence = {
            "schema_version": 1,
            "runtime": "local Windows",
            "target": args.base_url,
            "operation_id": operation.operation_id,
            "safety_class": operation.safety_class.value,
            "source_spec_path": str(args.spec.resolve()),
            "source_spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
            "canonical_document_sha256": document_hash,
            "status": (
                "blocked_before_http"
                if transport.call_count == 0
                else "failed_after_http"
            ),
            "http_request_sent": transport.call_count > 0,
            "http_request_count": transport.call_count,
            "http_status": None,
            "validation_issue_count": (
                1 if type(error).__name__ == "OpenAPIValidationError" else 0
            ),
            "error_code": (
                "openapi_spec_invalid"
                if type(error).__name__ == "OpenAPIValidationError"
                else "reference_runtime_error"
            ),
            "error_class": type(error).__name__,
            "trace_event_count": len(traces.events),
            "trace": _redacted_trace(traces.events),
            "redaction": {
                "credential_values_retained": False,
                "response_body_retained": False,
                "request_headers_retained": False,
                "exception_message_retained": False,
            },
        }
        _write_evidence(args.output, evidence, credential_value)
        return evidence

    response_hash = _json_hash(result.response_body)
    response_count = _product_type_count(result.response_body)
    evidence = {
        "schema_version": 1,
        "runtime": "local Windows",
        "target": args.base_url,
        "operation_id": operation.operation_id,
        "safety_class": operation.safety_class.value,
        "source_spec_path": str(args.spec.resolve()),
        "source_spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "canonical_document_sha256": document_hash,
        "status": result.status.value,
        "http_request_sent": transport.call_count > 0,
        "http_request_count": transport.call_count,
        "http_status": result.status_code,
        "validation_issue_count": len(result.validation_issues),
        "error_code": result.error_code,
        "response_body_sha256": response_hash,
        "response_product_type_count": response_count,
        "trace_event_count": len(traces.events),
        "trace": _redacted_trace(traces.events),
        "redaction": {
            "credential_values_retained": False,
            "response_body_retained": False,
            "request_headers_retained": False,
        },
    }
    _write_evidence(args.output, evidence, credential_value)
    if result.status is not ExecutionStatus.SUCCEEDED:
        raise RuntimeError(
            f"The read failed with {result.status.value}/{result.error_code}."
        )
    return evidence


def _operation(document: Mapping[str, Any]) -> OperationContract:
    path = "/store/product-types"
    path_item = document["paths"][path]
    operation = path_item["get"]
    parameters = []
    for value in [*(path_item.get("parameters") or []), *(operation.get("parameters") or [])]:
        if "$ref" in value:
            raise RuntimeError("The reference operation contains an unresolved parameter.")
        location = str(value["in"])
        name = str(value["name"])
        parameters.append(
            ParameterContract(
                name=name,
                location=location,
                required=bool(value.get("required")),
                managed_by_auth=(location, name) == (
                    "header",
                    "x-publishable-api-key",
                ),
            )
        )
    response_media_types = sorted(
        {
            media_type
            for response in (operation.get("responses") or {}).values()
            if isinstance(response, Mapping)
            for media_type in ((response.get("content") or {}).keys())
        }
    )
    return OperationContract(
        operation_id=str(operation["operationId"]),
        method="GET",
        path_template=path,
        safety_class=SafetyClass.READ,
        parameters=tuple(parameters),
        response_media_types=tuple(response_media_types or ["application/json"]),
        idempotent=True,
    )


def _env_value(path: Path, name: str) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            result = value.strip().strip('"').strip("'")
            if result:
                return result
    raise RuntimeError(f"Required credential {name} is unavailable.")


def _json_hash(value: Any) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _product_type_count(value: Any) -> int | None:
    if not isinstance(value, Mapping):
        return None
    product_types = value.get("product_types")
    return len(product_types) if isinstance(product_types, list) else None


class _DocumentProvider:
    def __init__(self, document_hash: str, document: Mapping[str, Any]) -> None:
        self.document_hash = document_hash
        self.document = document

    async def get_document(self, document_hash: str) -> Mapping[str, Any]:
        if document_hash != self.document_hash:
            raise RuntimeError("The requested OpenAPI document is unavailable.")
        return self.document


class _CredentialResolver:
    def __init__(self, value: str) -> None:
        self.value = value

    async def resolve(self, credential_ref: str) -> Mapping[str, str]:
        if credential_ref != "phase-a-reference-credential":
            raise RuntimeError("The requested credential is unavailable.")
        return {
            "header_name": "x-publishable-api-key",
            "value": self.value,
        }


class _ReadApprovalVerifier:
    async def verify(
        self,
        envelope: CapabilityEnvelope,
        operation: OperationContract,
    ) -> None:
        if operation.safety_class is not SafetyClass.READ:
            raise RuntimeError("Phase A permits only the approved read reference.")
        if envelope.operation_id != "GetProductTypes":
            raise RuntimeError("Phase A permits only GetProductTypes.")


class _TraceSink:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    async def emit(self, event: TraceEvent) -> None:
        self.events.append(event)


class _CountingTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.call_count = 0
        self._transport = httpx.AsyncHTTPTransport()
        self._closed = False

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.call_count += 1
        return await self._transport.handle_async_request(request)

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            await self._transport.aclose()


def _redacted_trace(events: list[TraceEvent]) -> list[dict[str, Any]]:
    return [
        {
            "event": event.event,
            "safe_detail_keys": sorted(event.safe_details),
        }
        for event in events
    ]


def _write_evidence(path: Path, evidence: Mapping[str, Any], credential: str) -> None:
    encoded = json.dumps(evidence, indent=2, sort_keys=True)
    if credential in encoded:
        raise RuntimeError("Credential material reached the redacted evidence payload.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded + "\n", encoding="utf-8")


def main() -> int:
    evidence = asyncio.run(run(parse_args()))
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "http_status": evidence["http_status"],
                "validation_issue_count": evidence["validation_issue_count"],
                "response_product_type_count": evidence.get(
                    "response_product_type_count"
                ),
                "trace_event_count": evidence["trace_event_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if evidence["status"] == ExecutionStatus.SUCCEEDED.value else 2


if __name__ == "__main__":
    raise SystemExit(main())
