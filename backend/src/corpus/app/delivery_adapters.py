from __future__ import annotations

import hashlib
import json

from corpus.features.deployment.domain import EligibleBuild
from corpus.features.deployment.ports import DeploymentConflict
from corpus.features.evaluation.eligibility import current_eligibility


class CorpusEligibilityGateway:
    def __init__(self, repository) -> None:
        self.repository = repository

    async def require_eligible(self, organization_id, agent_id, build_id) -> EligibleBuild:
        value = await self.repository.latest_eligibility(
            organization_id, agent_id, build_id
        )
        cases = []
        runs = []
        for evaluation_set in await self.repository.list_sets(
            organization_id, agent_id
        ):
            if evaluation_set.build_id != build_id:
                continue
            cases.extend(
                await self.repository.cases(organization_id, evaluation_set.id)
            )
            runs.extend(
                await self.repository.runs(organization_id, evaluation_set.id)
            )
        truth = current_eligibility(cases, runs, value)
        if value is None or truth.eligible is not True:
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
