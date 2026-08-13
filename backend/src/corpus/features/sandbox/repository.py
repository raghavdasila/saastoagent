from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from corpus.persistence import CorpusDatabase

from .domain import RuntimeSandboxRun, SandboxRecord
from .models import AgentSandboxRun, AgentSandboxSession
from .ports import SandboxUnavailable


class SqlAlchemySandboxRepository:
    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def begin(self, organization_id, agent_id, *, build, message):
        now = datetime.now(UTC)
        session_id, run_id = uuid.uuid4(), uuid.uuid4()
        runtime_session_id, runtime_run_id = str(session_id), str(run_id)
        async with self.database.session() as db:
            async with db.begin():
                session = AgentSandboxSession(
                    id=session_id, organization_id=organization_id, agent_id=agent_id,
                    build_id=build.id, runtime_session_id=runtime_session_id, created_at=now,
                )
                run = AgentSandboxRun(
                    id=run_id, session_id=session_id, organization_id=organization_id,
                    agent_id=agent_id, build_id=build.id, runtime_build_hash=build.runtime_build_hash,
                    runtime_run_id=runtime_run_id, status="running", message=message, awaiting=None,
                    final_response=None, api_call_count=0, safe_events=[], routedeck_projection={}, failure_code=None,
                    created_at=now, updated_at=now,
                )
                db.add(session)
                await db.flush()
                db.add(run)
                await db.flush()
                return _record(run, session.runtime_session_id)

    async def complete(self, organization_id, record_id, result):
        async with self.database.session() as db:
            async with db.begin():
                run, session = await _locked(db, organization_id, record_id)
                if run.status != "running" or result.runtime_run_id != run.runtime_run_id:
                    raise SandboxUnavailable("The Sandbox run identity changed before completion.")
                run.status, run.awaiting, run.final_response = result.status, result.awaiting, result.final_response
                run.api_call_count, run.safe_events = result.api_call_count, list(result.safe_events)
                run.routedeck_projection = result.routedeck_projection
                run.updated_at = datetime.now(UTC)
                await db.flush()
                return _record(run, session.runtime_session_id)

    async def begin_resume(self, organization_id, agent_id, record_id):
        async with self.database.session() as db:
            async with db.begin():
                run, session = await _locked(db, organization_id, record_id)
                if run.agent_id != agent_id or run.status != "waiting" or not run.awaiting:
                    raise SandboxUnavailable("The Sandbox run is not waiting for clarification.")
                # Keep the exact waiting reason on the returned locked record. The
                # durable row moves to running only after the caller has captured it.
                waiting_reason = run.awaiting
                run.status, run.awaiting, run.updated_at = "running", None, datetime.now(UTC)
                await db.flush()
                value = _record(run, session.runtime_session_id)
                return SandboxRecord(
                    value.id, value.organization_id, value.agent_id, value.build_id,
                    value.runtime_build_hash, value.runtime_session_id,
                    value.runtime_run_id, value.status, waiting_reason,
                    value.final_response, value.api_call_count, value.safe_events,
                    value.routedeck_projection, value.failure_code,
                    value.created_at, value.updated_at, value.message,
                )

    async def fail(self, organization_id, record_id, *, code):
        async with self.database.session() as db:
            async with db.begin():
                run, session = await _locked(db, organization_id, record_id)
                run.status, run.failure_code, run.updated_at = "failed", code[:80], datetime.now(UTC)
                await db.flush()
                return _record(run, session.runtime_session_id)

    async def list(self, organization_id, agent_id):
        async with self.database.session() as db:
            rows = (await db.execute(select(AgentSandboxRun, AgentSandboxSession).join(
                AgentSandboxSession, AgentSandboxSession.id == AgentSandboxRun.session_id,
            ).where(
                AgentSandboxRun.organization_id == organization_id,
                AgentSandboxRun.agent_id == agent_id,
            ).order_by(AgentSandboxRun.created_at.desc()))).all()
        return tuple(_record(run, session.runtime_session_id) for run, session in rows)


async def _locked(db, organization_id, record_id):
    row = (await db.execute(select(AgentSandboxRun, AgentSandboxSession).join(
        AgentSandboxSession, AgentSandboxSession.id == AgentSandboxRun.session_id,
    ).where(
        AgentSandboxRun.organization_id == organization_id,
        AgentSandboxRun.id == record_id,
    ).with_for_update())).one_or_none()
    if row is None:
        raise SandboxUnavailable("The Sandbox run is unavailable.")
    return row


def _record(run, runtime_session_id):
    return SandboxRecord(
        run.id, run.organization_id, run.agent_id, run.build_id, run.runtime_build_hash,
        runtime_session_id, run.runtime_run_id, run.status, run.awaiting, run.final_response,
        run.api_call_count, tuple(dict(item) for item in run.safe_events), dict(run.routedeck_projection), run.failure_code,
        run.created_at, run.updated_at, run.message,
    )


__all__ = ["SqlAlchemySandboxRepository"]
