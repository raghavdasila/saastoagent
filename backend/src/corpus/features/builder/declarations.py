from routedeck_core.contracts.operations import EntityInput, Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .schemas import AssembleBuildArguments


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

__all__ = ["ASSEMBLE_BUILD"]
