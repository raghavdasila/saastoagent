from __future__ import annotations

import asyncio
import uuid

from pydantic import BaseModel, ConfigDict

from .models import SourceState
from .ports import SourceDependencyGateway
from .repository import LocalSourceRepository, SourceNotReady


class SourceDependencyConflict(RuntimeError):
    pass


class SourceDependencyView(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    processing_state: SourceState
    attached_agent_ids: tuple[uuid.UUID, ...] = ()
    build_ids: tuple[uuid.UUID, ...] = ()
    design_revision_ids: tuple[uuid.UUID, ...] = ()
    blocks_delete: bool


class SourceLifecycleService:
    def __init__(
        self,
        repository: LocalSourceRepository,
        dependencies: SourceDependencyGateway,
    ) -> None:
        self.repository = repository
        self.dependencies = dependencies

    async def inspect_dependencies(
        self, organization_id: uuid.UUID, source_id: str
    ) -> SourceDependencyView:
        source, references = await asyncio.gather(
            asyncio.to_thread(
                self.repository.get,
                owner_key=str(organization_id),
                source_id=source_id,
            ),
            self.dependencies.inspect_source_dependencies(organization_id, source_id),
        )
        processing = source.revision.state in {SourceState.QUEUED, SourceState.RUNNING}
        return SourceDependencyView(
            source_id=source_id,
            processing_state=source.revision.state,
            attached_agent_ids=references.attached_agent_ids,
            build_ids=references.build_ids,
            design_revision_ids=references.design_revision_ids,
            blocks_delete=processing
            or bool(
                references.attached_agent_ids
                or references.build_ids
                or references.design_revision_ids
            ),
        )

    async def delete(self, organization_id: uuid.UUID, source_id: str) -> None:
        await self.require_deletable(organization_id, source_id)
        try:
            await asyncio.to_thread(
                self.repository.delete_source,
                owner_key=str(organization_id),
                source_id=source_id,
            )
        except SourceNotReady as error:
            raise SourceDependencyConflict(str(error)) from error

    async def require_deletable(
        self, organization_id: uuid.UUID, source_id: str
    ) -> SourceDependencyView:
        dependencies = await self.inspect_dependencies(organization_id, source_id)
        if dependencies.blocks_delete:
            raise SourceDependencyConflict(_dependency_message(dependencies))
        return dependencies


def _dependency_message(value: SourceDependencyView) -> str:
    blockers: list[str] = []
    if value.processing_state in {SourceState.QUEUED, SourceState.RUNNING}:
        blockers.append("active API analysis")
    if value.attached_agent_ids:
        blockers.append(f"{len(value.attached_agent_ids)} Agent attachment(s)")
    if value.design_revision_ids:
        blockers.append(f"{len(value.design_revision_ids)} saved Agent design revision(s)")
    if value.build_ids:
        blockers.append(f"{len(value.build_ids)} immutable Agent build(s)")
    detail = ", ".join(blockers) or "an unavailable dependency"
    return f"Delete is blocked by {detail}. The API source and every dependency remain unchanged."


__all__ = [
    "SourceDependencyConflict",
    "SourceDependencyView",
    "SourceLifecycleService",
]
