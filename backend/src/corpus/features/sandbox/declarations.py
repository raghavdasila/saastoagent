from routedeck_core.contracts.operations import EntityInput, Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from .schemas import ResumeSandboxArguments, ResolveSandboxReviewArguments, StartSandboxArguments


_SANDBOX_OBSERVATION_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "final_response": {"type": ["string", "null"]},
        "api_call_count": {"type": "integer", "minimum": 0},
        "clarification": {
            "oneOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "candidate_choices": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "operation_id": {"type": "string", "minLength": 1},
                                    "label": {"type": ["string", "null"]},
                                },
                                "required": ["operation_id", "label"],
                                "additionalProperties": False,
                            },
                        },
                        "missing_input_names": {
                            "type": "array",
                            "items": {"type": "string", "minLength": 1},
                        },
                    },
                    "required": ["question", "candidate_choices", "missing_input_names"],
                    "additionalProperties": False,
                },
            ],
        },
    },
    "required": ["status", "final_response", "api_call_count", "clarification"],
    "additionalProperties": False,
}


START_SANDBOX = Operation(
    id="sandbox.start", title="Start Agent Sandbox run",
    description=(
        "Start one isolated run against the exact selected immutable Agent build when the "
        "owner asks to try or test it in a private trial. Pass the user's unresolved request "
        "without answering, expanding, splitting, or selecting an operation; the built Agent "
        "and ToolRouter own resolution and clarification."
    ),
    input_schema=FrozenJsonObject(StartSandboxArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("started",), outcome_schemas=FrozenJsonObject({"started": _SANDBOX_OBSERVATION_SCHEMA}),
    public_outcome_schemas=FrozenJsonObject({"started": _SANDBOX_OBSERVATION_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
)

RESUME_SANDBOX = Operation(
    id="sandbox.resume", title="Continue Agent Sandbox clarification",
    description=(
        "Continue the exact waiting Sandbox run from the user's natural non-secret reply. "
        "Use only exact candidate and missing-input identities from the latest Sandbox tool observation."
    ),
    input_schema=FrozenJsonObject(ResumeSandboxArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("resumed",), outcome_schemas=FrozenJsonObject({"resumed": _SANDBOX_OBSERVATION_SCHEMA}),
    public_outcome_schemas=FrozenJsonObject({"resumed": _SANDBOX_OBSERVATION_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
)

ACCEPT_SANDBOX_REVIEW = Operation(
    id="sandbox.accept_action_review", title="Approve reviewed Sandbox action",
    description=(
        "Accept the exact pending reviewed action for the selected Sandbox run after the "
        "owner explicitly approves its visible effect. Continue that same immutable run; "
        "never infer approval from the original request or a clarification answer."
    ),
    input_schema=FrozenJsonObject(ResolveSandboxReviewArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    outcomes=("resumed",), outcome_schemas=FrozenJsonObject({"resumed": _SANDBOX_OBSERVATION_SCHEMA}),
    public_outcome_schemas=FrozenJsonObject({"resumed": _SANDBOX_OBSERVATION_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
)

REJECT_SANDBOX_REVIEW = Operation(
    id="sandbox.reject_action_review", title="Reject reviewed Sandbox action",
    description="Reject the exact pending Sandbox action without sending its external write.",
    input_schema=FrozenJsonObject(ResolveSandboxReviewArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    outcomes=("resumed",), outcome_schemas=FrozenJsonObject({"resumed": _SANDBOX_OBSERVATION_SCHEMA}),
    public_outcome_schemas=FrozenJsonObject({"resumed": _SANDBOX_OBSERVATION_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
)

__all__ = ["ACCEPT_SANDBOX_REVIEW", "REJECT_SANDBOX_REVIEW", "RESUME_SANDBOX", "START_SANDBOX"]
