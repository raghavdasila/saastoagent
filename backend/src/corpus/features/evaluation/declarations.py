from routedeck_core.contracts.operations import EntityInput, Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .schemas import CreateEvaluationCaseArguments, RunEvaluationCaseArguments
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

__all__ = ["CREATE_CASE", "RUN_CASE"]
