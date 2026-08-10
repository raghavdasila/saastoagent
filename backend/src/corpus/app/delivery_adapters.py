from __future__ import annotations

import hashlib
import json

from corpus.features.deployment.domain import EligibleBuild
from corpus.features.deployment.ports import DeploymentConflict


class CorpusEligibilityGateway:
    def __init__(self, repository) -> None:
        self.repository = repository

    async def require_eligible(self, organization_id, agent_id, build_id) -> EligibleBuild:
        value = await self.repository.latest_eligibility(
            organization_id, agent_id, build_id
        )
        if value is None or not value.eligible:
            raise DeploymentConflict(
                "The exact selected build is not eligible for deployment."
            )
        evidence = {
            "eligibility_id": str(value.id),
            "runtime_build_hash": value.runtime_build_hash,
            "supporting_evaluation_run_ids": list(value.supporting_evaluation_run_ids),
        }
        digest = hashlib.sha256(
            json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return EligibleBuild(value.id, value.runtime_build_hash, digest)


__all__ = ["CorpusEligibilityGateway"]
