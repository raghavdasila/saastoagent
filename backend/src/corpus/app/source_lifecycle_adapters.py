from __future__ import annotations

import uuid

from sqlalchemy import select

from corpus.features.agents.models import (
    AgentBuildLineage,
    AgentBuildSourceReference,
    AgentSourceAttachment,
)
from corpus.features.designer.models import AgentDesign, AgentDesignRevision
from corpus.features.sources.ports import SourceDependencyReferences
from corpus.persistence import CorpusDatabase


class CorpusSourceDependencyGateway:
    """Read cross-feature immutable Source references without moving ownership."""

    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def inspect_source_dependencies(
        self, organization_id: uuid.UUID, source_id: str
    ) -> SourceDependencyReferences:
        async with self.database.session() as session:
            attached_agent_ids = tuple(
                (
                    await session.scalars(
                        select(AgentSourceAttachment.agent_id)
                        .where(
                            AgentSourceAttachment.organization_id == organization_id,
                            AgentSourceAttachment.source_id == source_id,
                        )
                        .order_by(AgentSourceAttachment.agent_id)
                    )
                ).all()
            )
            build_ids = tuple(
                (
                    await session.scalars(
                        select(AgentBuildLineage.build_id)
                        .join(
                            AgentBuildSourceReference,
                            AgentBuildSourceReference.build_lineage_id
                            == AgentBuildLineage.id,
                        )
                        .where(
                            AgentBuildLineage.organization_id == organization_id,
                            AgentBuildSourceReference.source_id == source_id,
                        )
                        .order_by(AgentBuildLineage.build_id)
                    )
                ).all()
            )
            design_rows = (
                await session.execute(
                    select(AgentDesignRevision.id, AgentDesignRevision.source_inputs)
                    .join(AgentDesign, AgentDesignRevision.design_id == AgentDesign.id)
                    .where(AgentDesign.organization_id == organization_id)
                    .order_by(AgentDesignRevision.id)
                )
            ).all()
        design_revision_ids = tuple(
            revision_id
            for revision_id, source_inputs in design_rows
            if any(
                isinstance(item, dict) and item.get("source_id") == source_id
                for item in (source_inputs or [])
            )
        )
        return SourceDependencyReferences(
            attached_agent_ids=attached_agent_ids,
            build_ids=build_ids,
            design_revision_ids=design_revision_ids,
        )


__all__ = ["CorpusSourceDependencyGateway"]
