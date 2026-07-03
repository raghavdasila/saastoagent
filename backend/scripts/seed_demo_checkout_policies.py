from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from backend.core.database import async_session
from backend.core.models import AgentLearningCandidate, SaaSAgent, User


def _load_request() -> dict[str, Any]:
    file_path = os.environ.get("DEMO_POLICY_SEED_FILE")
    if file_path:
        with open(file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    raw = os.environ.get("DEMO_POLICY_SEED_JSON")
    if not raw:
        raise SystemExit("DEMO_POLICY_SEED_JSON or DEMO_POLICY_SEED_FILE is required")
    return json.loads(raw)


async def _seed() -> dict[str, Any]:
    request = _load_request()
    agent_id = uuid.UUID(str(request["agentId"]))
    owner_email = str(request.get("ownerEmail") or "")
    policies = request.get("policies") or []
    if not isinstance(policies, list) or not policies:
        raise SystemExit("seed request has no policies")

    async with async_session() as session:
        agent = await session.get(SaaSAgent, agent_id)
        if agent is None:
            raise SystemExit(f"SaaS Agent not found: {agent_id}")

        reviewed_by = None
        if owner_email:
            reviewed_by = (
                await session.execute(select(User.id).where(User.email == owner_email))
            ).scalar_one_or_none()

        existing_result = await session.execute(
            select(AgentLearningCandidate).where(
                AgentLearningCandidate.saas_agent_id == agent_id,
                AgentLearningCandidate.trigger_type == "domain_policy_gap",
                AgentLearningCandidate.status.in_(["approved", "active"]),
            )
        )
        existing_allowed = {
            tuple(sorted(map(str, (candidate.evidence or {}).get("allowed_action_paths") or [])))
            for candidate in existing_result.scalars().all()
        }

        inserted = []
        skipped = []
        now = datetime.now(timezone.utc)
        for policy in policies:
            allowed_paths = [str(path) for path in policy.get("allowed_action_paths") or [] if str(path)]
            if not allowed_paths:
                continue
            key = tuple(sorted(allowed_paths))
            target_path = str(policy.get("target_action_path") or allowed_paths[-1])
            if key in existing_allowed:
                skipped.append({"target_action_path": target_path, "allowed_action_paths": allowed_paths})
                continue
            candidate = AgentLearningCandidate(
                saas_agent_id=agent_id,
                trigger_type="domain_policy_gap",
                status="approved",
                title=str(policy.get("title") or "Approved visitor checkout policy"),
                summary="Demo setup approved this known Medusa checkout action chain after the visible Learning approval.",
                hint_text="Allow this generated action chain for the recorded Medusa checkout demo.",
                target_tool_name="Medusa Store API generated action",
                target_action_path=target_path,
                target_risk_level=str(policy.get("target_risk_level") or "write"),
                evidence={
                    "policy_kind": "internal_dependency_write",
                    "public_channel": True,
                    "reason": "Seeded for the recorded demo after one visible owner Learning approval.",
                    "allowed_action_paths": allowed_paths,
                    "requested_action_path": target_path,
                    "source": "record-chat-first-final",
                },
                reviewed_by=reviewed_by,
                reviewed_at=now,
            )
            session.add(candidate)
            inserted.append({"target_action_path": target_path, "allowed_action_paths": allowed_paths})
            existing_allowed.add(key)

        await session.commit()
        return {
            "ok": True,
            "agent_id": str(agent_id),
            "owner_email": owner_email,
            "inserted": inserted,
            "skipped": skipped,
        }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(_seed()), indent=2))
