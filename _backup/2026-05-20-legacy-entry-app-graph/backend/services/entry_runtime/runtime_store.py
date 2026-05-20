from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import EntryArtifact, EntryOutput, EntryRun, EntrySession, EntryStage, User

ENTRY_SESSION_COOKIE = "sta_v01_entry_session"
ENTRY_SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 7


class EntryRuntimeStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session(self, session_id: uuid.UUID) -> EntrySession | None:
        return await self.db.get(EntrySession, session_id)

    async def ensure_session(
        self,
        *,
        session_id: uuid.UUID | None,
        current_user: User | None,
        initial_state: dict[str, Any] | None = None,
    ) -> tuple[EntrySession, bool]:
        session_record: EntrySession | None = None
        created = False

        if session_id is not None:
            session_record = await self.get_session(session_id)
            if (
                session_record is not None
                and current_user is not None
                and session_record.user_id is not None
                and session_record.user_id != current_user.id
            ):
                session_record = None

        if session_record is None:
            session_record = EntrySession(
                user_id=current_user.id if current_user else None,
                current_state=initial_state,
                metadata_={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(session_record)
            await self.db.flush()
            created = True
        else:
            if session_record.current_state is None and initial_state is not None:
                session_record.current_state = initial_state
            if current_user is not None and session_record.user_id is None:
                session_record.user_id = current_user.id
            session_record.updated_at = datetime.now(timezone.utc)
            await self.db.flush()

        return session_record, created

    async def start_run(
        self,
        *,
        session_record: EntrySession,
        current_user: User | None,
        graph_manifest: dict[str, Any],
        request_input: dict[str, Any] | None,
    ) -> EntryRun:
        run_record = EntryRun(
            session_id=session_record.id,
            user_id=current_user.id if current_user else session_record.user_id,
            graph_version=graph_manifest["version"],
            graph_manifest=graph_manifest,
            request_input=request_input,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run_record)
        await self.db.flush()
        return run_record

    async def complete_run(
        self,
        run_record: EntryRun,
        *,
        status: str,
        final_state: dict[str, Any] | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        run_record.status = status
        run_record.final_state = final_state
        if metadata:
            merged_metadata = dict(run_record.metadata_ or {})
            merged_metadata.update(metadata)
            run_record.metadata_ = merged_metadata
        run_record.completed_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def persist_session_state(
        self,
        session_record: EntrySession,
        *,
        state: dict[str, Any],
        current_user: User | None,
        last_stage_id: str | None,
        last_run_id: uuid.UUID | None,
    ) -> None:
        session_record.current_state = state
        if current_user is not None:
            session_record.user_id = current_user.id
        session_record.status = "ready" if state.get("node") == "operator_ready" else "active"
        session_record.updated_at = datetime.now(timezone.utc)

        merged_metadata = dict(session_record.metadata_ or {})
        if last_stage_id is not None:
            merged_metadata["last_stage_id"] = last_stage_id
        if last_run_id is not None:
            merged_metadata["last_run_id"] = str(last_run_id)
        session_record.metadata_ = merged_metadata
        await self.db.flush()

    async def start_stage(
        self,
        *,
        run_record: EntryRun,
        session_record: EntrySession,
        stage_id: str,
        lane: str,
        sequence: int,
        parent_stage_id: str | None,
        depends_on: list[str],
        input_payload: dict[str, Any] | None,
    ) -> EntryStage:
        stage = EntryStage(
            run_id=run_record.id,
            session_id=session_record.id,
            stage_id=stage_id,
            parent_stage_id=parent_stage_id,
            depends_on=depends_on or None,
            sequence=sequence,
            lane=lane,
            status="running",
            started_at=datetime.now(timezone.utc),
            input_payload=input_payload,
        )
        self.db.add(stage)
        await self.db.flush()
        return stage

    async def complete_stage(
        self,
        stage_record: EntryStage,
        *,
        status: str = "completed",
        output_payload: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        completed_at = datetime.now(timezone.utc)
        stage_record.status = status
        stage_record.output_payload = output_payload
        stage_record.error = error
        stage_record.completed_at = completed_at
        if stage_record.started_at is not None:
            duration = completed_at - stage_record.started_at
            stage_record.duration_ms = int(duration.total_seconds() * 1000)
        await self.db.flush()

    async def record_output(
        self,
        *,
        run_record: EntryRun,
        session_record: EntrySession,
        stage_id: str,
        sequence: int,
        lane: str,
        content: str,
    ) -> None:
        output = EntryOutput(
            run_id=run_record.id,
            session_id=session_record.id,
            stage_id=stage_id,
            sequence=sequence,
            lane=lane,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(output)
        await self.db.flush()

    async def record_artifact(
        self,
        *,
        run_record: EntryRun,
        session_record: EntrySession,
        stage_id: str,
        artifact_type: str,
        name: str,
        payload: dict[str, Any],
    ) -> None:
        artifact = EntryArtifact(
            run_id=run_record.id,
            session_id=session_record.id,
            stage_id=stage_id,
            artifact_type=artifact_type,
            name=name,
            payload=payload,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(artifact)
        await self.db.flush()