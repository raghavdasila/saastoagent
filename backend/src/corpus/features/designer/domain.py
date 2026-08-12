from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DesignerSemanticGroup:
    label: str
    operation_ids: tuple[str, ...]


@dataclass(frozen=True)
class DesignerSourceInput:
    source_id: str
    source_revision_id: str
    display_name: str
    curation_id: str
    inventory_fingerprint: str
    included_operation_ids: tuple[str, ...]
    semantic_groups: tuple[DesignerSemanticGroup, ...]


@dataclass(frozen=True)
class DesignerInputSnapshot:
    agent_id: uuid.UUID
    agent_version: int
    agent_name: str
    description: str
    instructions: str
    sources: tuple[DesignerSourceInput, ...]


@dataclass(frozen=True)
class DesignerGeneratedFeature:
    feature: str
    behaviors: tuple[str, ...]
    policies: tuple[str, ...]
    capability_title: str
    runtime_area_title: str
    operation_ids: tuple[str, ...]


@dataclass(frozen=True)
class DesignRevisionRecord:
    id: uuid.UUID
    design_id: uuid.UUID
    revision: int
    agent_version: int
    input_fingerprint: str
    content: dict[str, object]
    source_inputs: tuple[dict[str, object], ...]
    created_at: datetime


@dataclass(frozen=True)
class AgentDesignRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    current_revision_id: uuid.UUID
    current_revision: int
    accepted_revision_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BuildRequestRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    design_revision_id: uuid.UUID
    status: str
    created_at: datetime
