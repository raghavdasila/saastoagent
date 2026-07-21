# Corpus Behavior Reference

Verified against the standalone SaaStoAgent v0.1 source and tests on
2026-07-20.

The verified implementation is now preserved under
`benchmark/saastoagent-v0.1/`. Source paths in this document are relative to
that benchmark root unless stated otherwise. This document remains at the new
repository root so the redesign can compare against proven behavior without
importing benchmark code.

## Purpose And Authority

This document is the canonical description of the behavior currently
implemented by Corpus. It records what the product does now so that a later
RouteDeck migration can preserve behavior intentionally instead of treating the
current package shape as the target architecture.

This is a behavior reference, not a RouteDeck framework specification. The
current implementation uses the vendored RouteDeck v0 compatibility runtime in
`vendor/routedeck-v0-compat/`. The standalone RouteDeck repository has evolved
beyond that runtime. When this document conflicts with live source or executable
tests, source and tests win and this document must be updated.

Primary evidence:

- `backend/corpus/graph/definitions.py`
- `backend/corpus/graph/app.py`
- `backend/corpus/schemas/graph.py`
- `backend/routes/corpus_graph.py`
- `frontend/src/components/corpus/`
- `backend/tests/test_corpus_*.py`
- `backend/tests/test_app_graph_contract.py`
- `backend/tests/test_routedeck_schema_boundary.py`
- `frontend/scripts/e2e-docker.mjs`
- `frontend/scripts/e2e-medusa-docker.mjs`

## Product Boundary

Corpus is the SaaStoAgent owner-workbench agent. It helps an authenticated owner
create and select SaaS Agents, connect APIs, inspect generated catalogs, plan
executions, review approvals and results, manage instructions, knowledge and
memory, review learning evidence, and run QA.

Corpus does not currently run inside a deployed public agent. The public
`/a/{slug}` experience uses the separate deployed-agent chat runtime described
under [Deployed-Agent Relationship](#deployed-agent-relationship). Corpus and
deployed agents share product records such as SaaS Agents, connections, generated
tools, execution traces, learning candidates, knowledge, and memory; they do not
share the Corpus navigation graph or Corpus SSE protocol.

The runtime ownership chain is:

```text
Corpus definitions and handlers own product meaning and side effects
  -> RouteDeck compatibility runtime validates state and legal operations
    -> projection exposes current navigation, surfaces, context, and capabilities
      -> React renders product components and dispatches typed operations
```

The model may choose among legal product operations, but it does not write graph
state directly and it does not receive internal route operations as planning
vocabulary.

## Public Corpus API

| Endpoint | Behavior |
| --- | --- |
| `GET /api/corpus/state` | Resolves the optional browser location and owner/agent context, applies eligibility guards, and returns `state`, a RouteDeck `projection`, and an optional canonical `replace_path`. |
| `POST /api/corpus/action` | Dispatches one typed `operation_id` with `args` through the RouteDeck runtime and returns updated state/projection, an optional active review surface, messages, and replacement path. |
| `GET /api/corpus/stream` | With no user input, streams the runtime projection. With user input, runs a Corpus model turn, validates its plan against current legality, dispatches or stages the selected operation, and streams response events. |
| `GET /api/diagnostics/stream` | Emits one read-only `diagnostic_event` containing the manifest, runtime snapshot, introspection, and projection. It does not mutate product state. |

All four endpoints accept owner context through the current optional-auth
dependency. A request outside the anonymous home/auth lane is redirected by
runtime eligibility rules rather than being allowed to manufacture an
authenticated state.

## State And Projection Contract

Corpus state extends RouteDeck graph state with:

- the current node and executed-node history;
- selected SaaS Agent and connection IDs;
- an optional pending execution trace;
- current and pending operation/review state;
- active surface and surface presentation state;
- back and forward navigation stacks;
- graph context used by active product surfaces.

The projection is the frontend source of truth for:

- current graph node and canonical location;
- legal operations and their dispatch readiness;
- current, back, and forward navigation locations;
- active and frame surfaces;
- the Corpus context lens;
- capability-rail data;
- node hierarchy, blocked operations, guard explanations, and diagnostics.

React keeps local UI state such as form edits, busy indicators, and an unsaved
changes prompt. It does not independently decide graph legality or persist a
second authoritative graph state. Browser locations are reconciled back through
a typed internal RouteDeck navigation operation.

## Current Graph Vocabulary

The current graph version is `corpus_routedeck_v1` and declares 26 nodes:

| Area | Nodes |
| --- | --- |
| Entry and identity | `home`, `auth_sign_in`, `auth_register` |
| SaaS Agent selection | `saas_agent_select`, `saas_agent_create`, `agent_home` |
| Setup and catalog | `instructions`, `connection_configure`, `schema_preview`, `catalog_activation`, `catalog`, `entities`, `actions` |
| Execution | `execution_planning`, `needs_input`, `approval_required`, `executing`, `result_review` |
| Agent content | `knowledge`, `memory` |
| Learning | `learning`, `learning.policy_candidate`, `learning.execution_trace`, `learning.active_policy` |
| Assurance and recovery | `qa`, `recovery` |

It declares 40 typed operations. Product-visible operations cover:

- home, authentication, SaaS Agent list/open/create, and agent home;
- deployment settings and instructions;
- connection preview and activation;
- catalog, entity, and action views;
- execution planning, missing input, approval, rejection, and result review;
- knowledge generation and memory save;
- learning views, evidence review, approval, and rejection;
- QA execution and recovery.

Five additional operations are runtime plumbing and remain hidden from ordinary
Corpus planning and product quick actions:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

The capability rail projects the owner journey as Home, Create Agent, Connect
API, Catalog, Actions, Execution, Knowledge, Memory, Learning, and QA. Items are
enabled by the legal operations in the current projection, not by a separate
frontend route table.

## Guards And Reachability

Current runtime guards enforce these observable rules:

- Anonymous users can use home and auth surfaces only.
- Authenticated users without a selected SaaS Agent are sent to agent selection
  before agent-specific work.
- A selected agent is membership-checked before its state is projected.
- Catalog, entities, actions, and execution entry require a connection.
- Execution planning requires at least one generated tool; otherwise the owner
  is sent to connection setup.
- Approval actions require a pending execution trace.
- Unknown nodes resolve to recovery rather than becoming arbitrary graph state.

The projection includes both currently legal operations and diagnostic reasons
for blocked operations. Corpus planning receives only the legal, product-facing
subset.

## Direct Interaction Behavior

Buttons, forms, the capability rail, browser history reconciliation, and chat
all converge on RouteDeck dispatch.

A direct product interaction follows this sequence:

1. React reads the current operation from the projection.
2. The UI refuses operations whose projection says they cannot dispatch now.
3. The client posts the typed operation and declared arguments to
   `/api/corpus/action`.
4. RouteDeck validates the operation against the current node and stages review
   when required.
5. A Corpus handler performs the product side effect or navigation transition.
6. The response replaces client RouteDeck state and synchronizes the canonical
   browser path without remounting the app shell.

Surface-hosted operations can collect or save inputs inside their active
surface. Other review-mode operations are staged on the generic operation-review
surface before a commit. Unsaved instructions and other dirty surfaces invoke a
three-way prompt: save and continue, keep working, or continue without saving.

## Chat Planning And Dispatch

A Corpus chat turn follows this sequence:

1. Snapshot current state and projection.
2. Build `planning_context` from the current node, active SaaS Agent, active
   surface, available peer surfaces, visible selectable entities, and legal
   product operations.
3. Require a configured OpenAI key. Missing configuration fails the chat request
   with HTTP 503; there is no mock or alternate-model fallback.
4. Ask the model for a typed JSON decision: `reply_now`, `open_surface`,
   `clarify`, `deep_work`, or `propose_operation`.
5. Normalize the decision. Unknown intents, illegal/hidden operation IDs,
   undeclared arguments, and unknown surface IDs collapse to a safe
   clarification instead of dispatch.
6. Optionally resolve an explicit navigation request against currently legal,
   auto-dispatchable operations. This is a legality-scoped post-plan
   disambiguator, not the retired phrase-to-route table; ambiguous ties are not
   dispatched.
7. Switch a legal peer surface, dispatch/stage a legal operation, or stream an
   informational response.
8. Generate the assistant-facing operation reply from the committed effect
   summary and active surface, then finish with the resulting projection
   version.

Visible selectable entities can expose a bound operation payload for the model
to reuse. In the current v0 implementation, the SaaS Agent list exposes real
agent IDs in those bound arguments, capped at 25 visible entries. That is a
current compatibility behavior, not a recommendation for a future framework
boundary.

Normal conversational reply context removes operation IDs, argument payloads,
surface IDs, input schemas, and required/missing argument details. The
operation-reply prompt also removes the internal operation ID and instructs the
model not to mention route, node, component, operation, or surface identifiers.

## Corpus Stream Events

Every `/api/corpus/stream` event includes a generated `turn_id`. Model-backed
turns use these event types:

| Event | Meaning |
| --- | --- |
| `corpus_status` | The model planner is thinking. |
| `projection_update` | A surface presentation intent changed projection state before operation dispatch. |
| RouteDeck runtime event | A typed operation committed or was staged; the current implementation forwards the first runtime event. |
| `message_delta` | A chunk of the conversational or post-operation reply. |
| `corpus_done` | The turn completed with status such as `committed`, `review`, `reply_now`, `clarify`, or `deep_work`. |
| `corpus_error` | Planning or reply generation failed. Operation-reply failure explicitly reports that the operation may already have completed. |

The frontend updates status and chat text incrementally. Projection-bearing
events replace the RouteDeck client state; `corpus_done` ends the busy state;
`corpus_error` surfaces failure rather than presenting success.

## Surface Behavior

Corpus projects a frame surface plus one or more active surfaces. Active
components currently include authentication, SaaS Agent selection, instructions,
connection setup, schema preview, catalog/entities/actions, execution,
knowledge, memory, learning, QA, recovery, and operation review.

Learning demonstrates two distinct surface behaviors:

- peer surfaces switch among policy gaps, failed executions, active policies,
  and rejected evidence without changing the parent `learning` node;
- detail review nodes open a policy candidate, execution trace, or active policy
  as a child review workflow.

Stale detail/review surfaces are not silently rehydrated after the backing
review state disappears. The runtime projects an eligible current/default
surface instead.

## Product Workflows

| Workflow | Current behavior |
| --- | --- |
| Authentication | Sign-in and registration are real active forms. Merely opening a form is not reported as successful authentication. |
| Agent setup | Owners create/select an agent, edit instructions and deployment settings, then work within agent-scoped routes. |
| Connection | Preview parses connection/spec input; activation persists discovery output, generated tools, and router index state before catalog/execution become ready. |
| Catalog | Catalog, entities, and actions render the activated provider/discovery records for the selected agent. |
| Execution | A goal is matched to generated tools, declared inputs are collected, risky work can enter approval, and results are recorded in execution traces. |
| Knowledge and memory | Owners generate knowledge and save agent-scoped memory through typed operations and services. |
| Learning | Owners inspect trace-derived or policy-gap evidence and explicitly approve or reject candidates/policies. |
| QA | The QA surface runs the project QA service and displays its product result. |
| Recovery | Invalid graph locations become the recovery node, with a typed path back home. |

## Failure, Safety, And Privacy Semantics

- Missing LLM configuration fails Corpus chat loudly; it does not silently
  produce a canned or heuristic response.
- Model planning failure emits `corpus_error` and stops the turn.
- Illegal operations, invalid surface IDs, and unsupported arguments do not
  dispatch.
- Review-required operations remain pending until explicitly committed or
  rejected.
- Membership and readiness guards are evaluated on the backend.
- Credential-like fields (`credentials`, `password`, `token`, `api_key`) are
  masked by the graph's sensitive-data policy.
- Diagnostics are a separate, read-only endpoint and are not normal public chat
  vocabulary.
- Public deployed chat suppresses internal tool-start/tool-end events and uses a
  separate public-safe response path.

## Deployed-Agent Relationship

The deployed-agent path is deliberately separate today:

```text
GET /api/deployed-agents/{slug}
  -> resolve enabled deployment and visitor-auth policy

POST /api/deployed-agents/{slug}/chat
  -> rate-limit/check visitor access
  -> create or resume AgentSession
  -> load agent instructions, memory, and history
  -> run deterministic REST operator first
     -> ToolRouter chooses generated API candidates
     -> execution frame carries variables and workflow state
     -> policy/approval rules gate writes and hidden dependencies
     -> execution trace and learning evidence are persisted
  -> otherwise run the SaaS Agent LangGraph conversation
  -> stream public-safe SSE and persist the assistant message
```

Owner decisions can still affect deployed behavior through shared records:

- deployment enablement, visitor authentication, execution mode, and write
  policy are configured from owner surfaces;
- approved learning policies/hints are consumed by deployed REST orchestration;
- deployed failures and policy gaps create traces or candidates that become
  visible in Corpus learning surfaces;
- knowledge, memory, instructions, connections, generated tools, and router
  indexes are scoped to the same SaaS Agent.

This is data and policy integration, not integration of the Corpus graph agent
itself. The deployed endpoints do not call `/api/corpus/*`, instantiate
`CorpusRouteDeckRuntime`, consume Corpus projections, or render Corpus surfaces.

## Verification Evidence

The following current contract suites define the behavior boundary:

| Evidence | Protected behavior |
| --- | --- |
| `test_corpus_graph_contract.py` | Projection, navigation dispatch, handler cleanup, stale review behavior, and stream-turn commit through RouteDeck. |
| `test_corpus_routedeck_runtime.py` | Snapshot/dispatch/stream protocol, context lens, projection, and browser route conversion. |
| `test_corpus_routedeck_state.py` | Operation policy, bound operations, active surfaces, and learning peer/detail behavior. |
| `test_corpus_turn_planning.py` | Planning context, entity bindings, declared arguments, surface intents, and rejection of illegal or hidden plans. |
| `test_corpus_runtime_structure.py` | Active package boundary, explicit dispatcher, thin RouteDeck adapters, and retired legacy packages. |
| `test_corpus_surface_structure.py` | Product surface components and thin rendering adapter. |
| `test_app_graph_contract.py` | Owner shell, auth, controls, deployment, diagnostics, public chat, graph-owned legality, and no legacy app-graph API. |
| `test_routedeck_schema_boundary.py` | Direct RouteDeck schema boundary. |
| `e2e-docker.mjs` | Real owner-workbench behavior through the running Docker application. |
| `e2e-medusa-docker.mjs` | Real Medusa-backed connection, catalog, execution, deployment, and public-agent path. |

On 2026-07-20, the standalone repository passed the complete backend suite
(`273 passed`) and the Docker owner/deployed browser E2E on the local stack.
Those run results establish the current extraction baseline; they do not prove
parity with a future canonical RouteDeck implementation.

## Known Migration-Sensitive Behaviors

These behaviors must be handled explicitly in any RouteDeck migration:

- the implementation subclasses a compatibility runtime and composes it through
  `RouteDeckApp`; package structure is not the behavior contract;
- the large `backend/corpus/graph/app.py` mixes planning, projection, runtime
  adaptation, and product handlers even though their responsibilities are
  behaviorally distinct;
- current visible entity bindings can contain real database IDs;
- Corpus uses a custom model-planning and reply-stream protocol on top of
  RouteDeck runtime events;
- browser path reconciliation, surface dirty-state handling, peer/detail
  surfaces, and staged review are user-visible and must survive structural
  refactoring;
- deployed agents share domain state with Corpus but currently have their own
  orchestration and SSE contracts.

Do not infer that preserving these behaviors requires preserving their current
classes, module boundaries, identifiers, or compatibility framework API.
