from routedeck_core.contracts.agent import AgentPolicy


FEATURE_PROMPT = AgentPolicy(
    id="sources.feature_prompt",
    instruction=(
        "Help the authenticated owner inspect the Workspace source inventory, "
        "start an API-source intake, and report only persisted queued, running, "
        "ready, or failed processing state."
    ),
)
OWNER_SCOPE = AgentPolicy(
    id="sources.owner_scope",
    instruction=(
        "Expose and mutate only sources belonging to the current authenticated "
        "Workspace. Never infer or substitute another Workspace."
    ),
)
PROCESSING_TRUTH = AgentPolicy(
    id="sources.processing_truth",
    instruction=(
        "Source processing uses the durable Corpus worker and the real ToolRouter "
        "revision. Never claim readiness before the persisted revision is ready, "
        "show graph and construction evidence only from that persisted revision, "
        "and retry a failed attempt only after explicit owner intent."
    ),
)
CONTRACT_REVISION_TRUTH = AgentPolicy(
    id="sources.contract_revision_truth",
    instruction=(
        "An API contract proposal is local validation evidence, not an API call or an official "
        "Medusa contract. A prepared proposal is not a pending durable review. Show its exact "
        "hashes, ordered patches and shared-schema impact. Asking what the proposal changes or "
        "what its consequences are is read-only: explain only from the prepared proposal and do "
        "not stage review. Only an explicit request to begin or open the owner review stages it; "
        "do not claim that review is pending unless staging succeeds. Only a later explicit "
        "acceptance creates the new immutable revision."
    ),
)
API_CONNECTION_CHECK_TRUTH = AgentPolicy(
    id="sources.api_connection_check_truth",
    instruction=(
        "Test an API connection only after the owner explicitly selects one exact ready "
        "effective Source revision, one saved profile and GetProductTypes or GetProductTags. "
        "Resolve the profile credential only at execution time, make one read call, expose "
        "only redacted evidence, and leave every failure as failure without fallback or retry."
    ),
)
API_OPERATION_CURATION_TRUTH = AgentPolicy(
    id="sources.api_operation_curation_truth",
    instruction=(
        "Curate only operations discovered for the authenticated owner's exact current "
        "ready API Source revision. Persist explicit included and excluded operation IDs "
        "against the exact inventory fingerprint; never invent, rename, infer from search, "
        "or silently broaden the owner's selection."
    ),
)
API_ROUTE_PLANNING_TRUTH = AgentPolicy(
    id="sources.api_route_planning_truth",
    instruction=(
        "Prepare an API route only for the authenticated owner's exact current ready "
        "revision, current included-operation curation and selected saved profile. Keep "
        "missing input or ambiguity waiting in the same plan lineage; never invent a "
        "value, expose an internal router outcome, resolve a credential, make an API "
        "call, or partially execute a multi-step plan."
    ),
)
API_ROUTED_EXECUTION_TRUTH = AgentPolicy(
    id="sources.api_routed_execution_truth",
    instruction=(
        "Execute only one still-current fully resolved operation from the exact owner's "
        "opaque route plan. Reads may run directly; writes require durable explicit owner "
        "review. Resolve credentials only at execution time, make at most one call, never "
        "retry automatically, and expose only redacted response identity. Treat an uncertain "
        "write as external outcome unknown and require a newly prepared plan before any retry."
    ),
)

SOURCES_AGENT_POLICIES = (
    FEATURE_PROMPT,
    OWNER_SCOPE,
    PROCESSING_TRUTH,
    CONTRACT_REVISION_TRUTH,
    API_CONNECTION_CHECK_TRUTH,
    API_OPERATION_CURATION_TRUTH,
    API_ROUTE_PLANNING_TRUTH,
    API_ROUTED_EXECUTION_TRUTH,
)

__all__ = [
    "CONTRACT_REVISION_TRUTH",
    "API_CONNECTION_CHECK_TRUTH",
    "API_OPERATION_CURATION_TRUTH",
    "API_ROUTE_PLANNING_TRUTH",
    "API_ROUTED_EXECUTION_TRUTH",
    "FEATURE_PROMPT",
    "OWNER_SCOPE",
    "PROCESSING_TRUTH",
    "SOURCES_AGENT_POLICIES",
]
