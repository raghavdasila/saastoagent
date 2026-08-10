from routedeck_core.contracts.operations import EntityInput, Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .schemas import CreateChannelArguments, SetChannelEnabledArguments


CREATE_CHANNEL = Operation(
    id="channels.create", title="Create hosted Web channel",
    description=(
        "Set up one owner-scoped hosted Web address for the selected Agent without publishing "
        "a build or enabling public access."
    ),
    input_schema=FrozenJsonObject(CreateChannelArguments.model_json_schema()),
    safety_class=SafetyClass.DRAFT,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("created",), outcome_schemas=FrozenJsonObject({"created": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.NONE,
)
SET_CHANNEL_ENABLED = Operation(
    id="channels.set_enabled", title="Set hosted Web channel availability",
    description="Enable or disable public access to the exact owner-scoped hosted Web channel. This does not select, activate, or publish an Agent build.",
    input_schema=FrozenJsonObject(SetChannelEnabledArguments.model_json_schema()),
    safety_class=SafetyClass.WRITE_EXTERNAL,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("availability_set",),
    outcome_schemas=FrozenJsonObject({"availability_set": EMPTY_OBJECT_SCHEMA}),
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.REQUIRED,
    unknown_recovery_directive=(
        "Do not repeat an availability change automatically. Reload the exact channel state before any new reviewed action."
    ),
    public_metadata=FrozenJsonObject({"review_surface_id": "channels.availability_review"}),
)

__all__ = ["CREATE_CHANNEL", "SET_CHANNEL_ENABLED"]
