from __future__ import annotations

import uuid

from .ports import (
    AgentBuildLineageUnavailable,
    AgentRepository,
    AgentSourceAttachmentUnavailable,
    AgentSourceGateway,
)
from .schemas import (
    AgentBuildLineageListView,
    AgentBuildLineageView,
    AgentBuildSourceReferenceView,
    AgentListView,
    AgentDependencyView,
    AgentSourceAttachmentListView,
    AgentSourceAttachmentView,
    AgentView,
    CreateAgentArguments,
    UpdateAgentArguments,
)


class AgentService:
    def __init__(self, repository: AgentRepository, sources: AgentSourceGateway | None = None) -> None:
        self.repository = repository
        self.sources = sources

    async def list(self, organization_id: uuid.UUID) -> AgentListView:
        records = await self.repository.list(organization_id)
        return AgentListView(agents=tuple(AgentView.from_record(item) for item in records))

    async def get(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentView:
        return AgentView.from_record(
            await self.repository.get(organization_id, agent_id)
        )

    async def create(
        self,
        organization_id: uuid.UUID,
        arguments: CreateAgentArguments,
    ) -> AgentView:
        name = _normalized_name(arguments.name)
        return AgentView.from_record(
            await self.repository.create(
                organization_id,
                name=name,
                name_key=name.casefold(),
                description=arguments.description.strip(),
                instructions=arguments.instructions.strip(),
            )
        )

    async def update(
        self,
        organization_id: uuid.UUID,
        arguments: UpdateAgentArguments,
    ) -> AgentView:
        name = _normalized_name(arguments.name)
        return AgentView.from_record(
            await self.repository.update(
                organization_id,
                arguments.agent_id,
                expected_version=arguments.expected_version,
                name=name,
                name_key=name.casefold(),
                description=arguments.description.strip(),
                instructions=arguments.instructions.strip(),
            )
        )

    async def inspect_dependencies(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentDependencyView:
        return AgentDependencyView.from_snapshot(
            await self.repository.inspect_dependencies(organization_id, agent_id)
        )

    async def archive(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentView:
        return AgentView.from_record(
            await self.repository.archive(organization_id, agent_id)
        )

    async def delete(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> None:
        await self.repository.delete(organization_id, agent_id)

    async def list_source_attachments(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentSourceAttachmentListView:
        if self.sources is None:
            raise AgentSourceAttachmentUnavailable(
                "Source attachment details are unavailable."
            )
        records = await self.repository.list_source_attachments(organization_id, agent_id)
        attachments: list[AgentSourceAttachmentView] = []
        for record in records:
            source = await self.sources.exact_revision(
                organization_id,
                record.source_id,
                record.source_revision_id,
            )
            attachments.append(
                AgentSourceAttachmentView.from_record(
                    record,
                    display_name=source.display_name,
                )
            )
        return AgentSourceAttachmentListView(
            attachments=tuple(attachments)
        )

    async def one_agent_attached_to_source(
        self,
        organization_id: uuid.UUID,
        source_id: str,
    ) -> AgentView | None:
        matches = []
        for agent in await self.repository.list(organization_id):
            attachments = await self.repository.list_source_attachments(
                organization_id,
                agent.id,
            )
            if any(item.source_id == source_id for item in attachments):
                matches.append(agent)
        if len(matches) != 1:
            return None
        return AgentView.from_record(matches[0])

    async def one_attachable_ready_source(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AttachableSource:
        if self.sources is None:
            raise AgentSourceAttachmentUnavailable(
                "Source attachment details are unavailable."
            )
        attached = {
            record.source_id: record.source_revision_id
            for record in await self.repository.list_source_attachments(
                organization_id,
                agent_id,
            )
        }
        candidates = tuple(
            source
            for source in await self.sources.ready_inventory(organization_id)
            if attached.get(source.source_id) != source.source_revision_id
        )
        if len(candidates) != 1:
            raise AgentSourceAttachmentUnavailable(
                "This action requires one exact ready Source that is unattached or has a newer current API version; choose the Source you mean."
            )
        return candidates[0]

    async def attach_source(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        source_id: str,
        source_revision_id: str | None = None,
    ) -> AgentSourceAttachmentView:
        if self.sources is None:
            raise AgentSourceAttachmentUnavailable(
                "Source attachment details are unavailable."
            )
        source = (
            await self.sources.exact_revision(
                organization_id,
                source_id,
                source_revision_id,
            )
            if source_revision_id is not None
            else await self.sources.ready_current(organization_id, source_id)
        )
        record = await self.repository.attach_source(organization_id, agent_id, source)
        return AgentSourceAttachmentView.from_record(
            record,
            display_name=source.display_name,
        )

    async def detach_source(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        source_id: str,
    ) -> None:
        await self.repository.detach_source(
            organization_id,
            agent_id,
            source_id,
        )

    async def exact_ready_source(
        self,
        organization_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
    ) -> AttachableSource:
        if self.sources is None:
            raise AgentSourceAttachmentUnavailable(
                "Source attachment details are unavailable."
            )
        return await self.sources.exact_revision(
            organization_id,
            source_id,
            source_revision_id,
        )

    async def open_attached_source(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        source_id: str,
    ) -> AgentSourceAttachmentView:
        if self.sources is None:
            raise AgentSourceAttachmentUnavailable(
                "Source attachment details are unavailable."
            )
        record = await self.repository.get_source_attachment(
            organization_id, agent_id, source_id
        )
        source = await self.sources.exact_revision(
            organization_id,
            record.source_id,
            record.source_revision_id,
        )
        return AgentSourceAttachmentView.from_record(
            record,
            display_name=source.display_name,
        )

    async def record_build_lineage(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID,
        expected_agent_version: int,
        source_references: tuple[tuple[str, str], ...],
    ) -> AgentBuildLineageView:
        record = await self.repository.record_build_lineage(
            organization_id,
            agent_id,
            build_id=build_id,
            expected_agent_version=expected_agent_version,
            source_references=source_references,
        )
        return await self._build_lineage_view(organization_id, record)

    async def list_build_lineages(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentBuildLineageListView:
        records = await self.repository.list_build_lineages(organization_id, agent_id)
        return AgentBuildLineageListView(
            builds=tuple(
                [await self._build_lineage_view(organization_id, record) for record in records]
            )
        )

    async def require_build_source_reference(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
    ) -> None:
        records = await self.repository.list_build_lineages(organization_id, agent_id)
        record = next((item for item in records if item.build_id == build_id), None)
        if record is None or (source_id, source_revision_id) not in {
            (item.source_id, item.source_revision_id) for item in record.source_references
        }:
            raise AgentBuildLineageUnavailable(
                "The exact historical build Source reference is unavailable."
            )
        if self.sources is None:
            raise AgentBuildLineageUnavailable("Historical Source details are unavailable.")
        try:
            await self.sources.exact_revision(
                organization_id,
                source_id,
                source_revision_id,
            )
        except AgentSourceAttachmentUnavailable as error:
            raise AgentBuildLineageUnavailable(str(error)) from error

    async def _build_lineage_view(self, organization_id, record) -> AgentBuildLineageView:
        references: list[AgentBuildSourceReferenceView] = []
        for item in record.source_references:
            display_name: str | None = None
            available = False
            if self.sources is not None:
                try:
                    source = await self.sources.exact_revision(
                        organization_id,
                        item.source_id,
                        item.source_revision_id,
                    )
                except AgentSourceAttachmentUnavailable:
                    pass
                else:
                    display_name = source.display_name
                    available = True
            references.append(
                AgentBuildSourceReferenceView(
                    source_id=item.source_id,
                    source_revision_id=item.source_revision_id,
                    display_name=display_name,
                    available=available,
                )
            )
        return AgentBuildLineageView(
            build_id=record.build_id,
            agent_id=record.agent_id,
            agent_version=record.agent_version,
            created_at=record.created_at,
            source_references=tuple(references),
        )


def _normalized_name(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError("Agent name cannot be blank.")
    return normalized


__all__ = ["AgentService"]
