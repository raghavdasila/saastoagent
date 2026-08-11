from __future__ import annotations

import hashlib
import json
import uuid

from .ports import DesignerConflict, DesignerInputGateway, DesignerRepository, DesignerUnavailable
from .schemas import (
    AgentDesignView,
    BuildRequestView,
    DesignContent,
    DesignRevisionView,
    DesignRuntimeArea,
)
from .topology import compile_design_topology


class DesignerService:
    def __init__(self, repository: DesignerRepository, inputs: DesignerInputGateway) -> None:
        self.repository = repository
        self.inputs = inputs

    async def get(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> AgentDesignView:
        design, revisions, build = await self.repository.get(organization_id, agent_id)
        view = _view(design, revisions, build)
        try:
            snapshot = await self.inputs.snapshot(organization_id, agent_id)
        except DesignerUnavailable:
            return view.model_copy(update={
                "current_inputs_ready": False,
                "current_inputs_match": False,
            })
        return view.model_copy(update={
            "current_inputs_ready": True,
            "current_inputs_match": bool(revisions) and revisions[-1].input_fingerprint == _fingerprint(snapshot),
        })

    async def propose(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> AgentDesignView:
        snapshot = await self.inputs.snapshot(organization_id, agent_id)
        tools = tuple(sorted({operation for source in snapshot.sources for operation in source.included_operation_ids}))
        groups = tuple(
            (source, group)
            for source in snapshot.sources
            for group in source.semantic_groups
        )
        capabilities = _exclusive_capabilities(groups, tools)
        capability_titles = tuple(value.partition(":")[0].strip() for value in capabilities)
        content = DesignContent(
            goal=snapshot.description or snapshot.agent_name,
            instructions=snapshot.instructions,
            features=tuple(
                f"{group.label} API feature"
                for _, group in groups
            ) or tuple(f"Curated API Source {source.source_id}" for source in snapshot.sources),
            behaviors=(
                snapshot.instructions,
                *(
                    f"Use the {group.label} capability for matching owner requests."
                    for _, group in groups
                ),
            ),
            policies=(
                "Use only operations in the accepted immutable Source curation.",
                "Ask one natural clarification when required input or operation choice is unresolved.",
                "Require owner review before an external write.",
            ),
            capabilities=capabilities,
            tools=tools,
            runtime_areas=tuple(
                DesignRuntimeArea(
                    title=_runtime_area_title(title),
                    capability_titles=(title,),
                )
                for title in capability_titles
            ),
        )
        compile_design_topology(content)
        fingerprint = _fingerprint(snapshot)
        await self.repository.propose(
            organization_id,
            snapshot,
            content=content.model_dump(mode="json"),
            input_fingerprint=fingerprint,
        )
        return await self.get(organization_id, agent_id)

    async def customize(self, organization_id, agent_id, *, expected_revision_id, content):
        current = await self.get(organization_id, agent_id)
        if not current.current_inputs_ready or not current.current_inputs_match:
            raise DesignerConflict(
                "The Agent or Source inputs changed. Create a new proposal before customizing it."
            )
        snapshot = await self.inputs.snapshot(organization_id, agent_id)
        expected_tools = tuple(sorted({
            operation
            for source in snapshot.sources
            for operation in source.included_operation_ids
        }))
        if content.tools != expected_tools:
            raise DesignerConflict(
                "API tools are locked to the exact saved Source operation selections."
            )
        compile_design_topology(content)
        await self.repository.customize(
            organization_id,
            agent_id,
            expected_revision_id=expected_revision_id,
            content=content.model_dump(mode="json"),
        )
        return await self.get(organization_id, agent_id)

    async def accept(self, organization_id, agent_id, *, expected_revision_id):
        await self.repository.accept(organization_id, agent_id, expected_revision_id=expected_revision_id)
        return await self.get(organization_id, agent_id)

    async def request_build(self, organization_id, agent_id, *, accepted_revision_id):
        await self.repository.request_build(organization_id, agent_id, accepted_revision_id=accepted_revision_id)
        return await self.get(organization_id, agent_id)


def _view(design, revisions, build):
    return AgentDesignView(
        agent_id=design.agent_id,
        current_revision_id=design.current_revision_id,
        accepted_revision_id=design.accepted_revision_id,
        revisions=tuple(DesignRevisionView(
            id=item.id,
            revision=item.revision,
            agent_version=item.agent_version,
            input_fingerprint=item.input_fingerprint,
        content=(content := DesignContent.model_validate(item.content)),
        topology=compile_design_topology(content),
        source_inputs=item.source_inputs,
            created_at=item.created_at,
        ) for item in revisions),
        build_request=None if build is None else BuildRequestView(
            id=build.id,
            design_revision_id=build.design_revision_id,
            status=build.status,
            created_at=build.created_at,
        ),
        current_inputs_ready=False,
        current_inputs_match=False,
    )


def _fingerprint(snapshot) -> str:
    payload = {
        "agent_id": str(snapshot.agent_id),
        "agent_version": snapshot.agent_version,
        "description": snapshot.description,
        "instructions": snapshot.instructions,
        "sources": [
            {
                "source_id": item.source_id,
                "source_revision_id": item.source_revision_id,
                "display_name": item.display_name,
                "curation_id": item.curation_id,
                "inventory_fingerprint": item.inventory_fingerprint,
                "included_operation_ids": list(item.included_operation_ids),
                "semantic_groups": [
                    {
                        "label": group.label,
                        "operation_ids": list(group.operation_ids),
                    }
                    for group in item.semantic_groups
                ],
            }
            for item in snapshot.sources
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _exclusive_capabilities(groups, tools: tuple[str, ...]) -> tuple[str, ...]:
    """Project overlapping semantic memberships into one executable partition.

    ToolRouter's semantic graph intentionally relates an API operation to more
    than one resource. RouteDeck capabilities are executable ownership groups,
    so the stable graph order chooses the first matching semantic group for
    each curated operation. Later overlapping groups remain Source/feature
    context but cannot claim the operation a second time.
    """

    remaining = set(tools)
    capabilities: list[str] = []
    title_counts: dict[str, int] = {}
    for _, group in groups:
        assigned = tuple(
            operation_id
            for operation_id in group.operation_ids
            if operation_id in remaining
        )
        if not assigned:
            continue
        base_title = group.label.strip() or "Curated operations"
        key = base_title.casefold()
        count = title_counts.get(key, 0) + 1
        title_counts[key] = count
        title = base_title if count == 1 else f"{base_title} ({count})"
        capabilities.append(f"{title}: {', '.join(assigned)}")
        remaining.difference_update(assigned)
    if remaining:
        capabilities.append(
            f"Curated operations: {', '.join(operation for operation in tools if operation in remaining)}"
        )
    return tuple(capabilities)


def _runtime_area_title(capability_title: str) -> str:
    """Turn semantic graph identifiers into stable owner-facing area labels."""

    words = capability_title.replace("_", " ").replace("-", " ").split()
    if not words:
        return "Curated operations"
    return " ".join(words).capitalize()
