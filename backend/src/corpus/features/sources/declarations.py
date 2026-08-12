from __future__ import annotations

from routedeck_core.contracts.navigation import NodeRef
from routedeck_core.contracts.operations import (
    ContextProvider,
    EntityInput,
    EntityProvider,
    Guard,
    Operation,
    OperationSource,
    ReviewPolicy,
    SafetyClass,
)
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA
from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from . import policies
from .contracts import API_CONNECTION_FORM_ID
from .schemas import (
    ApproveContractRevisionArguments,
    ContinueCurrentApiRoutePlanArguments,
    GraphStageArguments,
    ProposeContractRevisionArguments,
    ProcessApiSourceArguments,
    PrepareCurrentApiRoutePlanArguments,
    OpenApiSourceArguments,
    OpenApiDescriptionArguments,
    RetrySourceArguments,
    SaveApiOperationCurationArguments,
    TestApiConnectionArguments,
)


def operation(
    operation_id: str,
    title: str,
    description: str,
    outcome: str,
    *,
    input_schema: dict = EMPTY_OBJECT_SCHEMA,
    safety_class: SafetyClass = SafetyClass.NAVIGATION,
    sources: frozenset[OperationSource] = frozenset(
        {OperationSource.AGENT, OperationSource.SURFACE}
    ),
    entity_inputs: tuple[EntityInput, ...] = (),
    review_policy: ReviewPolicy = ReviewPolicy.NONE,
    guard_refs=(),
    policy_refs=(),
    public_metadata: dict | None = None,
    unknown_recovery_directive: str | None = None,
    outcome_schema: dict = EMPTY_OBJECT_SCHEMA,
    additional_provider_refs=(),
) -> Operation:
    return Operation(
        id=operation_id,
        title=title,
        description=description,
        input_schema=FrozenJsonObject(input_schema),
        safety_class=safety_class,
        allowed_sources=sources,
        outcomes=(outcome,),
        outcome_schemas=FrozenJsonObject({outcome: outcome_schema}),
        public_outcome_schemas=FrozenJsonObject({outcome: outcome_schema}),
        provider_refs=(OWNER_CONTEXT_PROVIDER.ref, *additional_provider_refs),
        entity_inputs=entity_inputs,
        review_policy=review_policy,
        guard_refs=guard_refs,
        policy_refs=policy_refs,
        public_metadata=FrozenJsonObject(public_metadata or {}),
        unknown_recovery_directive=unknown_recovery_directive,
    )


CONTRACT_REVISION_PROPOSAL_PROVIDER = EntityProvider(
    id="sources.contract_revision_proposal",
    entity_kind="contract_revision_proposal",
    description="The exact owner-scoped persisted API update proposal retained in this session.",
    output_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
)
SELECTED_API_SOURCE_PROVIDER = ContextProvider(
    id="sources.selected_api_source",
    description=(
        "The exact API Source and revision already selected on the current API Source surface."
    ),
    output_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "source_id": {"type": "string", "minLength": 16, "maxLength": 16},
                "source_revision_id": {
                    "type": "string",
                    "minLength": 16,
                    "maxLength": 16,
                },
                "return_agent_ref": {"type": "string", "minLength": 1},
                "agent_handoff_mode": {
                    "type": "string",
                    "enum": ["create", "inspect"],
                },
                "attached_source_revision_id": {
                    "type": "string",
                    "minLength": 16,
                    "maxLength": 16,
                },
                "attachment_update_available": {"type": "boolean"},
                "return_context": {
                    "type": "string",
                    "enum": ["agent", "builder"],
                },
                "initial_workspace": {
                    "type": "string",
                    "enum": ["graph", "operations", "connection", "agent", "description"],
                },
            },
            "dependentRequired": {
                "source_id": ["source_revision_id"],
                "source_revision_id": ["source_id"],
            },
            "additionalProperties": False,
        }
    ),
)
CONTRACT_REVISION_CURRENT_GUARD = Guard(
    id="sources.contract_revision_current",
    description="Requires the reviewed API update and exact parent Source version to remain current at acceptance time.",
)
API_CONNECTION_CHECK_CURRENT_GUARD = Guard(
    id="sources.api_connection_check_current",
    description="Requires the exact owner Source revision, saved profile, credential version and safe read operation to remain executable.",
)
API_OPERATION_CURATION_CURRENT_GUARD = Guard(
    id="sources.api_operation_curation_current",
    description="Requires the exact owner Source revision and discovered operation inventory to remain current before saving explicit inclusion decisions.",
)
ROUTED_API_READ_CURRENT_GUARD = Guard(
    id="sources.routed_api_read_current",
    description="Requires one exact current owner plan with one fully resolved read operation and no prior execution claim.",
)
ROUTED_API_WRITE_CURRENT_GUARD = Guard(
    id="sources.routed_api_write_current",
    description="Rechecks one exact current owner plan with one fully resolved write operation and no prior execution claim at review acceptance time.",
)
SOURCE_DELETE_CURRENT_GUARD = Guard(
    id="sources.source_delete_current",
    description=(
        "Rechecks the exact selected Source, processing state, Agent attachments, saved designs, "
        "and immutable build references before staging and accepting permanent deletion."
    ),
)


RETURN_TO_HOME = operation(
    "sources.return_to_home",
    "Return Home",
    "Return from Sources to the authenticated owner home.",
    "opened",
    sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
)
OPEN_API_CREATION = operation(
    "sources.open_api_creation",
    "Open API source creation",
    (
        "Open new-definition intake only when the owner explicitly wants to add a new or different "
        "API definition in the current Workspace. If the owner's current "
        "request has already authorized creating and analyzing an attached definition, continue "
        "that same request there instead of asking for the file again."
    ),
    "opened",
)
OPEN_API_SOURCE = operation(
    "sources.open_api_source",
    "Open API source",
    "Open one exact owner-scoped API Source version from Source Hub without changing it.",
    "opened",
    input_schema=OpenApiSourceArguments.model_json_schema(),
)
OPEN_API_DESCRIPTION = operation(
    "sources.open_api_description",
    "Open API description editor",
    "Open the exact selected API Source at its Markdown description editor without saving content.",
    "opened",
    input_schema=OpenApiDescriptionArguments.model_json_schema(),
    policy_refs=(policies.SOURCE_LIFECYCLE_TRUTH.ref,),
)
SAVE_API_DESCRIPTION = operation(
    "sources.save_api_description",
    "Save API description",
    (
        "Persist the exact Markdown file staged in this authenticated conversation as supporting "
        "context for the selected API Source without changing its API version."
    ),
    "saved",
    safety_class=SafetyClass.DRAFT,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    policy_refs=(policies.SOURCE_LIFECYCLE_TRUTH.ref,),
    outcome_schema={
        "type": "object",
        "properties": {
            "source_id": {"type": "string", "minLength": 16, "maxLength": 16},
            "source_revision_id": {"type": "string", "minLength": 16, "maxLength": 16},
            "description_id": {"type": "string", "minLength": 1},
            "filename": {"type": "string", "minLength": 1},
            "content_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
        "required": ["source_id", "source_revision_id", "description_id", "filename", "content_sha256"],
        "additionalProperties": False,
    },
)
DELETE_API_SOURCE = operation(
    "sources.delete_api_source",
    "Delete API source",
    (
        "Permanently delete the reviewed exact selected API Source only when active analysis and "
        "every declared Agent, design, and build dependency remain absent."
    ),
    "deleted",
    safety_class=SafetyClass.DESTRUCTIVE,
    review_policy=ReviewPolicy.REQUIRED,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    guard_refs=(SOURCE_DELETE_CURRENT_GUARD.ref,),
    policy_refs=(policies.SOURCE_LIFECYCLE_TRUTH.ref,),
    public_metadata={"review_surface_id": "sources.delete_review"},
    outcome_schema={
        "type": "object",
        "properties": {
            "source_id": {"type": "string", "minLength": 16, "maxLength": 16},
        },
        "required": ["source_id"],
        "additionalProperties": False,
    },
)
RETURN_TO_SOURCE_HUB = operation(
    "sources.return_to_source_hub",
    "Return to Source Hub",
    "Return from API Source to the owner Source inventory only when the owner asks to browse or leave the current API. This changes neither record.",
    "opened",
)
ACCEPT_STAGED_API = operation(
    "sources.accept_staged_api",
    "Add attached API definition",
    (
        "Create one accepted API Source version from the exact file staged in the "
        "current authenticated conversation. This does not start analysis or attach it to an Agent."
    ),
    "accepted",
    safety_class=SafetyClass.DRAFT,
    outcome_schema={
        "type": "object",
        "properties": {
            "source_id": {"type": "string", "minLength": 16, "maxLength": 16},
            "source_revision_id": {"type": "string", "minLength": 16, "maxLength": 16},
            "display_name": {"type": "string", "minLength": 1},
            "state": {"type": "string", "const": "accepted"},
        },
        "required": ["source_id", "source_revision_id", "display_name", "state"],
        "additionalProperties": False,
    },
)
PROCESS_API = operation(
    "sources.process_api",
    "Analyze API operations",
    (
        "Explicitly queue ToolRouter analysis for one accepted API version. "
        "With no Source identity, use the exact API definition added from this conversation."
    ),
    "queued",
    input_schema=ProcessApiSourceArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    policy_refs=(policies.PROCESSING_TRUTH.ref,),
    outcome_schema={
        "type": "object",
        "properties": {
            "source_id": {"type": "string", "minLength": 16, "maxLength": 16},
            "source_revision_id": {"type": "string", "minLength": 16, "maxLength": 16},
            "display_name": {"type": "string", "minLength": 1},
            "state": {"type": "string", "const": "queued"},
        },
        "required": ["source_id", "source_revision_id", "display_name", "state"],
        "additionalProperties": False,
    },
)
RETRY_PROCESSING = operation(
    "sources.retry_processing",
    "Retry API processing",
    "Explicitly queue another durable attempt for a failed API source revision.",
    "queued",
    input_schema=RetrySourceArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
)
SELECT_GRAPH_STAGE = operation(
    "sources.select_graph_stage",
    "Inspect recorded graph stage",
    "Select one stage from the exact owner-scoped persisted ToolRouter construction record.",
    "selected",
    input_schema=GraphStageArguments.model_json_schema(),
    safety_class=SafetyClass.STATE_SELECTION,
)
INSPECT_CURRENT_API = operation(
    "sources.inspect_current_api",
    "Inspect current API architecture",
    (
        "Read the one exact current ready API Source, its semantic groups, operations, saved "
        "profile count, and current curation before choosing a follow-up action. Use this only "
        "after readiness is already established; never call it after queued or running analysis "
        "as a readiness check."
    ),
    "inspected",
    safety_class=SafetyClass.STATE_SELECTION,
    sources=frozenset({OperationSource.AGENT}),
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    policy_refs=(policies.PROCESSING_TRUTH.ref, policies.API_OPERATION_CURATION_TRUTH.ref),
    outcome_schema={
        "type": "object",
        "properties": {
            "source_id": {"type": "string", "minLength": 16, "maxLength": 16},
            "source_revision_id": {"type": "string", "minLength": 16, "maxLength": 16},
            "revision_kind": {"type": "string"},
            "semantic_groups": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "operation_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["label", "operation_ids"],
                    "additionalProperties": False,
                },
            },
            "operations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "operation_id": {"type": "string"},
                        "method": {"type": "string"},
                        "path_template": {"type": "string"},
                    },
                    "required": ["operation_id", "method", "path_template"],
                    "additionalProperties": False,
                },
            },
            "saved_profile_count": {"type": "integer", "minimum": 0},
            "current_included_operation_ids": {
                "type": "array", "items": {"type": "string"}
            },
        },
        "required": [
            "source_id", "source_revision_id", "revision_kind", "semantic_groups",
            "operations", "saved_profile_count", "current_included_operation_ids"
        ],
        "additionalProperties": False,
    },
)
SAVE_API_CONNECTION = operation(
    "sources.save_api_connection",
    "Save API connection",
    "Persist one API-version-specific connection profile from the protected surface.",
    "saved",
    safety_class=SafetyClass.CREDENTIAL,
    sources=frozenset({OperationSource.SURFACE}),
)
TEST_API_CONNECTION = operation(
    "sources.test_api_connection",
    "Test API connection",
    "Run one explicitly selected safe read through the exact approved API version and saved profile.",
    "checked",
    input_schema=TestApiConnectionArguments.model_json_schema(),
    safety_class=SafetyClass.READ_EXTERNAL,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    guard_refs=(API_CONNECTION_CHECK_CURRENT_GUARD.ref,),
    policy_refs=(policies.API_CONNECTION_CHECK_TRUTH.ref,),
)
SAVE_API_OPERATION_CURATION = operation(
    "sources.save_api_operation_curation",
    "Save operation curation",
    (
        "Persist the owner's explicit operation selection for the exact current API inventory. "
        "For an agent call, pass only included_operation_ids explicitly named by the user; "
        "Corpus resolves the current Source identity and classifies every other discovered "
        "operation as excluded. Never enumerate or invent server-owned inventory identity."
    ),
    "saved",
    input_schema=SaveApiOperationCurationArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    guard_refs=(API_OPERATION_CURATION_CURRENT_GUARD.ref,),
    policy_refs=(policies.API_OPERATION_CURATION_TRUTH.ref,),
)
PREPARE_ROUTED_API_TEST = operation(
    "sources.prepare_routed_api_test",
    "Prepare routed API test",
    "Open a non-executing route-planning surface for the current Source context.",
    "opened",
    safety_class=SafetyClass.STATE_SELECTION,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    policy_refs=(policies.API_ROUTE_PLANNING_TRUTH.ref,),
)
ROUTE_PLAN_PUBLIC_OUTCOME_SCHEMA = {
    "type": "object",
    "properties": {
        "state": {
            "type": "string",
            "enum": ["ready", "needs_input", "needs_operation_choice", "not_routable"],
        },
        "question": {"type": ["string", "null"]},
        "choices": {"type": "array", "items": {"type": "string"}},
        "missing_inputs": {"type": "array", "items": {"type": "string"}},
        "method": {"type": ["string", "null"]},
        "path": {"type": ["string", "null"]},
    },
    "required": ["state", "question", "choices", "missing_inputs", "method", "path"],
    "additionalProperties": False,
}
CREATE_API_ROUTE_PLAN = operation(
    "sources.create_api_route_plan",
    "Plan routed API request",
    (
        "Prepare a non-executing ToolRouter plan for the owner's ordinary API request using "
        "the exact selected ready Source, current saved operation selection, and saved profile. "
        "Supply only explicitly known non-secret inputs; never invent Source, revision, profile, "
        "operation, credential, or conversation identities."
    ),
    "planned",
    input_schema=PrepareCurrentApiRoutePlanArguments.model_json_schema(),
    outcome_schema=ROUTE_PLAN_PUBLIC_OUTCOME_SCHEMA,
    safety_class=SafetyClass.DRAFT,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    policy_refs=(policies.API_ROUTE_PLANNING_TRUTH.ref,),
)
CONTINUE_API_ROUTE_PLAN = operation(
    "sources.continue_api_route_plan",
    "Answer routed API clarification",
    (
        "Continue the one current conversation-bound waiting API plan with the owner's ordinary "
        "non-secret answer. Corpus resolves the exact plan, expected record, missing input or "
        "user-facing operation choice server-side; never request or supply an internal plan ID."
    ),
    "continued",
    input_schema=ContinueCurrentApiRoutePlanArguments.model_json_schema(),
    outcome_schema=ROUTE_PLAN_PUBLIC_OUTCOME_SCHEMA,
    safety_class=SafetyClass.DRAFT,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    policy_refs=(policies.API_ROUTE_PLANNING_TRUTH.ref,),
)
OPAQUE_PLAN_ID_SCHEMA = {
    "type": "object",
    "properties": {"plan_id": {"type": "string", "minLength": 1}},
    "required": ["plan_id"],
    "additionalProperties": False,
}

TEST_ROUTED_API_READ = operation(
    "sources.test_routed_api_read",
    "Run routed API read",
    "Execute the one fully resolved read operation from the exact current opaque route plan.",
    "observed",
    input_schema=OPAQUE_PLAN_ID_SCHEMA,
    safety_class=SafetyClass.READ_EXTERNAL,
    guard_refs=(ROUTED_API_READ_CURRENT_GUARD.ref,),
    policy_refs=(policies.API_ROUTED_EXECUTION_TRUTH.ref,),
)
TEST_ROUTED_API_WRITE = operation(
    "sources.test_routed_api_write",
    "Run reviewed routed API write",
    "Execute the one fully resolved write operation only after explicit durable owner review.",
    "observed",
    input_schema=OPAQUE_PLAN_ID_SCHEMA,
    safety_class=SafetyClass.WRITE_EXTERNAL,
    review_policy=ReviewPolicy.REQUIRED,
    guard_refs=(ROUTED_API_WRITE_CURRENT_GUARD.ref,),
    policy_refs=(policies.API_ROUTED_EXECUTION_TRUTH.ref,),
    public_metadata={"review_surface_id": "sources.routed_api_write_review"},
    unknown_recovery_directive=(
        "Do not retry this write automatically. Preserve the redacted trace and verify "
        "the external system state before any explicit reconciliation or new reviewed attempt."
    ),
)
PROPOSE_CONTRACT_REVISION = operation(
    "sources.propose_contract_revision",
    "Prepare API version update",
    (
        "Validate and persist the exact local Medusa compatibility update without calling the API. "
        "This prepares evidence only; it does not stage the required owner review."
    ),
    "proposed",
    input_schema=ProposeContractRevisionArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    policy_refs=(policies.CONTRACT_REVISION_TRUTH.ref,),
    outcome_schema={
        "type": "object",
        "properties": {
            "proposal_state": {"const": "proposal_prepared"},
            "review_staged": {"const": False},
            "next_owner_decision": {"const": "request_owner_review"},
        },
        "required": [
            "proposal_state",
            "review_staged",
            "next_owner_decision",
        ],
        "additionalProperties": False,
    },
)
APPROVE_CONTRACT_REVISION = operation(
    "sources.approve_contract_revision",
    "Review API version update",
    (
        "Stage the durable owner review for creating one immutable API version. "
        "Staging is not approval; only a later explicit acceptance creates the version."
    ),
    "approved",
    input_schema=ApproveContractRevisionArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
    entity_inputs=(
        EntityInput(
            argument_name="proposal_ref",
            entity_kind="contract_revision_proposal",
        ),
    ),
    review_policy=ReviewPolicy.REQUIRED,
    additional_provider_refs=(SELECTED_API_SOURCE_PROVIDER.ref,),
    guard_refs=(CONTRACT_REVISION_CURRENT_GUARD.ref,),
    policy_refs=(policies.CONTRACT_REVISION_TRUTH.ref,),
    public_metadata={"review_surface_id": "sources.contract_revision_review"},
)

SOURCES_HOME_REF = NodeRef(id="sources.home")
SOURCES_API_INTAKE_REF = NodeRef(id="sources.api_intake")
SOURCES_API_REF = NodeRef(id="sources.api")
__all__ = [
    "ACCEPT_STAGED_API",
    "APPROVE_CONTRACT_REVISION",
    "CONTRACT_REVISION_CURRENT_GUARD",
    "CONTRACT_REVISION_PROPOSAL_PROVIDER",
    "SELECTED_API_SOURCE_PROVIDER",
    "INSPECT_CURRENT_API",
    "OPEN_API_CREATION",
    "OPEN_API_SOURCE",
    "OPEN_API_DESCRIPTION",
    "SAVE_API_DESCRIPTION",
    "DELETE_API_SOURCE",
    "SOURCE_DELETE_CURRENT_GUARD",
    "PREPARE_ROUTED_API_TEST",
    "CREATE_API_ROUTE_PLAN",
    "CONTINUE_API_ROUTE_PLAN",
    "PROCESS_API",
    "TEST_ROUTED_API_READ",
    "TEST_ROUTED_API_WRITE",
    "ROUTED_API_READ_CURRENT_GUARD",
    "ROUTED_API_WRITE_CURRENT_GUARD",
    "PROPOSE_CONTRACT_REVISION",
    "API_CONNECTION_FORM_ID",
    "API_CONNECTION_CHECK_CURRENT_GUARD",
    "API_OPERATION_CURATION_CURRENT_GUARD",
    "RETRY_PROCESSING",
    "RETURN_TO_HOME",
    "RETURN_TO_SOURCE_HUB",
    "SELECT_GRAPH_STAGE",
    "SAVE_API_CONNECTION",
    "SAVE_API_OPERATION_CURATION",
    "TEST_API_CONNECTION",
    "SOURCES_HOME_REF",
    "SOURCES_API_INTAKE_REF",
    "SOURCES_API_REF",
]
