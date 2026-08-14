from __future__ import annotations

from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import (
    DeepLinkPolicy,
    NodeKind,
    RecoveryPolicy,
    Route,
    Transition,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import (
    PrivateFormBinding,
    Surface,
    SurfaceAffordance,
    SurfaceLifecycle,
    SurfaceSlots,
)
from routedeck_core.contracts.suggestions import SuggestedAction

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.features.workspace.contracts import HOME_REF
from corpus.features.agents.contracts import AGENTS_CREATE_REF, AGENTS_HOME_REF
from corpus.features.builder.contracts import BUILDER_HOME_REF
from corpus.features.agents.contracts import (
    AGENT_ENTITY_PROVIDER,
    ATTACH_CREATED_SOURCE,
    OPEN_AGENT_BUILDS,
    OPEN_EXISTING_AGENT_FOR_SOURCE,
    OPEN_CREATE,
    RETURN_FROM_SOURCE,
)
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .declarations import (
    ACCEPT_STAGED_API,
    APPROVE_CONTRACT_REVISION,
    API_CONNECTION_FORM_ID,
    CONTRACT_REVISION_CURRENT_GUARD,
    CONTRACT_REVISION_PROPOSAL_PROVIDER,
    SELECTED_API_SOURCE_PROVIDER,
    INSPECT_CURRENT_API,
    OPEN_API_CREATION,
    OPEN_API_SOURCE,
    OPEN_API_DESCRIPTION,
    SAVE_API_DESCRIPTION,
    DELETE_API_SOURCE,
    SOURCE_DELETE_CURRENT_GUARD,
    PROPOSE_CONTRACT_REVISION,
    PREPARE_ROUTED_API_TEST,
    CREATE_API_ROUTE_PLAN,
    CONTINUE_API_ROUTE_PLAN,
    PROCESS_API,
    RETRY_PROCESSING,
    RETURN_TO_HOME,
    RETURN_TO_SOURCE_HUB,
    SELECT_GRAPH_STAGE,
    SAVE_API_CONNECTION,
    SAVE_API_OPERATION_CURATION,
    TEST_API_CONNECTION,
    TEST_ROUTED_API_READ,
    TEST_ROUTED_API_WRITE,
    API_CONNECTION_CHECK_CURRENT_GUARD,
    API_OPERATION_CURATION_CURRENT_GUARD,
    ROUTED_API_READ_CURRENT_GUARD,
    ROUTED_API_WRITE_CURRENT_GUARD,
    SOURCES_HOME_REF,
    SOURCES_API_INTAKE_REF,
    SOURCES_API_REF,
)
from . import policies


SOURCES_HOME_SURFACE = Surface(
    id="sources.home",
    component="sources.home",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "return_agent_ref": {"type": "string", "minLength": 1},
                "agent_handoff_mode": {"type": "string", "enum": ["create", "inspect"]},
                "selected_source_id": {"type": "string", "minLength": 16, "maxLength": 16},
                "selected_source_revision_id": {"type": "string", "minLength": 16, "maxLength": 16},
            },
            "additionalProperties": False,
        }
    ),
    affordances=(
        SurfaceAffordance(id="return_to_home", event="open", operation=RETURN_TO_HOME.ref),
        SurfaceAffordance(id="open_api_creation", event="open", operation=OPEN_API_CREATION.ref),
        SurfaceAffordance(id="open_api_source", event="open", operation=OPEN_API_SOURCE.ref),
        SurfaceAffordance(id="open_api_description", event="open", operation=OPEN_API_DESCRIPTION.ref),
        SurfaceAffordance(id="attach_created_source", event="submit", operation=ATTACH_CREATED_SOURCE.ref),
        SurfaceAffordance(id="return_to_agent", event="open", operation=RETURN_FROM_SOURCE.ref),
    ),
)

API_SOURCE_INTAKE_SURFACE = Surface(
    id="sources.api_intake",
    component="sources.api_intake",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "const": "create"},
                "return_agent_ref": {"type": "string", "minLength": 1},
                "agent_handoff_mode": {"type": "string", "enum": ["create", "inspect"]},
            },
            "additionalProperties": False,
        }
    ),
    affordances=(
        SurfaceAffordance(
            id="accept_staged_api",
            event="submit",
            operation=ACCEPT_STAGED_API.ref,
        ),
        SurfaceAffordance(
            id="return_to_source_hub",
            event="open",
            operation=RETURN_TO_SOURCE_HUB.ref,
        ),
        SurfaceAffordance(
            id="return_to_agent",
            event="open",
            operation=RETURN_FROM_SOURCE.ref,
        ),
    ),
    policy_refs=(
        policies.OWNER_SCOPE.ref,
        policies.STAGED_SETUP_CONTINUATION.ref,
    ),
)

API_SOURCE_SURFACE = Surface(
    id="sources.api",
    component="sources.api",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "form_handle": {"type": "string", "const": API_CONNECTION_FORM_ID},
                "mode": {"type": "string", "enum": ["create", "inspect"]},
                "return_agent_ref": {"type": "string", "minLength": 1},
                "agent_handoff_mode": {"type": "string", "enum": ["create", "inspect"]},
                "selected_source_id": {"type": "string", "minLength": 16, "maxLength": 16},
                "selected_source_revision_id": {"type": "string", "minLength": 16, "maxLength": 16},
                "attached_source_revision_id": {"type": "string", "minLength": 16, "maxLength": 16},
                "attachment_update_available": {"type": "boolean"},
                "return_context": {"type": "string", "enum": ["agent", "builder"]},
                "initial_workspace": {"type": "string", "enum": ["graph", "operations", "connection", "agent", "description"]},
            },
            "required": ["form_handle"],
            "additionalProperties": False,
        }
    ),
    private_form_binding=PrivateFormBinding(
        form_id_prop="form_handle",
        allowed_field_names=(
            "source_id",
            "profile_name",
            "environment",
            "base_url",
            "authentication_method",
            "credential_name",
            "credential_value",
        ),
    ),
    affordances=(
        SurfaceAffordance(
            id="return_to_source_hub",
            event="open",
            operation=RETURN_TO_SOURCE_HUB.ref,
        ),
        SurfaceAffordance(
            id="propose_contract_revision",
            event="submit",
            operation=PROPOSE_CONTRACT_REVISION.ref,
        ),
        SurfaceAffordance(
            id="select_graph_stage",
            event="select",
            operation=SELECT_GRAPH_STAGE.ref,
        ),
        SurfaceAffordance(
            id="save_api_connection",
            event="submit",
            operation=SAVE_API_CONNECTION.ref,
        ),
        SurfaceAffordance(
            id="test_api_connection",
            event="submit",
            operation=TEST_API_CONNECTION.ref,
        ),
        SurfaceAffordance(
            id="save_api_operation_curation",
            event="submit",
            operation=SAVE_API_OPERATION_CURATION.ref,
        ),
        SurfaceAffordance(
            id="prepare_routed_api_test",
            event="open",
            operation=PREPARE_ROUTED_API_TEST.ref,
        ),
        SurfaceAffordance(
            id="create_api_route_plan",
            event="submit",
            operation=CREATE_API_ROUTE_PLAN.ref,
        ),
        SurfaceAffordance(
            id="continue_api_route_plan",
            event="submit",
            operation=CONTINUE_API_ROUTE_PLAN.ref,
        ),
        SurfaceAffordance(
            id="process_api",
            event="submit",
            operation=PROCESS_API.ref,
        ),
        SurfaceAffordance(
            id="open_api_description",
            event="open",
            operation=OPEN_API_DESCRIPTION.ref,
        ),
        SurfaceAffordance(
            id="save_api_description",
            event="submit",
            operation=SAVE_API_DESCRIPTION.ref,
        ),
        SurfaceAffordance(
            id="delete_api_source",
            event="submit",
            operation=DELETE_API_SOURCE.ref,
        ),
        SurfaceAffordance(
            id="retry_processing",
            event="submit",
            operation=RETRY_PROCESSING.ref,
        ),
        SurfaceAffordance(
            id="attach_created_source",
            event="submit",
            operation=ATTACH_CREATED_SOURCE.ref,
        ),
        SurfaceAffordance(
            id="return_to_agent",
            event="open",
            operation=RETURN_FROM_SOURCE.ref,
        ),
        SurfaceAffordance(
            id="return_to_builder",
            event="open",
            operation=OPEN_AGENT_BUILDS.ref,
        ),
        SurfaceAffordance(
            id="open_agent_inventory",
            event="open",
            operation=OPEN_EXISTING_AGENT_FOR_SOURCE.ref,
        ),
        SurfaceAffordance(
            id="open_agent_creation",
            event="open",
            operation=OPEN_CREATE.ref,
        ),
    ),
)

API_OPERATION_TEST_SURFACE = Surface(
    id="sources.api_operation_test",
    component="sources.api_operation_test",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "open": {"type": "boolean", "const": True},
                "source_id": {
                    "type": "string",
                    "minLength": 16,
                    "maxLength": 16,
                },
                "source_revision_id": {
                    "type": "string",
                    "minLength": 16,
                    "maxLength": 16,
                },
            },
            "additionalProperties": False,
        }
    ),
    affordances=(
        SurfaceAffordance(
            id="create_api_route_plan",
            event="submit",
            operation=CREATE_API_ROUTE_PLAN.ref,
        ),
        SurfaceAffordance(
            id="continue_api_route_plan",
            event="submit",
            operation=CONTINUE_API_ROUTE_PLAN.ref,
        ),
        SurfaceAffordance(
            id="run_routed_api_read",
            event="submit",
            operation=TEST_ROUTED_API_READ.ref,
        ),
        SurfaceAffordance(
            id="review_routed_api_write",
            event="submit",
            operation=TEST_ROUTED_API_WRITE.ref,
        ),
    ),
    policy_refs=(policies.API_ROUTE_PLANNING_TRUTH.ref,),
)

ROUTED_API_WRITE_REVIEW_SURFACE = Surface(
    id="sources.routed_api_write_review",
    component="sources.routed_api_write_review",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "state": {"type": "string", "const": "pending"},
                "review_id": {"type": "string", "minLength": 1},
                "expires_at": {"type": "string", "minLength": 1},
            },
            "additionalProperties": False,
        }
    ),
    policy_refs=(policies.API_ROUTED_EXECUTION_TRUTH.ref,),
)

SOURCE_DELETE_REVIEW_SURFACE = Surface(
    id="sources.delete_review",
    component="sources.delete_review",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "state": {"type": "string", "const": "pending"},
                "review_id": {"type": "string", "minLength": 1},
                "expires_at": {"type": "string", "minLength": 1},
            },
            "additionalProperties": False,
        }
    ),
    policy_refs=(policies.SOURCE_LIFECYCLE_TRUTH.ref,),
)

CONTRACT_REVISION_PROPOSAL_SURFACE = Surface(
    id="sources.contract_revision_proposal",
    component="sources.contract_revision_proposal",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "source_id": {"type": "string", "minLength": 16, "maxLength": 16},
                "proposal_ref": {"type": "string", "minLength": 1},
            },
            "additionalProperties": False,
        }
    ),
    affordances=(
        SurfaceAffordance(
            id="approve_contract_revision",
            event="submit",
            operation=APPROVE_CONTRACT_REVISION.ref,
        ),
    ),
    policy_refs=(policies.CONTRACT_REVISION_TRUTH.ref,),
)

CONTRACT_REVISION_REVIEW_SURFACE = Surface(
    id="sources.contract_revision_review",
    component="sources.contract_revision_review",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "state": {"type": "string", "const": "pending"},
                "review_id": {"type": "string", "minLength": 1},
                "expires_at": {"type": "string", "minLength": 1},
            },
            "additionalProperties": False,
        }
    ),
    policy_refs=(policies.CONTRACT_REVISION_TRUTH.ref,),
)

SOURCES_CAPABILITY = Capability(
    id="sources.manage",
    title="Manage owner Sources through registered connectors",
    operations=(
        OPEN_API_CREATION.ref,
        OPEN_API_SOURCE.ref,
        OPEN_API_DESCRIPTION.ref,
        SAVE_API_DESCRIPTION.ref,
        DELETE_API_SOURCE.ref,
        PROCESS_API.ref,
        INSPECT_CURRENT_API.ref,
        RETRY_PROCESSING.ref,
        RETURN_TO_HOME.ref,
        RETURN_TO_SOURCE_HUB.ref,
        SELECT_GRAPH_STAGE.ref,
        SAVE_API_CONNECTION.ref,
        TEST_API_CONNECTION.ref,
        SAVE_API_OPERATION_CURATION.ref,
        PREPARE_ROUTED_API_TEST.ref,
        CREATE_API_ROUTE_PLAN.ref,
        CONTINUE_API_ROUTE_PLAN.ref,
        TEST_ROUTED_API_READ.ref,
        TEST_ROUTED_API_WRITE.ref,
        PROPOSE_CONTRACT_REVISION.ref,
        APPROVE_CONTRACT_REVISION.ref,
        ATTACH_CREATED_SOURCE.ref,
        RETURN_FROM_SOURCE.ref,
        OPEN_AGENT_BUILDS.ref,
        OPEN_EXISTING_AGENT_FOR_SOURCE.ref,
        OPEN_CREATE.ref,
    ),
    surfaces=(
        SOURCES_HOME_SURFACE.ref,
        API_SOURCE_SURFACE.ref,
        CONTRACT_REVISION_PROPOSAL_SURFACE.ref,
        CONTRACT_REVISION_REVIEW_SURFACE.ref,
        API_OPERATION_TEST_SURFACE.ref,
        ROUTED_API_WRITE_REVIEW_SURFACE.ref,
        SOURCE_DELETE_REVIEW_SURFACE.ref,
    ),
    policy_refs=(
        policies.OWNER_SCOPE.ref,
        policies.PROCESSING_TRUTH.ref,
        policies.STAGED_SETUP_CONTINUATION.ref,
        policies.ACTIVE_API_CONTINUATION.ref,
        policies.API_CONNECTION_CHECK_TRUTH.ref,
        policies.API_OPERATION_CURATION_TRUTH.ref,
        policies.API_ROUTE_PLANNING_TRUTH.ref,
        policies.API_ROUTED_EXECUTION_TRUTH.ref,
        policies.SOURCE_LIFECYCLE_TRUTH.ref,
    ),
)

SOURCES_INTAKE_CAPABILITY = Capability(
    id="sources.intake",
    title="Add one new API definition",
    operations=(
        ACCEPT_STAGED_API.ref,
        RETURN_TO_SOURCE_HUB.ref,
        RETURN_FROM_SOURCE.ref,
    ),
    surfaces=(API_SOURCE_INTAKE_SURFACE.ref,),
    policy_refs=(
        policies.OWNER_SCOPE.ref,
        policies.STAGED_SETUP_CONTINUATION.ref,
    ),
)

SOURCES_HOME_NODE = Node(
    id=SOURCES_HOME_REF.id,
    title="Sources",
    kind=NodeKind.SECTION,
    parent=HOME_REF,
    route=Route(
        template="/sources",
        deep_link_policy=DeepLinkPolicy.SESSION_BOUND,
    ),
    context_providers=(OWNER_CONTEXT_PROVIDER, SELECTED_API_SOURCE_PROVIDER),
    operations=(OPEN_API_CREATION, OPEN_API_SOURCE, OPEN_API_DESCRIPTION, RETURN_TO_HOME, ATTACH_CREATED_SOURCE, RETURN_FROM_SOURCE),
    outgoing=(
        Transition(
            operation=OPEN_API_CREATION.ref,
            outcome="opened",
            target=SOURCES_API_INTAKE_REF,
        ),
        Transition(operation=OPEN_API_SOURCE.ref, outcome="opened", target=SOURCES_API_REF),
        Transition(operation=OPEN_API_DESCRIPTION.ref, outcome="opened", target=SOURCES_API_REF),
        Transition(
            operation=ATTACH_CREATED_SOURCE.ref,
            outcome="attached",
            target=AGENTS_HOME_REF,
        ),
        Transition(
            operation=RETURN_FROM_SOURCE.ref,
            outcome="opened",
            target=AGENTS_HOME_REF,
        ),
        Transition(
            operation=RETURN_TO_HOME.ref,
            outcome="opened",
            target=HOME_REF,
        ),
    ),
    capabilities=(SOURCES_CAPABILITY,),
    entity_providers=(AGENT_ENTITY_PROVIDER,),
    surfaces=SurfaceSlots(active=SOURCES_HOME_SURFACE),
    suggested_actions=(
        SuggestedAction(
            id="sources.add_api",
            operation_id=OPEN_API_CREATION.id,
            label="Add API source",
        ),
    ),
    policy_refs=(
        policies.OWNER_SCOPE.ref,
        policies.PROCESSING_TRUTH.ref,
        policies.STAGED_SETUP_CONTINUATION.ref,
        policies.API_CONNECTION_CHECK_TRUTH.ref,
        policies.API_OPERATION_CURATION_TRUTH.ref,
        policies.API_ROUTE_PLANNING_TRUTH.ref,
        policies.API_ROUTED_EXECUTION_TRUTH.ref,
        policies.SOURCE_LIFECYCLE_TRUTH.ref,
    ),
)

SOURCES_API_INTAKE_NODE = Node(
    id=SOURCES_API_INTAKE_REF.id,
    title="New API Source",
    kind=NodeKind.WORKFLOW,
    parent=SOURCES_HOME_REF,
    route=Route(template="/sources/api/new", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
    context_providers=(OWNER_CONTEXT_PROVIDER, SELECTED_API_SOURCE_PROVIDER),
    operations=(
        ACCEPT_STAGED_API,
        RETURN_TO_SOURCE_HUB,
        RETURN_FROM_SOURCE,
    ),
    outgoing=(
        Transition(operation=ACCEPT_STAGED_API.ref, outcome="accepted", target=SOURCES_API_REF),
        Transition(operation=RETURN_TO_SOURCE_HUB.ref, outcome="opened", target=SOURCES_HOME_REF),
        Transition(operation=RETURN_FROM_SOURCE.ref, outcome="opened", target=AGENTS_HOME_REF),
    ),
    capabilities=(SOURCES_INTAKE_CAPABILITY,),
    entity_providers=(AGENT_ENTITY_PROVIDER,),
    surfaces=SurfaceSlots(active=API_SOURCE_INTAKE_SURFACE),
    policy_refs=(
        policies.OWNER_SCOPE.ref,
        policies.STAGED_SETUP_CONTINUATION.ref,
    ),
)

SOURCES_API_NODE = Node(
    id=SOURCES_API_REF.id,
    title="API Source",
    kind=NodeKind.WORKFLOW,
    parent=SOURCES_HOME_REF,
    route=Route(template="/sources/api", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
    context_providers=(OWNER_CONTEXT_PROVIDER, SELECTED_API_SOURCE_PROVIDER),
    operations=(
        PROCESS_API,
        OPEN_API_DESCRIPTION,
        SAVE_API_DESCRIPTION,
        DELETE_API_SOURCE,
        INSPECT_CURRENT_API,
        RETRY_PROCESSING,
        RETURN_TO_SOURCE_HUB,
        SELECT_GRAPH_STAGE,
        SAVE_API_CONNECTION,
        TEST_API_CONNECTION,
        SAVE_API_OPERATION_CURATION,
        PREPARE_ROUTED_API_TEST,
        CREATE_API_ROUTE_PLAN,
        CONTINUE_API_ROUTE_PLAN,
        TEST_ROUTED_API_READ,
        TEST_ROUTED_API_WRITE,
        PROPOSE_CONTRACT_REVISION,
        APPROVE_CONTRACT_REVISION,
        ATTACH_CREATED_SOURCE,
        RETURN_FROM_SOURCE,
        OPEN_AGENT_BUILDS,
        OPEN_EXISTING_AGENT_FOR_SOURCE,
        OPEN_CREATE,
    ),
    outgoing=(
        Transition(operation=PROCESS_API.ref, outcome="queued", target=SOURCES_API_REF),
        Transition(operation=OPEN_API_DESCRIPTION.ref, outcome="opened", target=SOURCES_API_REF),
        Transition(operation=SAVE_API_DESCRIPTION.ref, outcome="saved", target=SOURCES_API_REF),
        Transition(operation=DELETE_API_SOURCE.ref, outcome="deleted", target=SOURCES_HOME_REF),
        Transition(operation=INSPECT_CURRENT_API.ref, outcome="inspected", target=SOURCES_API_REF),
        Transition(operation=PROPOSE_CONTRACT_REVISION.ref, outcome="proposed", target=SOURCES_API_REF),
        Transition(operation=APPROVE_CONTRACT_REVISION.ref, outcome="approved", target=SOURCES_API_REF),
        Transition(operation=RETRY_PROCESSING.ref, outcome="queued", target=SOURCES_API_REF),
        Transition(operation=RETURN_TO_SOURCE_HUB.ref, outcome="opened", target=SOURCES_HOME_REF),
        Transition(operation=ATTACH_CREATED_SOURCE.ref, outcome="attached", target=AGENTS_HOME_REF),
        Transition(operation=RETURN_FROM_SOURCE.ref, outcome="opened", target=AGENTS_HOME_REF),
        Transition(operation=OPEN_AGENT_BUILDS.ref, outcome="opened", target=BUILDER_HOME_REF),
        Transition(operation=OPEN_EXISTING_AGENT_FOR_SOURCE.ref, outcome="opened", target=AGENTS_HOME_REF),
        Transition(operation=OPEN_CREATE.ref, outcome="opened", target=AGENTS_CREATE_REF),
        Transition(operation=SELECT_GRAPH_STAGE.ref, outcome="selected", target=SOURCES_API_REF),
        Transition(operation=SAVE_API_CONNECTION.ref, outcome="saved", target=SOURCES_API_REF),
        Transition(operation=TEST_API_CONNECTION.ref, outcome="checked", target=SOURCES_API_REF),
        Transition(operation=SAVE_API_OPERATION_CURATION.ref, outcome="saved", target=SOURCES_API_REF),
        Transition(operation=PREPARE_ROUTED_API_TEST.ref, outcome="opened", target=SOURCES_API_REF),
        Transition(operation=CREATE_API_ROUTE_PLAN.ref, outcome="planned", target=SOURCES_API_REF),
        Transition(operation=CONTINUE_API_ROUTE_PLAN.ref, outcome="continued", target=SOURCES_API_REF),
        Transition(operation=TEST_ROUTED_API_READ.ref, outcome="observed", target=SOURCES_API_REF),
        Transition(operation=TEST_ROUTED_API_WRITE.ref, outcome="observed", target=SOURCES_API_REF),
    ),
    capabilities=(SOURCES_CAPABILITY,),
    entity_providers=(AGENT_ENTITY_PROVIDER, CONTRACT_REVISION_PROPOSAL_PROVIDER),
    guards=(
        CONTRACT_REVISION_CURRENT_GUARD,
        API_CONNECTION_CHECK_CURRENT_GUARD,
        API_OPERATION_CURATION_CURRENT_GUARD,
        ROUTED_API_READ_CURRENT_GUARD,
        ROUTED_API_WRITE_CURRENT_GUARD,
        SOURCE_DELETE_CURRENT_GUARD,
    ),
    surfaces=SurfaceSlots(
        active=API_SOURCE_SURFACE,
        detail=(CONTRACT_REVISION_PROPOSAL_SURFACE, API_OPERATION_TEST_SURFACE),
        review=(CONTRACT_REVISION_REVIEW_SURFACE, ROUTED_API_WRITE_REVIEW_SURFACE, SOURCE_DELETE_REVIEW_SURFACE),
    ),
    recovery=RecoveryPolicy(
        directives=(
            "Do not retry this write automatically. Preserve the redacted trace and verify the external system state before any explicit reconciliation or new reviewed attempt.",
        ),
        failure_surface=API_OPERATION_TEST_SURFACE.ref,
    ),
    suggested_actions=(
        SuggestedAction(
            id="api-test-operation",
            operation_id=PREPARE_ROUTED_API_TEST.id,
            label="Try an API request",
        ),
    ),
    policy_refs=(
        policies.OWNER_SCOPE.ref,
        policies.PROCESSING_TRUTH.ref,
        policies.ACTIVE_API_CONTINUATION.ref,
        policies.API_CONNECTION_CHECK_TRUTH.ref,
        policies.API_OPERATION_CURATION_TRUTH.ref,
        policies.API_ROUTE_PLANNING_TRUTH.ref,
        policies.API_ROUTED_EXECUTION_TRUTH.ref,
        policies.SOURCE_LIFECYCLE_TRUTH.ref,
    ),
)

SOURCES_FEATURE = Feature(
    namespace="sources",
    nodes=(SOURCES_HOME_NODE, SOURCES_API_INTAKE_NODE, SOURCES_API_NODE),
    agent_policies=policies.SOURCES_AGENT_POLICIES,
    policy_refs=(
        policies.FEATURE_PROMPT.ref,
        policies.OWNER_SCOPE.ref,
        policies.PROCESSING_TRUTH.ref,
        policies.API_CONNECTION_CHECK_TRUTH.ref,
        policies.API_OPERATION_CURATION_TRUTH.ref,
        policies.API_ROUTE_PLANNING_TRUTH.ref,
        policies.API_ROUTED_EXECUTION_TRUTH.ref,
        policies.SOURCE_LIFECYCLE_TRUTH.ref,
    ),
)


__all__ = [
    "CONTRACT_REVISION_PROPOSAL_SURFACE",
    "CONTRACT_REVISION_REVIEW_SURFACE",
    "API_OPERATION_TEST_SURFACE",
    "ROUTED_API_WRITE_REVIEW_SURFACE",
    "SOURCE_DELETE_REVIEW_SURFACE",
    "SOURCES_HOME_SURFACE",
    "API_SOURCE_SURFACE",
    "SOURCES_FEATURE",
    "SOURCES_HOME_NODE",
    "SOURCES_API_NODE",
]
