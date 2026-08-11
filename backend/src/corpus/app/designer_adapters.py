from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

from corpus.features.agents.service import AgentService
from corpus.features.designer.domain import (
    DesignerInputSnapshot,
    DesignerSemanticGroup,
    DesignerSourceInput,
)
from corpus.features.designer.ports import DesignerInputGateway, DesignerUnavailable


@dataclass(frozen=True)
class CorpusDesignerInputGateway(DesignerInputGateway):
    agents: AgentService
    curations: object
    graphs: object

    async def snapshot(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> DesignerInputSnapshot:
        try:
            agent = await self.agents.get(organization_id, agent_id)
            attachments = (await self.agents.list_source_attachments(organization_id, agent_id)).attachments
        except Exception as error:
            raise DesignerUnavailable("The exact selected Agent inputs are unavailable.") from error
        sources: list[DesignerSourceInput] = []
        for attachment in attachments:
            try:
                view = await asyncio.to_thread(
                    self.curations.inspect,
                    owner_id=organization_id,
                    source_id=attachment.source_id,
                    source_revision_id=attachment.source_revision_id,
                )
                graph = await asyncio.to_thread(
                    self.graphs.inspect_exact,
                    owner_key=str(organization_id),
                    source_id=attachment.source_id,
                    revision_id=attachment.source_revision_id,
                )
            except Exception as error:
                raise DesignerUnavailable(
                    "An attached Source curation is unavailable. Refresh the Source before proposing a design."
                ) from error
            if view.current is None:
                raise DesignerUnavailable("Every attached Source requires a saved operation curation.")
            included = set(view.current.included_operation_ids)
            sources.append(DesignerSourceInput(
                source_id=attachment.source_id,
                source_revision_id=attachment.source_revision_id,
                display_name=attachment.display_name,
                curation_id=view.current.id,
                inventory_fingerprint=view.inventory_fingerprint,
                included_operation_ids=view.current.included_operation_ids,
                semantic_groups=tuple(
                    DesignerSemanticGroup(
                        label=group.label,
                        operation_ids=tuple(
                            operation_id
                            for operation_id in graph.operation_ids_for_group(group)
                            if operation_id in included
                        ),
                    )
                    for group in graph.semantic_groups
                    if included.intersection(
                        graph.operation_ids_for_group(group)
                    )
                ),
            ))
        if not sources:
            raise DesignerUnavailable("Attach and curate at least one ready Source before proposing a design.")
        return DesignerInputSnapshot(
            agent_id=agent.id,
            agent_version=agent.current_version,
            agent_name=agent.name,
            description=agent.description,
            instructions=agent.instructions,
            sources=tuple(sources),
        )


__all__ = ["CorpusDesignerInputGateway"]
