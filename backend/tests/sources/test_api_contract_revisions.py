from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest

from corpus.features.sources.connectors.api.contract_revisions import (
    ApiContractRevisionConflict,
    ApiContractRevisionService,
    ApprovedPatchPlan,
    EffectiveContractPlan,
    MEDUSA_EFFECTIVE_CONTRACT_PLAN,
)
from corpus.features.sources.models import ContractRevisionProposalState, SourceState
from corpus.features.sources.repository import LocalSourceRepository, SourceNotFound
from corpus.integrations.api_execution._snapshot.contract_revision import (
    PatchKind,
    approve_contract_patches,
    openapi_document_hash,
)
from corpus.features.sources.connectors.api.toolrouter import load_api_contract_documents


OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_OWNER = uuid.UUID("00000000-0000-0000-0000-000000000002")


def _ready_fixture(tmp_path: Path):
    path = tmp_path / "reviewed_store.yaml"
    path.write_text(
        """openapi: 3.0.0
info:
  title: Reviewed Store
  version: 1.0.0
paths:
  /cart:
    get:
      operationId: CreateCart
      responses:
        '200':
          description: ok
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StoreCart'
components:
  schemas:
    StoreCart:
      type: object
      required: [id]
      properties:
        id:
          type: string
""",
        encoding="utf-8",
    )
    repository = LocalSourceRepository(tmp_path / "sources")
    prepared = repository.begin_source(
        owner_key=str(OWNER),
        connector_key="api",
        display_name="Reviewed Store",
        original_filename=path.name,
        content=path.read_bytes(),
    )
    repository.mark_running(
        owner_key=str(OWNER),
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
    )
    source = repository.mark_ready(
        owner_key=str(OWNER),
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
        summary={"endpoint_count": 1},
    )
    bundle = load_api_contract_documents(prepared.input_path)
    name = next(iter(bundle.raw_specs))
    raw = bundle.raw_specs[name]
    repaired = bundle.repaired_specs[name]
    patch = ApprovedPatchPlan(
        patch_id="0123456789abcdef",
        kind=PatchKind.REMOVE_REQUIRED,
        schema_pointer="/components/schemas/StoreCart",
        field_name="id",
        evidence_count=2,
        impact_count=1,
    )
    revision = approve_contract_patches(
        repaired,
        (patch.runtime_patch(),),
        approved_patch_ids=(patch.patch_id,),
        approved_by="test-review",
        source_hash=openapi_document_hash(raw),
        parent_hash=openapi_document_hash(repaired),
    )
    plan = EffectiveContractPlan(
        source_raw_sha256=hashlib.sha256(prepared.input_path.read_bytes()).hexdigest(),
        source_canonical_sha256=openapi_document_hash(raw),
        repair_manifest_sha256=hashlib.sha256(
            json.dumps(
                bundle.repair_manifest, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest(),
        repaired_parent_sha256=openapi_document_hash(repaired),
        final_canonical_sha256=revision.revision_hash,
        local_medusa_version="test",
        local_package_json_sha256="a" * 64,
        local_package_lock_sha256="b" * 64,
        evidence_sha256="c" * 64,
        patches=(patch,),
    )
    return repository, source, plan


def test_exact_medusa_plan_retains_ordered_reviewed_chain_and_shared_impact() -> None:
    plan = MEDUSA_EFFECTIVE_CONTRACT_PLAN
    assert plan.repaired_parent_sha256 == "bc1b4b2456eefab4684a07ffa6e63f652118f5a705dd13eba5d77e74ab965c6e"
    assert plan.final_canonical_sha256 == "6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6"
    assert [item.patch_id for item in plan.patches] == [
        "0e3ca203c694b3ea",
        "0b580a91a8f44b89",
        "79b18616b26c149a",
        "40e01e7194d00a7d",
        "092ef91c4b3d772b",
        "c974401b1bfc59b3",
        "6435eb6c5861391b",
        "2e3008cbf6b3f5b2",
        "edcb5d80e92f57a1",
        "3f4de4aa354d0324",
    ]
    shared = next(item for item in plan.patches if item.patch_id == "6435eb6c5861391b")
    assert shared.schema_pointer == "/components/schemas/BaseRegionCountry"
    assert shared.field_name == "id"
    assert shared.impact_count == 2


def test_proposal_and_approval_are_owner_scoped_immutable_and_transport_free(
    tmp_path: Path,
) -> None:
    repository, source, plan = _ready_fixture(tmp_path)
    service = ApiContractRevisionService(repository, plan=plan)

    proposal = service.propose(
        owner_id=OWNER,
        source_id=source.source_id,
        parent_revision_id=source.revision.revision_id,
    )

    assert proposal.state is ContractRevisionProposalState.PENDING
    assert proposal.parent_revision_id == source.revision.revision_id
    assert tuple(item.patch_id for item in proposal.patches) == ("0123456789abcdef",)
    with pytest.raises(ApiContractRevisionConflict, match="already proposed"):
        service.propose(
            owner_id=OWNER,
            source_id=source.source_id,
            parent_revision_id=source.revision.revision_id,
        )
    with pytest.raises(SourceNotFound):
        service.inspect(
            owner_id=OTHER_OWNER,
            source_id=source.source_id,
            proposal_id=proposal.proposal_id,
        )

    approved = service.approve(
        owner_id=OWNER,
        source_id=source.source_id,
        proposal_id=proposal.proposal_id,
    )

    assert approved.revision.state is SourceState.READY
    assert approved.revision.parent_revision_id == source.revision.revision_id
    assert approved.revision.summary["ordered_patch_ids"] == ["0123456789abcdef"]
    assert approved.revision.summary["approved_by_owner_id"] == str(OWNER)
    assert repository.get_revision(
        owner_key=str(OWNER),
        source_id=source.source_id,
        revision_id=source.revision.revision_id,
    ).revision == source.revision
    with pytest.raises(ApiContractRevisionConflict, match="no longer pending"):
        service.approve(
            owner_id=OWNER,
            source_id=source.source_id,
            proposal_id=proposal.proposal_id,
        )


def test_accept_time_recheck_rejects_persisted_patch_provenance_drift(
    tmp_path: Path,
) -> None:
    repository, source, plan = _ready_fixture(tmp_path)
    service = ApiContractRevisionService(repository, plan=plan)
    proposal = service.propose(
        owner_id=OWNER,
        source_id=source.source_id,
        parent_revision_id=source.revision.revision_id,
    )
    source_path = next((tmp_path / "sources").rglob(f"{source.source_id}/source.json"))
    persisted = json.loads(source_path.read_text(encoding="utf-8"))
    persisted["contract_revision_proposals"][0]["local_medusa_version"] = "falsified"
    persisted["contract_revision_proposals"][0]["patches"][0]["impact_count"] = 99
    source_path.write_text(json.dumps(persisted), encoding="utf-8")

    with pytest.raises(ApiContractRevisionConflict, match="reviewed contract plan"):
        service.require_pending_current(
            owner_id=OWNER,
            source_id=source.source_id,
            proposal_id=proposal.proposal_id,
        )
    assert repository.get(
        owner_key=str(OWNER), source_id=source.source_id
    ).revision.revision_id == source.revision.revision_id
