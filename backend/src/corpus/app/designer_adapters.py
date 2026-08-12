from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from corpus.features.agents.service import AgentService
from corpus.features.designer.domain import (
    DesignerGeneratedFeature,
    DesignerInputSnapshot,
    DesignerSemanticGroup,
    DesignerSourceInput,
)
from corpus.features.designer.ports import DesignerGenerationGateway, DesignerInputGateway, DesignerUnavailable


class _GeneratedFeature(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    feature: str = Field(min_length=1, max_length=240)
    behaviors: tuple[str, ...] = Field(min_length=1, max_length=8)
    policies: tuple[str, ...] = Field(min_length=1, max_length=8)
    capability_title: str = Field(min_length=1, max_length=160)
    runtime_area_title: str = Field(min_length=1, max_length=160)
    operation_ids: tuple[str, ...] = Field(min_length=1, max_length=64)


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


@dataclass(frozen=True)
class CorpusDesignerGenerationGateway(DesignerGenerationGateway):
    model: BaseChatModel
    plain_json: bool = False

    async def generate(
        self,
        snapshot: DesignerInputSnapshot,
        current_content: dict[str, object],
        description: str,
    ) -> DesignerGeneratedFeature:
        allowed_operations = tuple(sorted({
            operation_id
            for source in snapshot.sources
            for operation_id in source.included_operation_ids
        }))
        semantic_groups = [
            {
                "source": source.display_name,
                "label": group.label,
                "operation_ids": list(group.operation_ids),
            }
            for source in snapshot.sources
            for group in source.semantic_groups
        ]
        payload = {
            "owner_description": description,
            "agent": {
                "name": snapshot.agent_name,
                "description": snapshot.description,
                "instructions": snapshot.instructions,
            },
            "current_design": current_content,
            "allowed_operation_ids": list(allowed_operations),
            "semantic_groups": semantic_groups,
        }
        system = (
            "Generate one reviewable Corpus Agent design feature from the owner's ordinary description. "
            "Return concise owner-facing feature, behavior, policy, capability, and runtime-area text. "
            "Choose the smallest nonempty relevant operation_ids subset only from allowed_operation_ids. "
            "The capability title must be unique relative to current_design capabilities. Never invent an "
            "operation, credential, input value, API result, build, approval, or execution."
        )
        if self.plain_json:
            system += (
                " Return only one JSON object with exactly feature, behaviors, policies, "
                "capability_title, runtime_area_title, and operation_ids matching the supplied values."
            )
        value = await asyncio.to_thread(
            self._invoke,
            system,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        )
        try:
            generated = _GeneratedFeature.model_validate(value)
        except ValidationError as error:
            raise DesignerUnavailable(
                "The design model returned an invalid feature proposal."
            ) from error
        if len(set(generated.operation_ids)) != len(generated.operation_ids):
            raise DesignerUnavailable("The design model repeated one curated operation.")
        if not set(generated.operation_ids).issubset(allowed_operations):
            raise DesignerUnavailable("The design model selected an operation outside the saved Source curation.")
        return DesignerGeneratedFeature(**generated.model_dump())

    def _invoke(self, system: str, payload: str) -> object:
        model = self.model if self.plain_json else self.model.with_structured_output(
            _GeneratedFeature, method="json_schema"
        )
        response = model.invoke([("system", system), ("human", payload)])
        if not self.plain_json:
            return response
        content = getattr(response, "content", response)
        if not isinstance(content, str):
            raise DesignerUnavailable("The design model did not return structured text.")
        text = content.strip()
        if text.startswith("```json\n") and text.endswith("\n```"):
            text = text[len("```json\n") : -len("\n```")].strip()
        try:
            value = json.loads(text)
        except json.JSONDecodeError as error:
            raise DesignerUnavailable("The design model returned invalid structured JSON.") from error
        if not isinstance(value, dict):
            raise DesignerUnavailable("The design model output must be one JSON object.")
        return value


__all__ = ["CorpusDesignerGenerationGateway", "CorpusDesignerInputGateway"]
