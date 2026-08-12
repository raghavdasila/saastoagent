from __future__ import annotations

import hashlib
import json
import uuid

from .ports import DesignerConflict, DesignerGenerationGateway, DesignerInputGateway, DesignerRepository, DesignerUnavailable
from .schemas import (
    AgentDesignView,
    BuildRequestView,
    DesignContent,
    DesignRevisionView,
    DesignRuntimeArea,
)
from .topology import compile_design_topology


class DesignerService:
    def __init__(
        self,
        repository: DesignerRepository,
        inputs: DesignerInputGateway,
        generation: DesignerGenerationGateway | None = None,
    ) -> None:
        self.repository = repository
        self.inputs = inputs
        self.generation = generation

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

    async def generate_feature(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        expected_revision_id: uuid.UUID,
        description: str,
    ) -> AgentDesignView:
        if self.generation is None:
            raise DesignerUnavailable("Agent design generation is not configured.")
        current = await self.get(organization_id, agent_id)
        if not current.current_inputs_ready or not current.current_inputs_match:
            raise DesignerConflict(
                "The Agent or Source inputs changed. Create a new proposal before generating a feature."
            )
        if current.current_revision_id != expected_revision_id or not current.revisions:
            raise DesignerConflict("The current Agent design revision changed. Refresh before generating a feature.")
        snapshot = await self.inputs.snapshot(organization_id, agent_id)
        current_content = current.revisions[-1].content
        generated = await self.generation.generate(
            snapshot,
            current_content.model_dump(mode="json"),
            description,
        )
        content = _merge_generated_feature(current_content, generated)
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


def _merge_generated_feature(current: DesignContent, generated) -> DesignContent:
    selected = set(generated.operation_ids)
    if not selected:
        raise DesignerConflict("The generated feature selected no curated API operation.")
    if not selected.issubset(current.tools):
        raise DesignerConflict("The generated feature selected an operation outside the current design.")

    retained_capabilities: list[tuple[str, tuple[str, ...]]] = []
    for value in current.capabilities:
        title, separator, raw_operations = value.partition(":")
        operations = tuple(item.strip() for item in raw_operations.split(",") if item.strip())
        if not separator or not title.strip() or not operations:
            raise DesignerConflict("The current design capability mapping is unavailable for generation.")
        remaining = tuple(operation for operation in operations if operation not in selected)
        if remaining:
            retained_capabilities.append((title.strip(), remaining))

    generated_title = generated.capability_title.strip()
    if not generated_title or generated_title.casefold() in {
        title.casefold() for title, _ in retained_capabilities
    }:
        raise DesignerConflict("The design model returned a duplicate capability title.")
    selected_in_design_order = tuple(operation for operation in current.tools if operation in selected)
    capabilities = tuple(
        f"{title}: {', '.join(operations)}"
        for title, operations in retained_capabilities
    ) + (f"{generated_title}: {', '.join(selected_in_design_order)}",)

    retained_titles = {title.casefold() for title, _ in retained_capabilities}
    runtime_areas = tuple(
        DesignRuntimeArea(
            title=area.title,
            capability_titles=tuple(
                title for title in area.capability_titles if title.casefold() in retained_titles
            ),
        )
        for area in current.runtime_areas
        if any(title.casefold() in retained_titles for title in area.capability_titles)
    )
    runtime_title = generated.runtime_area_title.strip()
    if not runtime_title or runtime_title.casefold() in {
        area.title.casefold() for area in runtime_areas
    }:
        raise DesignerConflict("The design model returned a duplicate runtime-area title.")
    runtime_areas = (*runtime_areas, DesignRuntimeArea(
        title=runtime_title,
        capability_titles=(generated_title,),
    ))
    return DesignContent(
        goal=current.goal,
        instructions=current.instructions,
        features=_append_unique(current.features, (generated.feature,)),
        behaviors=_append_unique(current.behaviors, generated.behaviors),
        policies=_append_unique(current.policies, generated.policies),
        capabilities=capabilities,
        tools=current.tools,
        runtime_areas=runtime_areas,
    )


def _append_unique(current: tuple[str, ...], additions: tuple[str, ...]) -> tuple[str, ...]:
    values = list(current)
    seen = {value.casefold() for value in current}
    for raw in additions:
        value = raw.strip()
        if value and value.casefold() not in seen:
            seen.add(value.casefold())
            values.append(value)
    return tuple(values)
