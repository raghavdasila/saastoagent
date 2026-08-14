from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from corpus.credentials.domain import CredentialReference, ResolvedCredential
from corpus.features.sources.connectors.api.connection_checks import (
    ApiConnectionCheckConflict,
    ApiConnectionCheckRepository,
    ApiConnectionCheckService,
)
from corpus.features.sources.connectors.api.connections import (
    ApiAuthenticationMethod,
    ApiConnectionProfileRepository,
)
from corpus.features.sources.models import (
    ContractPatchRecord,
    ContractRevisionProposalRecord,
    ContractRevisionProposalState,
    SourceState,
)
from corpus.features.sources.repository import LocalSourceRepository, SourceNotFound
from corpus.features.sources.operations import (
    TestApiConnectionHandler as ApiConnectionCheckHandler,
)
from corpus.integrations.api_execution._snapshot.contract_revision import (
    openapi_document_hash,
)
from corpus.integrations.api_execution.adapters import SafeApiExecutionAdapter


OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_OWNER = uuid.UUID("00000000-0000-0000-0000-000000000002")
CREDENTIAL = uuid.UUID("00000000-0000-0000-0000-000000000011")
SECRET = "source-check-secret-canary"


class FixedOwnerScope:
    async def organization_id_for_route(self, session_id: str) -> uuid.UUID:
        assert session_id == "source-session"
        return OWNER


class FixedVault:
    def __init__(
        self,
        *,
        owner_id: uuid.UUID = OWNER,
        version: int = 2,
        resolve_error: Exception | None = None,
    ) -> None:
        self.owner_id = owner_id
        self.version = version
        self.resolve_error = resolve_error
        self.metadata_calls = 0
        self.resolve_calls = 0

    async def metadata(self, *, owner_id: uuid.UUID, credential_id: uuid.UUID):
        self.metadata_calls += 1
        return self._reference()

    async def resolve(self, *, owner_id: uuid.UUID, credential_id: uuid.UUID):
        self.resolve_calls += 1
        if self.resolve_error is not None:
            raise self.resolve_error
        return ResolvedCredential(
            reference=self._reference(),
            values={"header_name": "x-publishable-api-key", "value": SECRET},
        )

    def _reference(self) -> CredentialReference:
        now = datetime.now(UTC)
        return CredentialReference(
            id=CREDENTIAL,
            owner_id=self.owner_id,
            label="Medusa",
            kind="api_connection_api_key",
            version=self.version,
            created_at=now,
            updated_at=now,
        )


def test_safe_check_revalidates_exact_identity_calls_once_and_persists_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_id, revision_id, profile_id, contract_hash = _fixture(tmp_path)
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"product_types": []},
        )

    vault = FixedVault()
    service = _service(
        repository, vault, httpx.MockTransport(respond)
    )
    record = asyncio.run(
        service.execute(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
            connection_profile_id=profile_id,
            operation_id="GetProductTypes",
        )
    )

    assert record.status == "succeeded"
    assert record.http_call_count == 1
    assert calls == 1
    assert vault.metadata_calls == 1
    assert vault.resolve_calls == 1
    reloaded = service.list(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    assert reloaded == (record,)
    retained = next((tmp_path / "sources").rglob(f"{record.id}.json")).read_text(
        encoding="utf-8"
    )
    assert SECRET not in retained
    for forbidden in ("headers", "query", "response_body", "credential_value"):
        assert forbidden not in retained
    with pytest.raises(SourceNotFound):
        service.list(
            owner_id=OTHER_OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        )


def test_changed_credential_version_is_an_immutable_zero_call_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_id, revision_id, profile_id, contract_hash = _fixture(tmp_path)
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"product_types": []})

    service = _service(repository, FixedVault(version=3), httpx.MockTransport(respond))
    record = asyncio.run(
        service.execute(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
            connection_profile_id=profile_id,
            operation_id="GetProductTypes",
        )
    )

    assert record.status == "failed"
    assert record.error_code == "credential_version_mismatch"
    assert record.http_call_count == 0
    assert calls == 0
    assert len(service.list(
        owner_id=OWNER, source_id=source_id, source_revision_id=revision_id
    )) == 1


def test_invalid_operation_or_profile_never_calls_or_persists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_id, revision_id, profile_id, contract_hash = _fixture(tmp_path)
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"product_types": []})

    service = _service(repository, FixedVault(), httpx.MockTransport(respond))
    with pytest.raises(ApiConnectionCheckConflict, match="not approved"):
        asyncio.run(
            service.execute(
                owner_id=OWNER,
                source_id=source_id,
                source_revision_id=revision_id,
                connection_profile_id=profile_id,
                operation_id="CreateProduct",
            )
        )
    with pytest.raises(Exception, match="unavailable"):
        asyncio.run(
            service.execute(
                owner_id=OWNER,
                source_id=source_id,
                source_revision_id=revision_id,
                connection_profile_id="missingprofile01",
                operation_id="GetProductTypes",
            )
        )
    assert calls == 0
    assert service.list(
        owner_id=OWNER, source_id=source_id, source_revision_id=revision_id
    ) == ()


def test_jit_vault_corruption_is_persisted_as_redacted_zero_call_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_id, revision_id, profile_id, contract_hash = _fixture(tmp_path)
    canary = "credential-authentication-exception-secret"
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"product_types": []})

    service = _service(
        repository,
        FixedVault(resolve_error=RuntimeError(canary)),
        httpx.MockTransport(respond),
    )
    record = asyncio.run(
        service.execute(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
            connection_profile_id=profile_id,
            operation_id="GetProductTypes",
        )
    )

    assert record.status == "failed"
    assert record.error_code == "credential_unavailable"
    assert record.http_call_count == 0
    assert calls == 0
    retained = next((tmp_path / "sources").rglob(f"{record.id}.json")).read_text(
        encoding="utf-8"
    )
    assert canary not in retained


def test_routedeck_handler_rechecks_and_returns_truthful_success_and_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_id, revision_id, profile_id, contract_hash = _fixture(tmp_path)
    responses = iter(
        (
            httpx.Response(
                200,
                headers={"content-type": "application/json"},
                json={"product_types": []},
            ),
            httpx.Response(
                401,
                headers={"content-type": "application/json"},
                json={"message": "rejected"},
            ),
        )
    )

    async def respond(request: httpx.Request) -> httpx.Response:
        return next(responses)

    handler = ApiConnectionCheckHandler(
        _service(repository, FixedVault(), httpx.MockTransport(respond)),
        FixedOwnerScope(),  # type: ignore[arg-type]
    )
    context = SimpleNamespace(
        session_id="source-session",
        attempt_id="attempt-safe-check",
        request_id="request-safe-check",
    )
    arguments = {
        "source_id": source_id,
        "source_revision_id": revision_id,
        "connection_profile_id": profile_id,
        "operation_id": "GetProductTypes",
    }

    succeeded = asyncio.run(handler(arguments, context))  # type: ignore[arg-type]
    failed = asyncio.run(handler(arguments, context))  # type: ignore[arg-type]

    assert succeeded.outcome == "checked"
    assert succeeded.failure is None
    assert failed.outcome is None
    assert failed.failure is not None
    assert failed.failure.code == "api_connection_check_failed"
    assert failed.delivery_phase.value == "response_received"
    records = handler.service.list(
        owner_id=OWNER, source_id=source_id, source_revision_id=revision_id
    )
    assert [item.status for item in records] == ["succeeded", "failed"]


def _service(repository, vault, transport):
    profiles = ApiConnectionProfileRepository(repository)
    return ApiConnectionCheckService(
        sources=repository,
        profiles=profiles,
        records=ApiConnectionCheckRepository(repository),
        credentials=vault,
        execution=SafeApiExecutionAdapter(
            credentials=vault,
            allowed_base_urls=("https://example.com",),
            transport=transport,
        ),
    )


def _fixture(tmp_path: Path):
    document = {
        "openapi": "3.0.3",
        "info": {"title": "Safe test", "version": "1.0.0"},
        "paths": {
            "/store/product-types": {
                "get": {
                    "operationId": "GetProductTypes",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["product_types"],
                                        "additionalProperties": False,
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
    candidate = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    contract_hash = openapi_document_hash(document)
    repository = LocalSourceRepository(tmp_path / "sources")
    parent = repository.begin_source(
        owner_key=str(OWNER),
        connector_key="api",
        display_name="Safe API",
        original_filename="raw.yaml",
        content=b"openapi: 3.0.3\ninfo: {title: raw, version: 1}\npaths: {}\n",
    )
    repository.mark_running(
        owner_key=str(OWNER),
        source_id=parent.source.source_id,
        revision_id=parent.revision.revision_id,
    )
    repository.mark_ready(
        owner_key=str(OWNER),
        source_id=parent.source.source_id,
        revision_id=parent.revision.revision_id,
        summary={},
    )
    proposal = ContractRevisionProposalRecord(
        proposal_id="proposalopaque01",
        source_id=parent.source.source_id,
        parent_revision_id=parent.revision.revision_id,
        state=ContractRevisionProposalState.PENDING,
        source_raw_sha256="a" * 64,
        source_canonical_sha256="b" * 64,
        repair_manifest_sha256="c" * 64,
        repaired_parent_sha256="d" * 64,
        final_canonical_sha256=contract_hash,
        patches=(
            ContractPatchRecord(
                patch_id="0123456789abcdef",
                kind="remove_required",
                schema_pointer="/components/schemas/Test",
                evidence_count=1,
                impact_count=1,
            ),
        ),
        local_medusa_version="test",
        local_package_json_sha256="e" * 64,
        local_package_lock_sha256="f" * 64,
        evidence_sha256="1" * 64,
        proposed_at=datetime.now(UTC),
    )
    repository.create_contract_revision_proposal(
        owner_key=str(OWNER), proposal=proposal, candidate_bytes=candidate
    )
    revision_id = "revisionopaque01"
    repository.approve_contract_revision(
        owner_key=str(OWNER),
        source_id=parent.source.source_id,
        proposal_id=proposal.proposal_id,
        revision_id=revision_id,
        approved_by_owner_id=str(OWNER),
        approved_at=datetime.now(UTC),
        summary={
            "revision_kind": "reviewed_api_contract",
            "final_canonical_sha256": contract_hash,
            "approved_by_owner_id": str(OWNER),
        },
    )
    profiles = ApiConnectionProfileRepository(repository)
    profile = profiles.create(
        owner_key=str(OWNER),
        source_id=parent.source.source_id,
        profile_name="Local Medusa",
        environment="local",
        base_url="https://example.com",
        authentication_method=ApiAuthenticationMethod.API_KEY,
        credential_name="x-publishable-api-key",
        credential_reference_id=CREDENTIAL,
        credential_version=2,
    )
    return repository, parent.source.source_id, revision_id, profile.id, contract_hash
