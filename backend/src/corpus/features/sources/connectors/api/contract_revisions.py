from __future__ import annotations

import uuid
from typing import Protocol

from ...models import ContractRevisionProposalRecord, SourceView


class ApiContractRevisionError(RuntimeError):
    pass


class ApiContractRevisionConflict(ApiContractRevisionError):
    pass


class ApiContractRevisionService(Protocol):
    """Source-owned contract for an explicitly selected acceptance policy."""

    def propose(
        self,
        *,
        owner_id: uuid.UUID,
        source_id: str,
        parent_revision_id: str,
    ) -> ContractRevisionProposalRecord: ...

    def inspect(
        self, *, owner_id: uuid.UUID, source_id: str, proposal_id: str
    ) -> ContractRevisionProposalRecord: ...

    def list(
        self, *, owner_id: uuid.UUID, source_id: str
    ) -> tuple[ContractRevisionProposalRecord, ...]: ...

    def require_pending_current(
        self, *, owner_id: uuid.UUID, source_id: str, proposal_id: str
    ) -> ContractRevisionProposalRecord: ...

    def approve(
        self, *, owner_id: uuid.UUID, source_id: str, proposal_id: str
    ) -> SourceView: ...


def proposal_public_ref(proposal_id: str) -> str:
    return f"contract-proposal-{proposal_id}"


__all__ = [
    "ApiContractRevisionConflict",
    "ApiContractRevisionError",
    "ApiContractRevisionService",
    "proposal_public_ref",
]
