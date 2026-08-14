from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from openapi_core import OpenAPI
from openapi_spec_validator import validate_spec

from corpus.integrations.api_execution._snapshot.contract_revision import (
    ContractPatch,
    PatchKind,
    approve_contract_patches,
    openapi_document_hash,
)
from corpus.integrations.toolrouter.engine.openapi_loader import load_openapi_specs
from corpus.features.sources.connectors.api.contract_revisions import (
    ApiContractRevisionConflict,
    ApiContractRevisionError,
)
from corpus.features.sources.models import (
    ContractPatchRecord,
    ContractRevisionProposalRecord,
    ContractRevisionProposalState,
    SourceState,
    SourceView,
    utc_now,
)
from corpus.features.sources.repository import (
    ContractRevisionConflict,
    LocalSourceRepository,
    SourceNotReady,
)


@dataclass(frozen=True)
class ApprovedPatchPlan:
    patch_id: str
    kind: PatchKind
    schema_pointer: str
    field_name: str | None
    evidence_count: int
    impact_count: int = 1
    operation_id: str = "CreateCart"
    instance_path: str = "/"
    before_schema: Mapping[str, object] | None = None
    replacement_schema: Mapping[str, object] | None = None
    target_hash: str | None = None

    def runtime_patch(self) -> ContractPatch:
        return ContractPatch(
            patch_id=self.patch_id,
            kind=self.kind,
            operation_id=self.operation_id,
            status_code=200,
            media_type="application/json",
            instance_path=self.instance_path,
            schema_pointer=self.schema_pointer,
            field_name=self.field_name,
            observed="reviewed local Medusa evidence",
            declared="official-current Medusa Store contract",
            proposed=self.kind.value,
            evidence_count=self.evidence_count,
            before_schema=self.before_schema,
            replacement_schema=self.replacement_schema,
            target_hash=self.target_hash,
            impact_count=self.impact_count,
        )

    def record(self) -> ContractPatchRecord:
        return ContractPatchRecord(
            patch_id=self.patch_id,
            kind=self.kind.value,
            schema_pointer=self.schema_pointer,
            field_name=self.field_name,
            evidence_count=self.evidence_count,
            impact_count=self.impact_count,
        )


@dataclass(frozen=True)
class EffectiveContractPlan:
    source_raw_sha256: str
    source_canonical_sha256: str
    repair_manifest_sha256: str
    repaired_parent_sha256: str
    final_canonical_sha256: str
    local_medusa_version: str
    local_package_json_sha256: str
    local_package_lock_sha256: str
    evidence_sha256: str
    patches: tuple[ApprovedPatchPlan, ...]


@dataclass(frozen=True)
class PreparedContractCandidate:
    proposal: ContractRevisionProposalRecord
    candidate_bytes: bytes


MEDUSA_EFFECTIVE_CONTRACT_PLAN = EffectiveContractPlan(
    source_raw_sha256="fd17273078c222a5632459f67204cbc9cf03cb925641d47669209baa9cc97fb6",
    source_canonical_sha256="a3dbb864bef80085e5600496784fc908bf3ea5791de97043f48397d812ad4f87",
    repair_manifest_sha256="dc712d7c172a8e6c3ee2fef8aa11c4f337d0c1622330df521dcf89c6fda19af2",
    repaired_parent_sha256="bc1b4b2456eefab4684a07ffa6e63f652118f5a705dd13eba5d77e74ab965c6e",
    final_canonical_sha256="c0b9c6bf1b149a0e458de9fbda4f7bad3cf6f9f7eb4ff383bded3b09d23e50ef",
    local_medusa_version="2.13.6",
    local_package_json_sha256="798ddcda5807af7667b0892586386056a9c1c1ec4367a085722385c5980a99ab",
    local_package_lock_sha256="540ad6d63416365a54a624302d17c9a544a57a16903d590cbcade8a46dae34e4",
    evidence_sha256="eb250633572df3a6eee25f06998858dc1ff18461a07c1a7c89263879a8af3e3f",
    patches=(
        ApprovedPatchPlan("0e3ca203c694b3ea", PatchKind.SET_NULLABLE, "/components/schemas/StoreCart/properties/billing_address", None, 1),
        ApprovedPatchPlan("0b580a91a8f44b89", PatchKind.SET_NULLABLE, "/components/schemas/StoreCart/properties/completed_at", None, 1),
        ApprovedPatchPlan("79b18616b26c149a", PatchKind.SET_NULLABLE, "/components/schemas/StoreCart/properties/customer_id", None, 1),
        ApprovedPatchPlan("40e01e7194d00a7d", PatchKind.SET_NULLABLE, "/components/schemas/StoreCart/properties/email", None, 1),
        ApprovedPatchPlan("092ef91c4b3d772b", PatchKind.SET_NULLABLE, "/components/schemas/StoreCart/properties/metadata", None, 1),
        ApprovedPatchPlan("c974401b1bfc59b3", PatchKind.SET_NULLABLE, "/components/schemas/StoreCart/properties/shipping_address", None, 1),
        ApprovedPatchPlan("6435eb6c5861391b", PatchKind.REMOVE_REQUIRED, "/components/schemas/BaseRegionCountry", "id", 7, 2),
        ApprovedPatchPlan("2e3008cbf6b3f5b2", PatchKind.REMOVE_REQUIRED, "/components/schemas/StoreCart", "original_subtotal", 1),
        ApprovedPatchPlan("edcb5d80e92f57a1", PatchKind.REMOVE_REQUIRED, "/components/schemas/StoreCart", "gift_card_total", 1),
        ApprovedPatchPlan("3f4de4aa354d0324", PatchKind.REMOVE_REQUIRED, "/components/schemas/StoreCart", "gift_card_tax_total", 1),
        ApprovedPatchPlan(
            "fe22ecc628158a9b",
            PatchKind.CUSTOM_SCHEMA,
            "/paths/~1store~1products/get/responses/200/content/application~1json/schema",
            None,
            1,
            operation_id="GetProducts",
            before_schema={"$ref": "#/components/schemas/StoreProductListResponse"},
            replacement_schema={
                "type": "object",
                "required": ["products", "count", "offset", "limit"],
                "additionalProperties": True,
                "properties": {
                    "products": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "title", "variants"],
                            "additionalProperties": True,
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "variants": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["id"],
                                        "additionalProperties": True,
                                        "properties": {"id": {"type": "string"}},
                                    },
                                },
                            },
                        },
                    },
                    "count": {"type": "integer"},
                    "offset": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
            },
            target_hash="23e40838ada9b1b8170cc2c5c94597bd595ece2017dc476f67ed7d189053c66c",
        ),
        ApprovedPatchPlan(
            "b183ac24f1a1a683",
            PatchKind.CUSTOM_SCHEMA,
            "/paths/~1store~1carts~1{id}~1line-items/post/responses/200/content/application~1json/schema",
            None,
            1,
            operation_id="PostCartsIdLineItems",
            before_schema={"$ref": "#/components/schemas/StoreCartResponse"},
            replacement_schema={
                "type": "object",
                "required": ["cart"],
                "additionalProperties": True,
                "properties": {
                    "cart": {
                        "type": "object",
                        "required": ["id", "items"],
                        "additionalProperties": True,
                        "properties": {
                            "id": {"type": "string"},
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id", "variant_id", "quantity"],
                                    "additionalProperties": True,
                                    "properties": {
                                        "id": {"type": "string"},
                                        "variant_id": {"type": "string"},
                                        "quantity": {"type": "integer"},
                                    },
                                },
                            },
                        },
                    }
                },
            },
            target_hash="1657825eb69f1a6e757766e7696bea8f57155b56718f255d471dd4b7231cf0eb",
        ),
    ),
)


class MedusaContractAcceptanceAdapter:
    """Create and approve one immutable, locally validated API version update.

    This service performs document validation and filesystem persistence only. It
    has no transport dependency and cannot call the target API.
    """

    def __init__(
        self,
        repository: LocalSourceRepository,
        *,
        plan: EffectiveContractPlan = MEDUSA_EFFECTIVE_CONTRACT_PLAN,
    ) -> None:
        self.repository = repository
        self.plan = plan

    def propose(
        self,
        *,
        owner_id: uuid.UUID,
        source_id: str,
        parent_revision_id: str,
    ) -> ContractRevisionProposalRecord:
        owner_key = str(owner_id)
        source = self.repository.get(owner_key=owner_key, source_id=source_id)
        if source.connector_key != "api" or source.revision.state is not SourceState.READY:
            raise SourceNotReady("Only a ready API Source can propose an API version update.")
        if source.revision.revision_id != parent_revision_id:
            raise ApiContractRevisionConflict(
                "The selected Source revision is no longer current. Reload before proposing."
            )
        prepared = self._prepare_candidate(source=source, owner_key=owner_key)
        try:
            return self.repository.create_contract_revision_proposal(
                owner_key=owner_key,
                proposal=prepared.proposal,
                candidate_bytes=prepared.candidate_bytes,
            )
        except ContractRevisionConflict as error:
            raise ApiContractRevisionConflict(str(error)) from error

    def inspect(
        self, *, owner_id: uuid.UUID, source_id: str, proposal_id: str
    ) -> ContractRevisionProposalRecord:
        return self.repository.get_contract_revision_proposal(
            owner_key=str(owner_id), source_id=source_id, proposal_id=proposal_id
        )

    def list(
        self, *, owner_id: uuid.UUID, source_id: str
    ) -> tuple[ContractRevisionProposalRecord, ...]:
        return self.repository.list_contract_revision_proposals(
            owner_key=str(owner_id), source_id=source_id
        )

    def require_pending_current(
        self, *, owner_id: uuid.UUID, source_id: str, proposal_id: str
    ) -> ContractRevisionProposalRecord:
        proposal = self.inspect(
            owner_id=owner_id, source_id=source_id, proposal_id=proposal_id
        )
        source = self.repository.get(owner_key=str(owner_id), source_id=source_id)
        if proposal.state is not ContractRevisionProposalState.PENDING:
            raise ApiContractRevisionConflict("The API update is no longer pending.")
        if source.revision.revision_id != proposal.parent_revision_id:
            raise ApiContractRevisionConflict(
                "The Source changed after this API update was created."
            )
        self._assert_recorded_plan(proposal)
        return proposal

    def approve(
        self, *, owner_id: uuid.UUID, source_id: str, proposal_id: str
    ) -> SourceView:
        proposal = self.require_pending_current(
            owner_id=owner_id, source_id=source_id, proposal_id=proposal_id
        )
        approved_at = utc_now()
        revision_id = secrets.token_urlsafe(12)
        summary: dict[str, object] = {
            "revision_kind": "reviewed_api_contract",
            "source_raw_sha256": proposal.source_raw_sha256,
            "source_canonical_sha256": proposal.source_canonical_sha256,
            "repair_manifest_sha256": proposal.repair_manifest_sha256,
            "repaired_parent_sha256": proposal.repaired_parent_sha256,
            "final_canonical_sha256": proposal.final_canonical_sha256,
            "ordered_patch_ids": [item.patch_id for item in proposal.patches],
            "approved_by_owner_id": str(owner_id),
            "approved_at": approved_at.isoformat(),
            "local_medusa_version": proposal.local_medusa_version,
            "local_package_json_sha256": proposal.local_package_json_sha256,
            "local_package_lock_sha256": proposal.local_package_lock_sha256,
            "evidence_sha256": proposal.evidence_sha256,
            "toolrouter_artifact_revision_id": proposal.parent_revision_id,
        }
        try:
            return self.repository.approve_contract_revision(
                owner_key=str(owner_id),
                source_id=source_id,
                proposal_id=proposal_id,
                revision_id=revision_id,
                approved_by_owner_id=str(owner_id),
                approved_at=approved_at,
                summary=summary,
            )
        except ContractRevisionConflict as error:
            raise ApiContractRevisionConflict(str(error)) from error

    def _prepare_candidate(
        self, *, source: SourceView, owner_key: str
    ) -> PreparedContractCandidate:
        path = self.repository.input_path(owner_key=owner_key, source_id=source.source_id)
        if hashlib.sha256(path.read_bytes()).hexdigest() != self.plan.source_raw_sha256:
            raise ApiContractRevisionConflict(
                "This Source does not match the reviewed API definition."
            )
        bundle = load_openapi_specs((path,))
        if len(bundle.raw_specs) != 1 or len(bundle.repaired_specs) != 1:
            raise ApiContractRevisionError("The API definition normalization result is invalid.")
        source_name = next(iter(bundle.raw_specs))
        raw = bundle.raw_specs[source_name]
        repaired = bundle.repaired_specs[source_name]
        raw_hash = openapi_document_hash(raw)
        repaired_hash = openapi_document_hash(repaired)
        repair_manifest_hash = _json_hash(bundle.repair_manifest)
        if (
            raw_hash != self.plan.source_canonical_sha256
            or repaired_hash != self.plan.repaired_parent_sha256
            or repair_manifest_hash != self.plan.repair_manifest_sha256
        ):
            raise ApiContractRevisionConflict(
                "The normalized Source no longer matches the reviewed API version chain."
            )
        runtime_patches = tuple(item.runtime_patch() for item in self.plan.patches)
        revision = approve_contract_patches(
            repaired,
            runtime_patches,
            approved_patch_ids=(item.patch_id for item in self.plan.patches),
            approved_by="pending-owner-review",
            source_hash=raw_hash,
            parent_hash=repaired_hash,
        )
        validate_spec(revision.document)
        OpenAPI.from_dict(dict(revision.document))
        if revision.revision_hash != self.plan.final_canonical_sha256:
            raise ApiContractRevisionConflict(
                "The derived API definition no longer matches the reviewed final hash."
            )
        candidate_bytes = json.dumps(
            revision.document, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        proposal = ContractRevisionProposalRecord(
            proposal_id=secrets.token_urlsafe(12),
            source_id=source.source_id,
            parent_revision_id=source.revision.revision_id,
            state=ContractRevisionProposalState.PENDING,
            source_raw_sha256=self.plan.source_raw_sha256,
            source_canonical_sha256=raw_hash,
            repair_manifest_sha256=repair_manifest_hash,
            repaired_parent_sha256=repaired_hash,
            final_canonical_sha256=revision.revision_hash,
            patches=tuple(item.record() for item in self.plan.patches),
            local_medusa_version=self.plan.local_medusa_version,
            local_package_json_sha256=self.plan.local_package_json_sha256,
            local_package_lock_sha256=self.plan.local_package_lock_sha256,
            evidence_sha256=self.plan.evidence_sha256,
            proposed_at=utc_now(),
        )
        return PreparedContractCandidate(proposal=proposal, candidate_bytes=candidate_bytes)

    def _assert_recorded_plan(self, proposal: ContractRevisionProposalRecord) -> None:
        expected = (
            self.plan.source_raw_sha256,
            self.plan.source_canonical_sha256,
            self.plan.repair_manifest_sha256,
            self.plan.repaired_parent_sha256,
            self.plan.final_canonical_sha256,
            self.plan.local_medusa_version,
            self.plan.local_package_json_sha256,
            self.plan.local_package_lock_sha256,
            self.plan.evidence_sha256,
            tuple(item.record() for item in self.plan.patches),
        )
        actual = (
            proposal.source_raw_sha256,
            proposal.source_canonical_sha256,
            proposal.repair_manifest_sha256,
            proposal.repaired_parent_sha256,
            proposal.final_canonical_sha256,
            proposal.local_medusa_version,
            proposal.local_package_json_sha256,
            proposal.local_package_lock_sha256,
            proposal.evidence_sha256,
            proposal.patches,
        )
        if actual != expected:
            raise ApiContractRevisionConflict(
                "The persisted proposal no longer matches the reviewed API update plan."
            )


def proposal_public_ref(proposal_id: str) -> str:
    return f"contract-proposal-{proposal_id}"


def _json_hash(value: Mapping[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


__all__ = [
    "ApiContractRevisionConflict",
    "ApiContractRevisionError",
    "MedusaContractAcceptanceAdapter",
    "ApprovedPatchPlan",
    "EffectiveContractPlan",
    "MEDUSA_EFFECTIVE_CONTRACT_PLAN",
    "proposal_public_ref",
]
