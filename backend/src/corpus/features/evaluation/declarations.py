from routedeck_core.contracts.operations import EntityInput, Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .schemas import (
    CreateEvaluationCaseArguments,
    DeleteEvaluationCaseArguments,
    EditEvaluationCaseArguments,
    GenerateEvaluationSetArguments,
    RetryEvaluationGenerationArguments,
    RunEvaluationCaseArguments,
)
from .policies import EXACT_STATE


CREATE_CASE = Operation(
    id="evaluation.create_case", title="Create evaluation case",
    description=(
        "Create one required evaluation case by keeping an exact immutable completed private "
        "trial from Sandbox, with the owner's category, difficulty, and name."
    ),
    input_schema=FrozenJsonObject(CreateEvaluationCaseArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("created",), outcome_schemas=FrozenJsonObject({"created": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
    policy_refs=(EXACT_STATE.ref,),
)
RUN_CASE = Operation(
    id="evaluation.run_case", title="Run evaluation case",
    description=(
        "Check the exact Agent build against one saved evaluation case and append the observed "
        "result without changing the case or build."
    ),
    input_schema=FrozenJsonObject(RunEvaluationCaseArguments.model_json_schema()),
    safety_class=SafetyClass.READ_EXTERNAL,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("evaluated",), outcome_schemas=FrozenJsonObject({"evaluated": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
    policy_refs=(EXACT_STATE.ref,),
)

GENERATE_SET = Operation(
    id="evaluation.generate_set", title="Generate evaluation set",
    description=(
        "Queue ToolRouter evaluation-set generation for one exact immutable Agent build and "
        "its curated operations; generation never grants deployment eligibility."
    ),
    input_schema=FrozenJsonObject(GenerateEvaluationSetArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("queued",), outcome_schemas=FrozenJsonObject({"queued": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE, policy_refs=(EXACT_STATE.ref,),
)
RETRY_GENERATION = Operation(
    id="evaluation.retry_generation", title="Retry evaluation generation",
    description="Explicitly retry one failed ToolRouter evaluation-set generation job.",
    input_schema=FrozenJsonObject(RetryEvaluationGenerationArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("queued",), outcome_schemas=FrozenJsonObject({"queued": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE, policy_refs=(EXACT_STATE.ref,),
)
EDIT_CASE = Operation(
    id="evaluation.edit_case", title="Edit evaluation case",
    description=(
        "Append an exact metadata revision for one evaluation case while preserving prior "
        "case revisions and completed result attribution."
    ),
    input_schema=FrozenJsonObject(EditEvaluationCaseArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("edited",), outcome_schemas=FrozenJsonObject({"edited": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE, policy_refs=(EXACT_STATE.ref,),
)
DELETE_CASE = Operation(
    id="evaluation.delete_case", title="Delete evaluation case",
    description=(
        "Remove one exact evaluation case from future eligibility after consequence review "
        "while retaining immutable prior revisions and completed results."
    ),
    input_schema=FrozenJsonObject(DeleteEvaluationCaseArguments.model_json_schema()),
    safety_class=SafetyClass.DESTRUCTIVE,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("removed",), outcome_schemas=FrozenJsonObject({"removed": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.REQUIRED,
    public_metadata=FrozenJsonObject({
        "review_surface_id": "evaluation.delete_case_review"
    }),
    policy_refs=(EXACT_STATE.ref,),
)

__all__ = ["CREATE_CASE", "DELETE_CASE", "EDIT_CASE", "GENERATE_SET", "RETRY_GENERATION", "RUN_CASE"]
