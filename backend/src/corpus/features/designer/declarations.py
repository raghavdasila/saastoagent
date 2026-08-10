from __future__ import annotations

from routedeck_core.contracts.operations import ContextProvider, EntityInput, Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from . import policies
from .schemas import CustomizeDesignArguments, DesignerAgentArguments, RequestBuildArguments, ReviewDesignArguments


DESIGN_CURRENT_PROVIDER = ContextProvider(
    id="designer.current",
    description="Exact current selected-Agent design identity for review freshness.",
    output_schema=FrozenJsonObject({
        "type": "object",
        "properties": {
            "current_revision_id": {"type": "string", "minLength": 1},
            "accepted_revision_id": {"type": ["string", "null"]},
        },
        "required": ["current_revision_id", "accepted_revision_id"],
        "additionalProperties": False,
    }),
)


def _operation(operation_id, title, description, outcome, schema, *, review=ReviewPolicy.NONE, sources=None, metadata=None, current_provider=False, policy_refs=()):
    return Operation(
        id=operation_id,
        title=title,
        description=description,
        input_schema=FrozenJsonObject(schema),
        safety_class=SafetyClass.DRAFT if operation_id != "designer.return_to_agent" else SafetyClass.NAVIGATION,
        allowed_sources=sources or frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
        outcomes=(outcome,),
        outcome_schemas=FrozenJsonObject({outcome: EMPTY_OBJECT_SCHEMA}),
        provider_refs=(
            OWNER_CONTEXT_PROVIDER.ref,
            *((DESIGN_CURRENT_PROVIDER.ref,) if current_provider else ()),
        ),
        entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),) if "agent_ref" in schema.get("properties", {}) else (),
        review_policy=review,
        public_metadata=FrozenJsonObject(metadata or {}),
        policy_refs=policy_refs,
    )


PROPOSE_DESIGN = _operation("designer.propose", "Propose agent design", "Append a proposal from exact selected Agent and Source curation inputs.", "proposed", DesignerAgentArguments.model_json_schema(), policy_refs=(policies.EXACT_INPUTS.ref, policies.IMMUTABLE_REVISIONS.ref))
CUSTOMIZE_DESIGN = _operation("designer.customize", "Save design customization", "Append one next immutable proposal revision.", "customized", CustomizeDesignArguments.model_json_schema(), policy_refs=(policies.EXACT_INPUTS.ref, policies.IMMUTABLE_REVISIONS.ref))
APPROVE_DESIGN = _operation("designer.approve", "Approve agent design", "Accept the reviewed exact current proposal without starting a build.", "accepted", ReviewDesignArguments.model_json_schema(), review=ReviewPolicy.REQUIRED, metadata={"review_surface_id": "designer.review"}, current_provider=True, policy_refs=(policies.EXACT_REVIEW.ref,))
REQUEST_BUILD = _operation("designer.request_build", "Request agent build", "Append one pending build request for the exact accepted design revision.", "requested", RequestBuildArguments.model_json_schema(), policy_refs=(policies.EXACT_BUILD_REQUEST.ref, policies.DESIGN_BOUNDARY.ref))
RETURN_TO_AGENT = _operation("designer.return_to_agent", "Return to selected Agent", "Continue the selected Agent's current task in its operations hub without changing Designer state. Use this legal navigation when another Agent area owns the user's requested work; reaching the hub is not task completion.", "opened", DesignerAgentArguments.model_json_schema())

DESIGNER_OPERATION_IDS = (
    PROPOSE_DESIGN.id,
    CUSTOMIZE_DESIGN.id,
    APPROVE_DESIGN.id,
    REQUEST_BUILD.id,
    RETURN_TO_AGENT.id,
)
