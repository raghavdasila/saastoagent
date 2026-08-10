from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from corpus.features.sources.connectors.api.routed_executions import (
    ApiRoutedExecutionClaim,
    ApiRoutedExecutionConflict,
    ApiRoutedExecutionRepository,
    ApiRoutedExecutionResult,
)
from corpus.features.sources.repository import LocalSourceRepository


OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_claim_is_single_use_and_same_request_replays_exact_terminal_result(
    tmp_path: Path,
) -> None:
    sources, source_id, revision_id = _source(tmp_path)
    repository = ApiRoutedExecutionRepository(sources, boot_id="boot-a")
    claim = _claim(source_id, revision_id, request_id="request-00000001", boot_id="boot-a")

    assert repository.begin(owner_key=str(OWNER), claim=claim) == (claim, None)
    with pytest.raises(ApiRoutedExecutionConflict, match="already in progress"):
        repository.begin(owner_key=str(OWNER), claim=claim)
    with pytest.raises(ApiRoutedExecutionConflict, match="already consumed"):
        repository.begin(
            owner_key=str(OWNER),
            claim=claim.model_copy(update={"request_id": "request-00000002"}),
        )

    result = _result(claim)
    assert repository.complete(owner_key=str(OWNER), result=result) == result
    assert repository.begin(owner_key=str(OWNER), claim=claim) == (claim, result)
    with pytest.raises(ApiRoutedExecutionConflict, match="already has a result"):
        repository.complete(owner_key=str(OWNER), result=result)


def test_interrupted_write_claim_recovers_unknown_without_another_call(
    tmp_path: Path,
) -> None:
    sources, source_id, revision_id = _source(tmp_path)
    first = ApiRoutedExecutionRepository(sources, boot_id="boot-a")
    claim = _claim(source_id, revision_id, request_id="request-00000001", boot_id="boot-a")
    assert first.begin(owner_key=str(OWNER), claim=claim)[1] is None

    restarted = ApiRoutedExecutionRepository(sources, boot_id="boot-b")
    existing, recovered = restarted.begin(
        owner_key=str(OWNER),
        claim=claim.model_copy(update={"boot_id": "boot-b"}),
    )

    assert existing.boot_id == "boot-a"
    assert recovered is not None
    assert recovered.status == "outcome_unknown"
    assert recovered.delivery == "possibly_sent"
    assert recovered.error_code == "execution_interrupted"
    assert recovered.http_call_count is None
    assert restarted.begin(
        owner_key=str(OWNER),
        claim=claim.model_copy(update={"boot_id": "boot-b"}),
    )[1] == recovered


def test_interrupted_read_claim_fails_with_unknown_call_count_and_no_retry(
    tmp_path: Path,
) -> None:
    sources, source_id, revision_id = _source(tmp_path)
    first = ApiRoutedExecutionRepository(sources, boot_id="boot-a")
    claim = _claim(
        source_id,
        revision_id,
        request_id="request-00000001",
        boot_id="boot-a",
    ).model_copy(
        update={
            "operation_id": "GetProductTypes",
            "method": "GET",
            "path_template": "/store/product-types",
            "safety": "read",
        }
    )
    assert first.begin(owner_key=str(OWNER), claim=claim)[1] is None

    restarted = ApiRoutedExecutionRepository(sources, boot_id="boot-b")
    _, recovered = restarted.begin(
        owner_key=str(OWNER),
        claim=claim.model_copy(update={"boot_id": "boot-b"}),
    )

    assert recovered is not None
    assert recovered.status == "failed"
    assert recovered.delivery == "possibly_sent"
    assert recovered.http_call_count is None
    assert recovered.public_message == "The API read was interrupted and was not retried."


def _source(tmp_path: Path) -> tuple[LocalSourceRepository, str, str]:
    sources = LocalSourceRepository(tmp_path / "sources")
    prepared = sources.begin_source(
        owner_key=str(OWNER),
        connector_key="api",
        display_name="API",
        original_filename="api.json",
        content=b"{}",
    )
    return sources, prepared.source.source_id, prepared.revision.revision_id


def _claim(
    source_id: str,
    revision_id: str,
    *,
    request_id: str,
    boot_id: str,
) -> ApiRoutedExecutionClaim:
    return ApiRoutedExecutionClaim(
        claim_id="claimopaque00001",
        request_id=request_id,
        boot_id=boot_id,
        owner_id=OWNER,
        conversation_id="conversation-owner-a",
        route_session_id="route-session-owner-a",
        plan_id="planopaque000001",
        plan_record_id="recordopaque0001",
        plan_fingerprint="a" * 64,
        source_id=source_id,
        source_revision_id=revision_id,
        operation_id="CreateCart",
        method="POST",
        path_template="/store/carts",
        safety="write",
        created_at=datetime.now(UTC),
    )


def _result(claim: ApiRoutedExecutionClaim) -> ApiRoutedExecutionResult:
    now = datetime.now(UTC)
    return ApiRoutedExecutionResult(
        result_id="resultopaque0001",
        claim_id=claim.claim_id,
        request_id=claim.request_id,
        owner_id=claim.owner_id,
        conversation_id=claim.conversation_id,
        route_session_id=claim.route_session_id,
        plan_id=claim.plan_id,
        plan_record_id=claim.plan_record_id,
        plan_fingerprint=claim.plan_fingerprint,
        source_id=claim.source_id,
        source_revision_id=claim.source_revision_id,
        operation_id=claim.operation_id,
        method=claim.method,
        path_template=claim.path_template,
        safety=claim.safety,
        status="succeeded",
        delivery="response_received",
        status_code=200,
        response_media_type="application/json",
        response_byte_count=17,
        response_body_sha256="b" * 64,
        validation_issue_count=0,
        validation_phases=(),
        outcome_verified=None,
        http_call_count=1,
        started_at=now,
        finished_at=now,
        traces=(),
    )
