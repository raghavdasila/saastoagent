from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
import tomllib
from argparse import Namespace
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

import httpx
import pytest
from prance import BaseParser
from scripts import run_api_execution_phase_a_reference as reference_runner

from corpus.integrations.api_execution import _snapshot
from corpus.integrations.api_execution._snapshot.compiler import PreparedRequest
from corpus.integrations.api_execution._snapshot.contracts import (
    CapabilityEnvelope,
    ConnectionRevision,
    ExecutionRequest,
    ExecutionStatus,
    NetworkPolicy,
    OperationContract,
    SafetyClass,
    TraceEvent,
    utc_now,
)
from corpus.integrations.api_execution._snapshot.runtime import ApiExecutionRuntime
from corpus.integrations.api_execution._snapshot.validation import OpenAPIValidator


SNAPSHOT_ROOT = Path(_snapshot.__file__).resolve().parent
BACKEND_ROOT = SNAPSHOT_ROOT.parents[4]
MANIFEST = json.loads(
    (SNAPSHOT_ROOT / "source_manifest.json").read_text(encoding="utf-8")
)
EXPECTED_FILES = {
    "compiler.py",
    "contracts.py",
    "contract_revision.py",
    "errors.py",
    "plugins.py",
    "ports.py",
    "runtime.py",
    "security.py",
    "validation.py",
}


def test_snapshot_is_the_exact_approved_sibling_closure() -> None:
    source_root = Path(MANIFEST["source_repository"])
    assert source_root.is_dir()
    assert MANIFEST["source_package_version"] == "0.1.0"
    assert {entry["vendored_path"] for entry in MANIFEST["files"]} == EXPECTED_FILES
    assert {
        path.name for path in SNAPSHOT_ROOT.glob("*.py") if path.name != "__init__.py"
    } == EXPECTED_FILES

    for entry in MANIFEST["files"]:
        source = source_root / entry["source_path"]
        vendored = SNAPSHOT_ROOT / entry["vendored_path"]
        assert _sha256(source) == entry["source_sha256"]
        assert _sha256(vendored) == entry["vendored_sha256"]
        assert entry["source_sha256"] == entry["vendored_sha256"]
        assert source.read_bytes() == vendored.read_bytes()


def test_snapshot_initializer_and_imports_remain_restricted() -> None:
    assert _snapshot.__all__ == ["SNAPSHOT_PACKAGE_VERSION"]
    assert _snapshot.SNAPSHOT_PACKAGE_VERSION == "0.1.0"
    assert not any(name.startswith("api_execution_runtime") for name in sys.modules)
    for forbidden in (
        "adapters.py",
        "codec.py",
        "contract_store.py",
        "jobs.py",
        "worker.py",
    ):
        assert not (SNAPSHOT_ROOT / forbidden).exists()
    for path in SNAPSHOT_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "D:\\Dev\\AI Projects\\api-execution-runtime" not in source
        assert "from api_execution_runtime" not in source
        assert "import api_execution_runtime" not in source


def test_provenance_limits_the_snapshot_to_owner_authorized_internal_use() -> None:
    authorization = MANIFEST["snapshot_authorization"]
    provenance = (SNAPSHOT_ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
    assert "Owner-authorized for use within Corpus" in authorization
    assert "No public redistribution license has been established" in authorization
    assert "do not publish or redistribute" in authorization
    assert "internal, same-owner integration only" in provenance
    assert "Phase A does not wire this snapshot into Sources" in provenance


def test_project_metadata_pins_the_approved_dependency_set_without_prance_osv() -> None:
    metadata = tomllib.loads(
        (BACKEND_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert metadata["project"]["requires-python"] == ">=3.11,<3.12"
    dependencies = set(metadata["project"]["dependencies"])
    assert {
        "openapi-core==0.23.1",
        "httpx==0.28.1",
        "openapi-spec-validator==0.8.5",
        "prance==25.4.8.0",
    } <= dependencies
    assert not any(value.startswith("prance[") for value in dependencies)


def test_dependency_versions_and_python_runtime_match_the_approved_baseline() -> None:
    assert sys.version_info[:2] == (3, 11)
    assert importlib.metadata.version("openapi-core") == "0.23.1"
    assert importlib.metadata.version("httpx") == "0.28.1"
    assert importlib.metadata.version("openapi-spec-validator") == "0.8.5"
    assert importlib.metadata.version("prance") == "25.4.8.0"


def test_prance_parses_a_minimal_openapi_document_with_the_pinned_validator() -> None:
    parser = BaseParser(
        spec_string="""
openapi: 3.0.3
info:
  title: Minimal reference
  version: 1.0.0
paths:
  /product-types:
    get:
      operationId: GetProductTypes
      responses:
        '200':
          description: Product types
""",
        backend="openapi-spec-validator",
        strict=True,
    )

    assert parser.specification["openapi"] == "3.0.3"
    assert parser.specification["paths"]["/product-types"]["get"]["operationId"] == (
        "GetProductTypes"
    )


def test_openapi_core_request_and_response_apis_match_the_snapshot() -> None:
    validator = OpenAPIValidator()
    document = _document()
    prepared = PreparedRequest(
        method="GET",
        url="http://127.0.0.1:9100/product-types",
        host_url="http://127.0.0.1:9100",
        path="/product-types",
        full_url_pattern="http://127.0.0.1:9100/product-types",
        headers={},
        query={},
        cookies={},
        path_parameters={},
        body=None,
        content_type="",
    )

    assert validator.request_issues(
        "document-hash", document, prepared, "http://127.0.0.1:9100"
    ) == ()
    assert validator.response_issues(
        "document-hash",
        document,
        prepared,
        "http://127.0.0.1:9100",
        status_code=200,
        content_type="application/json",
        headers={"content-type": "application/json"},
        body=b'{"product_types":[]}',
    ) == ()


@pytest.mark.asyncio
async def test_unchanged_snapshot_executes_a_validated_read_with_injected_transport() -> None:
    document = _document()
    traces = _TraceSink()
    runtime = ApiExecutionRuntime(
        document_provider=_DocumentProvider(document),
        approval_verifier=_ApprovalVerifier(),
        trace_sink=traces,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"content-type": "application/json"},
                json={"product_types": []},
                request=request,
            )
        ),
    )
    request = _request()

    async with runtime:
        result = await runtime.execute(request)

    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.status_code == 200
    assert result.response_body == {"product_types": []}
    assert [event.event for event in traces.events] == [
        "execution_started",
        "request_validated",
        "execution_succeeded",
    ]


@pytest.mark.asyncio
async def test_reference_runner_retains_truthful_blocked_before_http_evidence(
    tmp_path: Path,
) -> None:
    spec = tmp_path / "invalid-openapi.yaml"
    credentials = tmp_path / ".env.local"
    output = tmp_path / "blocked-before-http.json"
    secret = "focused-reference-secret"
    spec.write_text(
        """
openapi: 3.0.3
info:
  title: Invalid default reference
  version: 1.0.0
paths:
  /store/product-types:
    get:
      operationId: GetProductTypes
      responses:
        '200':
          description: Product types
          content:
            application/json:
              schema:
                type: object
components:
  schemas:
    InvalidBooleanDefault:
      type: object
      properties:
        deleted:
          type: boolean
          default: variant
""".lstrip(),
        encoding="utf-8",
    )
    credentials.write_text(
        f"MEDUSA_PUBLISHABLE_KEY={secret}\n",
        encoding="utf-8",
    )

    evidence = await reference_runner.run(
        Namespace(
            spec=spec,
            credentials=credentials,
            base_url="http://127.0.0.1:9",
            output=output,
        )
    )

    assert evidence["status"] == "blocked_before_http"
    assert evidence["http_request_sent"] is False
    assert evidence["http_request_count"] == 0
    assert evidence["http_status"] is None
    assert evidence["error_code"] == "openapi_spec_invalid"
    assert evidence["error_class"] == "OpenAPIValidationError"
    assert evidence["validation_issue_count"] == 1
    assert evidence["trace_event_count"] == 1
    assert evidence["trace"] == [
        {"event": "execution_started", "safe_detail_keys": ["attempt"]}
    ]
    encoded = output.read_text(encoding="utf-8")
    assert secret not in encoded
    retained = json.loads(encoded)
    assert "response_body" not in retained
    assert "request_headers" not in retained
    assert retained["redaction"]["response_body_retained"] is False
    assert retained["redaction"]["request_headers_retained"] is False


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _document() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Runtime reference", "version": "1.0.0"},
        "paths": {
            "/product-types": {
                "get": {
                    "operationId": "GetProductTypes",
                    "responses": {
                        "200": {
                            "description": "Product types",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["product_types"],
                                        "properties": {
                                            "product_types": {
                                                "type": "array",
                                                "items": {"type": "object"},
                                            }
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


def _request() -> ExecutionRequest:
    connection = ConnectionRevision(
        connection_id="connection-reference",
        revision=1,
        tenant_id="tenant-reference",
        base_url="http://127.0.0.1:9100",
        openapi_document_hash="document-hash",
        network_policy=NetworkPolicy(
            allow_http=True,
            allow_private_networks=True,
        ),
    )
    operation = OperationContract(
        operation_id="GetProductTypes",
        method="GET",
        path_template="/product-types",
        safety_class=SafetyClass.READ,
    )
    envelope = CapabilityEnvelope(
        execution_id="execution-reference",
        tenant_id=connection.tenant_id,
        connection_id=connection.connection_id,
        connection_revision=connection.revision,
        openapi_document_hash=connection.openapi_document_hash,
        operation_id=operation.operation_id,
        expires_at=utc_now() + timedelta(minutes=5),
    )
    return ExecutionRequest(
        envelope=envelope,
        connection=connection,
        operation=operation,
    )


class _DocumentProvider:
    def __init__(self, document: Mapping[str, Any]) -> None:
        self.document = document

    async def get_document(self, document_hash: str) -> Mapping[str, Any]:
        assert document_hash == "document-hash"
        return self.document


class _ApprovalVerifier:
    async def verify(
        self,
        envelope: CapabilityEnvelope,
        operation: OperationContract,
    ) -> None:
        assert envelope.operation_id == operation.operation_id


class _TraceSink:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    async def emit(self, event: TraceEvent) -> None:
        self.events.append(event)
