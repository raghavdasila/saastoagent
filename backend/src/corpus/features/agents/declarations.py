from __future__ import annotations

from routedeck_core.contracts.operations import Operation, OperationSource, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .schemas import CreateAgentArguments, UpdateAgentArguments


def operation(
    operation_id: str,
    title: str,
    description: str,
    outcome: str,
    *,
    input_schema: dict = EMPTY_OBJECT_SCHEMA,
    safety_class: SafetyClass = SafetyClass.NAVIGATION,
    sources: frozenset[OperationSource] = frozenset(
        {OperationSource.AGENT, OperationSource.SURFACE}
    ),
) -> Operation:
    return Operation(
        id=operation_id,
        title=title,
        description=description,
        input_schema=FrozenJsonObject(input_schema),
        safety_class=safety_class,
        allowed_sources=sources,
        outcomes=(outcome,),
        outcome_schemas=FrozenJsonObject({outcome: EMPTY_OBJECT_SCHEMA}),
        provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    )


OPEN_CREATE = operation(
    "agents.open_create",
    "Open agent creation",
    "Open the new-agent configuration surface.",
    "opened",
)
RETURN_TO_WORKSPACE = operation(
    "agents.return_to_workspace",
    "Return to Workspace",
    "Return to the authenticated Workspace overview.",
    "opened",
)
CREATE_AGENT = operation(
    "agents.create_agent",
    "Create agent",
    "Create an active agent with configuration version 1.",
    "created",
    input_schema=CreateAgentArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
)
SAVE_AGENT_CHANGES = operation(
    "agents.save_changes",
    "Save agent changes",
    "Create the next immutable configuration version for the selected agent.",
    "saved",
    input_schema=UpdateAgentArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
)
CANCEL_CREATE = operation(
    "agents.cancel_create",
    "Cancel agent creation",
    "Return to the agent inventory without creating an agent.",
    "opened",
)

__all__ = [
    "CANCEL_CREATE",
    "CREATE_AGENT",
    "OPEN_CREATE",
    "RETURN_TO_WORKSPACE",
    "SAVE_AGENT_CHANGES",
]
