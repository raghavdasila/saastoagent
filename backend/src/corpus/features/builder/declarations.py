from routedeck_core.contracts.operations import EntityInput, Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .schemas import AssembleBuildArguments, BuildRuntimeLifecycleArguments


ASSEMBLE_BUILD = Operation(
    id="builder.assemble",
    title="Assemble accepted Agent build",
    description="Materialize one immutable runnable build from the exact pending accepted-design request, completing the owner's explicit request to create the runnable Agent.",
    input_schema=FrozenJsonObject(AssembleBuildArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("assembled",),
    outcome_schemas=FrozenJsonObject({"assembled": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
)

RUN_BUILD = Operation(
    id="builder.run",
    title="Run Agent build",
    description=(
        "Validate and enable the exact immutable draft Agent build for new "
        "Sandbox and Evaluation work without changing its compiled lineage."
    ),
    input_schema=FrozenJsonObject(BuildRuntimeLifecycleArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("running",),
    outcome_schemas=FrozenJsonObject({"running": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
)

PAUSE_BUILD = Operation(
    id="builder.pause",
    title="Pause Agent build",
    description=(
        "Pause admission of new Sandbox, Evaluation, and deployment work for "
        "the exact running draft Agent build while preserving immutable "
        "lineage, recorded runs, and already-deployed runtimes."
    ),
    input_schema=FrozenJsonObject(BuildRuntimeLifecycleArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("paused",),
    outcome_schemas=FrozenJsonObject({"paused": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
)

STOP_BUILD = Operation(
    id="builder.stop",
    title="Stop Agent build",
    description=(
        "Stop new draft Sandbox and Evaluation work for the exact build while "
        "preserving immutable history and every already-deployed runtime."
    ),
    input_schema=FrozenJsonObject(BuildRuntimeLifecycleArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("stopped",),
    outcome_schemas=FrozenJsonObject({"stopped": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
)

DELETE_BUILD = Operation(
    id="builder.delete",
    title="Delete Agent build",
    description=(
        "Remove the reviewed stopped draft runtime for the exact build while "
        "retaining immutable build, Sandbox, Evaluation, deployment, and "
        "Operations lineage."
    ),
    input_schema=FrozenJsonObject(BuildRuntimeLifecycleArguments.model_json_schema()),
    safety_class=SafetyClass.DESTRUCTIVE,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("removed",),
    outcome_schemas=FrozenJsonObject({"removed": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.REQUIRED,
    public_metadata=FrozenJsonObject({"review_surface_id": "builder.delete_review"}),
)

__all__ = [
    "ASSEMBLE_BUILD",
    "DELETE_BUILD",
    "PAUSE_BUILD",
    "RUN_BUILD",
    "STOP_BUILD",
]
