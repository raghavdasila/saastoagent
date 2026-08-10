from routedeck_core.contracts.operations import Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .schemas import PromoteInteractionArguments
from .policies import EXACT_STATE


PROMOTE_INTERACTION = Operation(
    id="operations.promote_evaluation_case", title="Promote interaction to evaluation",
    description=(
        "Only when the owner explicitly asks to turn one selected deployed interaction "
        "into a future evaluation case, create it from that exact interaction and build "
        "lineage. Never use this operation to inspect, explain, or display how an "
        "interaction ran."
    ),
    input_schema=FrozenJsonObject(PromoteInteractionArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("promoted",), outcome_schemas=FrozenJsonObject({"promoted": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,), review_policy=ReviewPolicy.NONE,
    policy_refs=(EXACT_STATE.ref,),
)

__all__ = ["PROMOTE_INTERACTION"]
