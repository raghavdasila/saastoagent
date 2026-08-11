from routedeck_core.contracts.operations import EntityInput, Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .schemas import DeployArguments, RetryDeploymentArguments, RollbackArguments


DEPLOY_AGENT = Operation(
    id="deployment.deploy", title="Deploy eligible Agent build",
    description=(
        "Queue one reviewed deployment attempt for an exact eligible immutable Agent build "
        "and configured hosted Web address."
    ),
    input_schema=FrozenJsonObject(DeployArguments.model_json_schema()),
    safety_class=SafetyClass.WRITE_EXTERNAL,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("queued",), outcome_schemas=FrozenJsonObject({"queued": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.REQUIRED,
    unknown_recovery_directive=(
        "Do not retry deployment automatically. Reload the exact durable deployment status and verify the hosted activation before any new reviewed attempt."
    ),
    public_metadata=FrozenJsonObject({"review_surface_id": "deployment.deploy_review"}),
)
RETRY_DEPLOYMENT = Operation(
    id="deployment.retry", title="Retry failed deployment",
    description=(
        "Queue one new reviewed attempt linked to an exact definitely failed deployment."
    ),
    input_schema=FrozenJsonObject(RetryDeploymentArguments.model_json_schema()),
    safety_class=SafetyClass.WRITE_EXTERNAL,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("queued",), outcome_schemas=FrozenJsonObject({"queued": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.REQUIRED,
    unknown_recovery_directive=(
        "Do not retry deployment automatically. Reload the exact failed deployment and stage a new owner review only when its external outcome is definite."
    ),
    public_metadata=FrozenJsonObject({"review_surface_id": "deployment.retry_review"}),
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

__all__ = ["DEPLOY_AGENT", "RETRY_DEPLOYMENT", "ROLLBACK_DEPLOYMENT"]
