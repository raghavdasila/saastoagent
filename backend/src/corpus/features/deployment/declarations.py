from routedeck_core.contracts.operations import EntityInput, Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .schemas import DeployArguments, RollbackArguments


DEPLOY_AGENT = Operation(
    id="deployment.deploy", title="Deploy eligible Agent build",
    description=(
        "Put or publish one exact eligible immutable Agent build on the selected configured "
        "hosted Web address by activating it only after the required owner review."
    ),
    input_schema=FrozenJsonObject(DeployArguments.model_json_schema()),
    safety_class=SafetyClass.WRITE_EXTERNAL,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("deployed",), outcome_schemas=FrozenJsonObject({"deployed": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.REQUIRED,
    unknown_recovery_directive=(
        "Do not retry deployment automatically. Reload the exact durable deployment status and verify the hosted activation before any new reviewed attempt."
    ),
    public_metadata=FrozenJsonObject({"review_surface_id": "deployment.deploy_review"}),
)
ROLLBACK_DEPLOYMENT = Operation(
    id="deployment.rollback", title="Roll back hosted Agent",
    description="Activate one exact earlier ready deployment for this hosted Web channel.",
    input_schema=FrozenJsonObject(RollbackArguments.model_json_schema()),
    safety_class=SafetyClass.WRITE_EXTERNAL,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("rolled_back",), outcome_schemas=FrozenJsonObject({"rolled_back": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.REQUIRED,
    unknown_recovery_directive=(
        "Do not repeat rollback automatically. Reload the channel's exact active deployment before any new reviewed action."
    ),
    public_metadata=FrozenJsonObject({"review_surface_id": "deployment.rollback_review"}),
)

__all__ = ["DEPLOY_AGENT", "ROLLBACK_DEPLOYMENT"]
