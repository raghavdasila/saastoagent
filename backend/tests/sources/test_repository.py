from __future__ import annotations

from pathlib import Path
from datetime import UTC, datetime
from concurrent.futures import ThreadPoolExecutor
import hashlib
from threading import Event
import time

import pytest

from corpus.features.sources import (
    LocalSourceRepository,
    SourceNotFound,
    SourceState,
)
from corpus.features.sources.models import (
    ContractPatchRecord,
    ContractRevisionProposalRecord,
    ContractRevisionProposalState,
)
from corpus.features.sources.repository import ContractRevisionConflict
import corpus.features.sources.repository as source_repository_module


def test_repository_keeps_owner_sources_isolated_and_revision_paths_opaque(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")

    prepared = repository.begin_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Widgets",
        original_filename="widgets.json",
        content=b'{"openapi":"3.0.3"}',
    )

    assert prepared.input_path.read_bytes() == b'{"openapi":"3.0.3"}'
    assert prepared.artifact_dir.parent.name == prepared.revision.revision_id
    assert "owner-a" not in str(prepared.artifact_dir)
    assert repository.get(
        owner_key="owner-a", source_id=prepared.source.source_id
    ).revision.state is SourceState.QUEUED
    assert repository.list(owner_key="owner-b") == ()
    with pytest.raises(SourceNotFound):
        repository.get(
            owner_key="owner-b", source_id=prepared.source.source_id
        )


def test_repository_atomically_marks_ready_and_failed_revisions(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    ready = repository.begin_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Ready API",
        original_filename="ready.yaml",
        content=b"openapi: 3.0.3",
    )

    repository.mark_running(
        owner_key="owner-a",
        source_id=ready.source.source_id,
        revision_id=ready.revision.revision_id,
    )
    ready_view = repository.mark_ready(
        owner_key="owner-a",
        source_id=ready.source.source_id,
        revision_id=ready.revision.revision_id,
        summary={"endpoint_count": 3},
    )

    assert ready_view.revision.state is SourceState.READY
    assert ready_view.revision.summary == {"endpoint_count": 3}
    assert not tuple((tmp_path / "sources").rglob("*.tmp"))

    failed = repository.begin_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Broken API",
        original_filename="broken.json",
        content=b"{}",
    )
    failed_view = repository.mark_failed(
        owner_key="owner-a",
        source_id=failed.source.source_id,
        revision_id=failed.revision.revision_id,
        failure_code="invalid_api_collection",
        failure_message="No OpenAPI version was declared.",
    )
    assert failed_view.revision.state is SourceState.FAILED
    assert failed_view.revision.failure_code == "invalid_api_collection"


def test_inventory_read_waits_for_source_lifecycle_manifest_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    prepared = repository.begin_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Concurrent API",
        original_filename="concurrent.yaml",
        content=b"openapi: 3.0.3",
    )
    original_write = source_repository_module._write_model_atomic
    mutation_open = Event()
    allow_commit = Event()

    def gapped_revision_commit(path: Path, model) -> None:
        if path.name == "revision.json" and model.state is SourceState.RUNNING:
            path.unlink()
            mutation_open.set()
            if not allow_commit.wait(timeout=2):
                raise TimeoutError("test did not release the lifecycle commit")
        original_write(path, model)

    monkeypatch.setattr(
        source_repository_module, "_write_model_atomic", gapped_revision_commit
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        writer = executor.submit(
            repository.mark_running,
            owner_key="owner-a",
            source_id=prepared.source.source_id,
            revision_id=prepared.revision.revision_id,
        )
        assert mutation_open.wait(timeout=1)
        reader = executor.submit(
            repository.get,
            owner_key="owner-a",
            source_id=prepared.source.source_id,
        )
        time.sleep(0.05)
        try:
            assert not reader.done(), "inventory read crossed an in-flight manifest commit"
        finally:
            allow_commit.set()

        assert writer.result().revision.state is SourceState.RUNNING
        assert reader.result().revision.state is SourceState.RUNNING


def test_new_source_publishes_revision_before_inventory_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    original_write = source_repository_module._write_model_atomic
    source_published = Event()
    allow_create_return = Event()

    def pause_after_source_pointer(path: Path, model) -> None:
        original_write(path, model)
        if path.name == "source.json":
            source_published.set()
            if not allow_create_return.wait(timeout=2):
                raise TimeoutError("test did not release Source creation")

    monkeypatch.setattr(
        source_repository_module, "_write_model_atomic", pause_after_source_pointer
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        creator = executor.submit(
            repository.begin_source,
            owner_key="owner-a",
            connector_key="api",
            display_name="New API",
            original_filename="new.yaml",
            content=b"openapi: 3.0.3",
        )
        assert source_published.wait(timeout=1)
        reader = executor.submit(repository.list, owner_key="owner-a")
        try:
            visible = reader.result(timeout=1)
        finally:
            allow_create_return.set()

        prepared = creator.result()
        assert len(visible) == 1
        assert visible[0].source_id == prepared.source.source_id
        assert visible[0].revision.revision_id == prepared.revision.revision_id


def _ready_source(repository: LocalSourceRepository):
    prepared = repository.begin_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Reviewed API",
        original_filename="medusa_store.yaml",
        content=b"openapi: 3.0.0\n",
    )
    repository.mark_running(
        owner_key="owner-a",
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
    )
    return repository.mark_ready(
        owner_key="owner-a",
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
        summary={"endpoint_count": 1},
    )


def _proposal(source_id: str, parent_revision_id: str):
    now = datetime.now(UTC)
    candidate = b'{"openapi":"3.0.0"}'
    final_hash = hashlib.sha256(candidate).hexdigest()
    return (
        ContractRevisionProposalRecord(
            proposal_id="proposal12345678",
            source_id=source_id,
            parent_revision_id=parent_revision_id,
            state=ContractRevisionProposalState.PENDING,
            source_raw_sha256="1" * 64,
            source_canonical_sha256="2" * 64,
            repair_manifest_sha256="3" * 64,
            repaired_parent_sha256="4" * 64,
            final_canonical_sha256=final_hash,
            patches=(
                ContractPatchRecord(
                    patch_id="6435eb6c5861391b",
                    kind="remove_required",
                    schema_pointer="/components/schemas/BaseRegionCountry",
                    field_name="id",
                    evidence_count=7,
                    impact_count=2,
                ),
            ),
            local_medusa_version="2.13.6",
            local_package_json_sha256="5" * 64,
            local_package_lock_sha256="6" * 64,
            evidence_sha256="7" * 64,
            proposed_at=now,
        ),
        candidate,
    )


def test_contract_revision_approval_advances_once_and_preserves_exact_parent(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    parent = _ready_source(repository)
    proposal, candidate = _proposal(parent.source_id, parent.revision.revision_id)
    repository.create_contract_revision_proposal(
        owner_key="owner-a", proposal=proposal, candidate_bytes=candidate
    )

    approved = repository.approve_contract_revision(
        owner_key="owner-a",
        source_id=parent.source_id,
        proposal_id=proposal.proposal_id,
        revision_id="revision12345678",
        approved_by_owner_id="owner-a",
        approved_at=datetime.now(UTC),
        summary={"revision_kind": "reviewed_api_contract"},
    )

    assert approved.revision.revision_id == "revision12345678"
    assert approved.revision.parent_revision_id == parent.revision.revision_id
    assert approved.revision.artifact_revision_id == parent.revision.revision_id
    assert repository.get_revision(
        owner_key="owner-a",
        source_id=parent.source_id,
        revision_id=parent.revision.revision_id,
    ).revision == parent.revision
    assert repository.artifact_dir(
        owner_key="owner-a", source_id=parent.source_id
    ).parent.name == parent.revision.revision_id
    with pytest.raises(ContractRevisionConflict):
        repository.approve_contract_revision(
            owner_key="owner-a",
            source_id=parent.source_id,
            proposal_id=proposal.proposal_id,
            revision_id="revision76543210",
            approved_by_owner_id="owner-a",
            approved_at=datetime.now(UTC),
            summary={},
        )


def test_contract_revision_manifest_failure_keeps_parent_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    parent = _ready_source(repository)
    proposal, candidate = _proposal(parent.source_id, parent.revision.revision_id)
    repository.create_contract_revision_proposal(
        owner_key="owner-a", proposal=proposal, candidate_bytes=candidate
    )
    original_write = source_repository_module._write_model_atomic

    def fail_source_commit(path, model):
        if path.name == "source.json" and model.current_revision_id == "revision12345678":
            raise OSError("forced manifest commit failure")
        return original_write(path, model)

    monkeypatch.setattr(source_repository_module, "_write_model_atomic", fail_source_commit)
    with pytest.raises(OSError, match="forced manifest"):
        repository.approve_contract_revision(
            owner_key="owner-a",
            source_id=parent.source_id,
            proposal_id=proposal.proposal_id,
            revision_id="revision12345678",
            approved_by_owner_id="owner-a",
            approved_at=datetime.now(UTC),
            summary={},
        )

    current = repository.get(owner_key="owner-a", source_id=parent.source_id)
    assert current.revision.revision_id == parent.revision.revision_id
    assert repository.get_contract_revision_proposal(
        owner_key="owner-a",
        source_id=parent.source_id,
        proposal_id=proposal.proposal_id,
    ).state is ContractRevisionProposalState.PENDING


def test_concurrent_contract_proposals_are_serialized_without_lost_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    parent = _ready_source(repository)
    template, _ = _proposal(parent.source_id, parent.revision.revision_id)
    original_read = repository._read_source

    def delayed_read(path: Path):
        value = original_read(path)
        time.sleep(0.015)
        return value

    monkeypatch.setattr(repository, "_read_source", delayed_read)

    def create(index: int) -> str:
        candidate = f'{{"openapi":"3.0.{index}"}}'.encode()
        proposal = template.model_copy(
            update={
                "proposal_id": f"proposal{index:08d}",
                "final_canonical_sha256": hashlib.sha256(candidate).hexdigest(),
            }
        )
        repository.create_contract_revision_proposal(
            owner_key="owner-a", proposal=proposal, candidate_bytes=candidate
        )
        return proposal.proposal_id

    with ThreadPoolExecutor(max_workers=6) as executor:
        returned = tuple(executor.map(create, range(6)))

    retained = repository.list_contract_revision_proposals(
        owner_key="owner-a", source_id=parent.source_id
    )
    assert {item.proposal_id for item in retained} == set(returned)


def test_concurrent_contract_approval_has_exactly_one_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    parent = _ready_source(repository)
    proposal, candidate = _proposal(parent.source_id, parent.revision.revision_id)
    repository.create_contract_revision_proposal(
        owner_key="owner-a", proposal=proposal, candidate_bytes=candidate
    )
    original_owned_source = repository._owned_source

    def delayed_owned_source(*, owner_key: str, source_id: str):
        value = original_owned_source(owner_key=owner_key, source_id=source_id)
        time.sleep(0.025)
        return value

    monkeypatch.setattr(repository, "_owned_source", delayed_owned_source)

    def approve(revision_id: str) -> str:
        try:
            repository.approve_contract_revision(
                owner_key="owner-a",
                source_id=parent.source_id,
                proposal_id=proposal.proposal_id,
                revision_id=revision_id,
                approved_by_owner_id="owner-a",
                approved_at=datetime.now(UTC),
                summary={"revision_kind": "reviewed_api_contract"},
            )
        except ContractRevisionConflict:
            return "conflict"
        return "approved"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(
            executor.map(approve, ("revision12345678", "revision87654321"))
        )

    assert sorted(results) == ["approved", "conflict"]
    current = repository.get(owner_key="owner-a", source_id=parent.source_id)
    assert current.revision.revision_id in {"revision12345678", "revision87654321"}
    assert repository.get_contract_revision_proposal(
        owner_key="owner-a",
        source_id=parent.source_id,
        proposal_id=proposal.proposal_id,
    ).state is ContractRevisionProposalState.APPROVED


def test_missing_source_contract_mutation_leaves_no_lock_directory(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    proposal, candidate = _proposal("missing000000001", "revision12345678")

    with pytest.raises(SourceNotFound):
        repository.create_contract_revision_proposal(
            owner_key="owner-a", proposal=proposal, candidate_bytes=candidate
        )

    assert not repository._source_dir("owner-a", proposal.source_id).exists()
