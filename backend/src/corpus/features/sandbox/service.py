from __future__ import annotations

import uuid

from corpus.clarification import (
    ClarificationInputRejected,
    screen_clarification_values,
)
from corpus.features.builder.service import BuilderService

from .domain import RuntimeSandboxRun
from .ports import SandboxRepository, SandboxRuntimeGateway, SandboxUnavailable
from .schemas import (
    SandboxClarificationChoiceView,
    SandboxClarificationView,
    SandboxEventView,
    SandboxRunCollectionView,
    SandboxRunView,
)


class SandboxService:
    def __init__(self, repository: SandboxRepository, runtime: SandboxRuntimeGateway, builds: BuilderService) -> None:
        self.repository, self.runtime, self.builds = repository, runtime, builds

    async def list(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> SandboxRunCollectionView:
        await self.builds.list(organization_id, agent_id)
        return SandboxRunCollectionView(agent_id=agent_id, runs=tuple(_view(item) for item in await self.repository.list(organization_id, agent_id)))

    async def start(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_id: uuid.UUID, message: str) -> SandboxRunView:
        build = await self.builds.require_ready(organization_id, agent_id, build_id)
        record = None
        try:
            record = await self.repository.begin(
                organization_id, agent_id, build=build, message=message
            )
            result = await self.runtime.start(
                organization_id=organization_id, session_id=record.runtime_session_id,
                run_id=record.runtime_run_id, build=build, message=message,
            )
            return _view(await self.repository.complete(organization_id, record.id, result))
        except Exception as error:
            if record is not None:
                await self.repository.fail(
                    organization_id, record.id, code=type(error).__name__
                )
            if isinstance(error, SandboxUnavailable):
                raise
            raise SandboxUnavailable("The Sandbox run failed.") from error

    async def start_current(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        message: str,
    ) -> SandboxRunView:
        ready = tuple(
            build
            for build in (await self.builds.list(organization_id, agent_id)).builds
            if build.status == "ready"
        )
        if len(ready) != 1:
            raise SandboxUnavailable(
                "Sandbox requires one exact ready build; select a build before starting."
            )
        return await self.start(
            organization_id,
            agent_id,
            build_id=ready[0].id,
            message=message,
        )

    async def resume(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        run_id: uuid.UUID,
        message: str,
        selected_operation_id: str | None,
        answers: dict[str, str],
    ) -> SandboxRunView:
        _screen_clarification(message, answers)
        record = await self.repository.begin_resume(organization_id, agent_id, run_id)
        build = await self.builds.require_ready(
            organization_id, agent_id, record.build_id
        )
        if build.runtime_build_hash != record.runtime_build_hash:
            await self.repository.fail(
                organization_id, record.id, code="runtime_build_changed"
            )
            raise SandboxUnavailable("The exact Sandbox build changed before clarification.")
        try:
            result = await self.runtime.resume(
                organization_id=organization_id,
                record=record,
                build=build,
                message=message,
                selected_operation_id=selected_operation_id,
                answers=answers,
            )
            return _view(
                await self.repository.complete(organization_id, record.id, result)
            )
        except Exception as error:
            await self.repository.fail(
                organization_id, record.id, code=type(error).__name__
            )
            if isinstance(error, SandboxUnavailable):
                raise
            raise SandboxUnavailable("The Sandbox clarification failed.") from error

    async def resume_current(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        message: str,
        selected_operation_id: str | None,
        answers: dict[str, str],
    ) -> SandboxRunView:
        waiting = tuple(
            run
            for run in (await self.list(organization_id, agent_id)).runs
            if run.status == "waiting"
        )
        if len(waiting) != 1:
            raise SandboxUnavailable(
                "Sandbox clarification requires one exact waiting run."
            )
        return await self.resume(
            organization_id,
            agent_id,
            run_id=waiting[0].id,
            message=message,
            selected_operation_id=selected_operation_id,
            answers=answers,
        )


def _view(value):
    clarification = _clarification(value)
    return SandboxRunView(
        id=value.id, agent_id=value.agent_id, build_id=value.build_id,
        runtime_session_id=value.runtime_session_id, runtime_run_id=value.runtime_run_id,
        status=value.status, message=value.message, awaiting=value.awaiting,
        clarification=clarification, final_response=value.final_response,
        api_call_count=value.api_call_count,
        events=tuple(SandboxEventView.model_validate(item) for item in value.safe_events),
        routedeck_projection=value.routedeck_projection,
        failure_code=value.failure_code, created_at=value.created_at, updated_at=value.updated_at,
    )


def _clarification(value) -> SandboxClarificationView | None:
    if value.status != "waiting" or not value.final_response:
        return None
    decisions = [item for item in value.safe_events if item.get("kind") == "router.decision"]
    data = decisions[-1].get("safe_data", {}) if decisions else {}
    if not isinstance(data, dict):
        data = {}
    candidates = tuple(
        str(item.get("operation_id"))
        for item in data.get("candidates", ())
        if isinstance(item, dict) and item.get("operation_id")
    )
    choices = tuple(
        SandboxClarificationChoiceView(
            operation_id=str(item.get("operation_id")),
            label=(str(item.get("label")) if item.get("label") else None),
        )
        for item in data.get("candidates", ())
        if isinstance(item, dict) and item.get("operation_id")
    )
    missing = tuple(str(item) for item in data.get("missing_params", ()) if str(item))
    return SandboxClarificationView(
        question=value.final_response,
        candidate_operation_ids=candidates,
        candidate_choices=choices,
        missing_input_names=missing,
    )


def _screen_clarification(message: str, answers: dict[str, str]) -> None:
    try:
        screen_clarification_values(message, answers)
    except ClarificationInputRejected as error:
        raise SandboxUnavailable(str(error)) from error


__all__ = ["SandboxService"]
