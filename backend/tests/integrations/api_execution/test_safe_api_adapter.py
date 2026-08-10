from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Mapping

import httpx

from corpus.credentials.domain import CredentialReference, ResolvedCredential
from corpus.integrations.api_execution.adapters import (
    SafeApiExecutionAdapter,
    SafeApiExecutionTarget,
)
from corpus.integrations.api_execution._snapshot.contract_revision import (
    openapi_document_hash,
)
from corpus.integrations.api_execution.redaction import redact_execution


OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")
CREDENTIAL = uuid.UUID("00000000-0000-0000-0000-000000000011")
SECRET = "phase-c-secret-canary"


class FixedVault:
    def __init__(
        self,
        *,
        owner_id: uuid.UUID = OWNER,
        version: int = 3,
        resolve_error: Exception | None = None,
    ) -> None:
        self.owner_id = owner_id
        self.version = version
        self.resolve_error = resolve_error
        self.resolve_calls = 0

    async def resolve(self, *, owner_id: uuid.UUID, credential_id: uuid.UUID):
        self.resolve_calls += 1
        if self.resolve_error is not None:
            raise self.resolve_error
        assert owner_id == OWNER
        assert credential_id == CREDENTIAL
        now = datetime.now(UTC)
        return ResolvedCredential(
            reference=CredentialReference(
                id=CREDENTIAL,
                owner_id=self.owner_id,
                label="Medusa",
                kind="api_connection_api_key",
                version=self.version,
                created_at=now,
                updated_at=now,
            ),
            values={"header_name": "x-publishable-api-key", "value": SECRET},
        )


def test_safe_adapter_resolves_exact_credential_just_in_time_and_calls_once() -> None:
    seen: list[httpx.Request] = []

    async def respond(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"product_types": []},
        )

    vault = FixedVault()
    outcome = asyncio.run(
        _execute(
            vault=vault,
            transport=httpx.MockTransport(respond),
            credential_name="X-PUBLISHABLE-API-KEY",
        )
    )
    redacted = redact_execution(outcome)

    assert outcome.result.status.value == "succeeded"
    assert outcome.http_call_count == 1
    assert vault.resolve_calls == 1
    assert len(seen) == 1
    assert seen[0].headers["x-publishable-api-key"] == SECRET
    retained = redacted.model_dump_json()
    assert SECRET not in retained
    assert "headers" not in retained
    assert "response_body" not in retained
    assert "query" not in retained
    assert SECRET not in repr(outcome.result)
    assert SECRET not in repr(outcome.traces)
    assert redacted.http_call_count == 1
    assert [item.event for item in redacted.traces] == [
        "execution_started",
        "request_validated",
        "execution_succeeded",
    ]


def test_safe_adapter_does_not_treat_other_required_headers_as_auth_managed() -> None:
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"product_types": []})

    document = _document()
    operation = document["paths"]["/store/product-types"]["get"]  # type: ignore[index]
    operation["parameters"].append(  # type: ignore[index,union-attr]
        {
            "name": "x-required-non-auth",
            "in": "header",
            "required": True,
            "schema": {"type": "string"},
        }
    )
    outcome = asyncio.run(
        _execute(
            vault=FixedVault(),
            transport=httpx.MockTransport(respond),
            document=document,
        )
    )

    assert outcome.result.status.value == "failed"
    assert outcome.result.error_code == "required_input_missing"
    assert outcome.http_call_count == 0
    assert calls == 0
    assert SECRET not in repr(outcome.result)
    assert SECRET not in repr(outcome.traces)


def test_safe_adapter_rejects_changed_credential_version_before_http() -> None:
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"product_types": []})

    vault = FixedVault(version=4)
    outcome = asyncio.run(
        _execute(vault=vault, transport=httpx.MockTransport(respond))
    )
    redacted = redact_execution(outcome)

    assert outcome.result.status.value == "failed"
    assert outcome.result.error_code == "credential_version_mismatch"
    assert outcome.http_call_count == 0
    assert calls == 0
    assert vault.resolve_calls == 1
    assert redacted.http_call_count == 0
    assert SECRET not in redacted.model_dump_json()


def test_safe_adapter_retains_response_validation_failure_without_body_or_retry() -> None:
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"unexpected": SECRET},
        )

    outcome = asyncio.run(
        _execute(vault=FixedVault(), transport=httpx.MockTransport(respond))
    )
    redacted = redact_execution(outcome)

    assert outcome.result.status.value == "failed"
    assert outcome.result.error_code == "response_validation_failed"
    assert outcome.http_call_count == 1
    assert calls == 1
    assert redacted.validation_issue_count > 0
    retained = redacted.model_dump_json()
    assert SECRET not in retained
    assert "unexpected" not in retained


def test_safe_adapter_converts_vault_authentication_failure_to_zero_call_safe_failure() -> None:
    calls = 0
    canary = "vault-corruption-exception-secret"

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"product_types": []})

    outcome = asyncio.run(
        _execute(
            vault=FixedVault(resolve_error=RuntimeError(canary)),
            transport=httpx.MockTransport(respond),
        )
    )
    redacted = redact_execution(outcome)

    assert outcome.result.status.value == "failed"
    assert outcome.result.error_code == "credential_unavailable"
    assert outcome.http_call_count == 0
    assert calls == 0
    assert canary not in redacted.model_dump_json()


def test_safe_adapter_executes_get_product_tags_as_the_other_exact_safe_read() -> None:
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.path == "/store/product-tags"
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"product_tags": []},
        )

    outcome = asyncio.run(
        _execute(
            vault=FixedVault(),
            transport=httpx.MockTransport(respond),
            operation_id="GetProductTags",
        )
    )

    assert outcome.result.status.value == "succeeded"
    assert outcome.http_call_count == 1
    assert calls == 1


async def _execute(
    *,
    vault: FixedVault,
    transport: httpx.AsyncBaseTransport,
    operation_id: str = "GetProductTypes",
    credential_name: str = "x-publishable-api-key",
    document: Mapping[str, object] | None = None,
):
    document = document or _document()
    adapter = SafeApiExecutionAdapter(
        credentials=vault,  # type: ignore[arg-type]
        allowed_base_urls=("https://example.com",),
        transport=transport,
    )
    return await adapter.execute(
        SafeApiExecutionTarget(
            execution_id="execution-safe-1",
            owner_id=OWNER,
            source_id="sourceopaque0001",
            source_revision_id="revisionopaque01",
            connection_profile_id="profileopaque001",
            base_url="https://example.com",
            authentication_method="api_key",
            credential_name=credential_name,
            credential_reference_id=CREDENTIAL,
            credential_version=3,
            document_hash=openapi_document_hash(document),
            document=document,
            operation_id=operation_id,
        )
    )


def _document() -> Mapping[str, object]:
    return json.loads(
        """
        {
          "openapi": "3.0.3",
          "info": {"title": "Safe test", "version": "1.0.0"},
          "paths": {
            "/store/product-types": {
              "get": {
                "operationId": "GetProductTypes",
                "parameters": [
                  {
                    "name": "x-publishable-api-key",
                    "in": "header",
                    "required": true,
                    "schema": {"type": "string"}
                  }
                ],
                "responses": {
                  "200": {
                    "description": "ok",
                    "content": {
                      "application/json": {
                        "schema": {
                          "type": "object",
                          "required": ["product_types"],
                          "additionalProperties": false,
                          "properties": {
                            "product_types": {
                              "type": "array",
                              "items": {"type": "object"}
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            "/store/product-tags": {
              "get": {
                "operationId": "GetProductTags",
                "responses": {
                  "200": {
                    "description": "ok",
                    "content": {
                      "application/json": {
                        "schema": {
                          "type": "object",
                          "required": ["product_tags"],
                          "additionalProperties": false,
                          "properties": {
                            "product_tags": {
                              "type": "array",
                              "items": {"type": "object"}
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
    )
