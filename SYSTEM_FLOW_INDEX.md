# Corpus System Flow Index

These are product/runtime relationships, not Navgraphs. The proposed RouteDeck
Navgraph is maintained separately in the design notebook.

## Validated Horizontal Product Lifecycle

```text
owner stages one API definition without processing
  -> explicitly starts durable Source analysis
  -> Source Hub renders the persisted ToolRouter semantic graph
  -> owner reviews and approves one effective API Source revision
  -> saves one protected profile and exact operation curation
  -> creates an Agent pinned to the exact Source revision
  -> Designer uses the configured real model to append one owner-described,
     Source-grounded immutable feature revision
  -> owner customizes, reviews, accepts, and requests one build
  -> Builder persists one durable queued assembly attempt
  -> source worker rechecks and materializes one immutable model/source/profile/curation binding
     then automatically schedules durable ToolRouter coverage for that exact build
  -> Sandbox runs the exact build through the neutral execution adapter
  -> Evaluation runs the generated exact-build case and derives eligibility
  -> Channels creates hosted Web; Deployment requires explicit review
  -> backend/worker restart restores exact build and delivery bindings
  -> public hosted session searches the real Medusa catalog
  -> cart creation waits for explicit review and executes once
  -> add-to-cart uses bounded response-derived session references,
     waits for a second explicit review, and executes once
  -> Operations shows owner-scoped redacted interaction evidence and promotion
```

The current complete local path is independently retained through direct
surfaces (`20260812T183856Z-02c48c5a50`, 39/39), ordinary owner-language chat
(`20260812T222652Z-403a886798`, 39/39), and one continuing hybrid conversation
(`20260812T221223Z-0e9ec6eb55`, 40/40). All three recordings are raw, uncut,
normal-speed, and include the semantic graph, Designer topology, compiled
build/evaluation/deployment NavGraphs, real Sandbox and public product search,
reviewed cart creation and add-to-cart, restart, Operations evidence/promotion,
and 390x844 rendering. Each has zero unexpected HTTP, console, page, or request
failures. Exact paths, hashes, IDs, and diagnostic allowlists are recorded in
`docs/superpowers/validation/2026-08-13-horizontal-ecommerce-chat-surface-hybrid.md`.

The accepted Designer revision now compiles one shared product-owned topology.
Designer visibly renders its stable topology hash, executable node, exact
capabilities, curated operations, policies, and runtime surfaces. Builder uses
that same topology to compile the immutable per-build RouteDeck Application;
the built NavGraph displays the same identity. The current runtime graph is one
real Agent node, not a decorative lifecycle diagram.

Durable Builder assembly is independently retained in bounded run
`20260811T163659Z-73c50607a2` (15/15). Its 13.84-second normal-speed maximized
film shows the feature transition through queued/running/ready, the exact
immutable compiled NavGraph, and automatic evaluation-coverage scheduling.
The run stopped before Sandbox and Evaluation by design.

Earlier accepted and failed runs retain their historical claim boundaries.
RouteDeck owns legality, review, transitions, and projection. Corpus owns every
domain identity, adapter, persistence record, public route, and product surface.
Credentials resolve only at the execution boundary; reviewed public writes do
not expose request/response bodies or owner-only runtime evidence.

## Docker Development Startup

```text
docker compose up --build
  -> filtered local Corpus + RouteDeck build context
  -> backend entrypoint reuses persistent development secrets
  -> owner-auth migration -> Uvicorn on backend:8099
  -> Vite on 127.0.0.1:5199 proxies same-origin API to backend
  -> notebook on 127.0.0.1:8771 serves repository design artifacts
  -> embedded ToolRouter uses pinned CPU MiniLM inside backend
  -> generator/reviewer calls use explicit host.docker.internal Ollama URL
  -> RouteDeck/auth/Source artifacts persist under bind-mounted .runtime
```

Compose owns only local process lifecycle, health, networking, and mounts.
Sources, ToolRouter, RouteDeck, and owner identity retain their documented
product and framework ownership. Missing Ollama/models or failed migrations
remain visible failures.

## Shared Durable Work And Credentials

```text
feature-owned service
  -> DurableJobPort commits queued Corpus job + lifecycle event
  -> Huey SQLite queue receives only the opaque job UUID
  -> feature-owned task records running then succeeded or failed
  -> owner-scoped status and explicit retry read central Corpus truth

private credential surface
  -> SecretBox vault creates an opaque owner-scoped reference
  -> authenticated ciphertext persists in central Corpus database
  -> execution adapter resolves plaintext only at the call boundary
  -> wrong owner, wrong key, tamper, or invalid binding fails closed
```

Huey does not replace Corpus lifecycle persistence, and queue rejection never
falls back to inline execution. The vault key is environment-supplied and is
not stored in Corpus data. No product feature consumes these seams until its
own mapped slice wires an explicit task and credential purpose.

## Corpus Interaction

```text
owner message or surface action
  -> active RouteDeck node
  -> node-scoped prompt, context, tools, legal operations and surfaces
  -> Corpus agent chooses or proposes a typed operation
  -> RouteDeck validates and commits legal interaction state
  -> Corpus renders chat plus projected surfaces
```

## Responsive Corpus Shell

```text
RouteDeck projects active/review surfaces and conversation state
  -> conversation history scrolls independently
  -> active/review surface stays in a bounded dock above the composer
  -> composer remains at the bottom of the available application viewport
  -> desktop renders the Workspace rail and docked Navgraph
  -> mobile hides the rail and exposes Workspace + Navgraph through header drawers
```

The responsive shell changes only presentation. RouteDeck continues to own the
current node, legal operations, surface projection, history, and Navgraph
state; Corpus does not duplicate those contracts in either drawer. When the
current node changes, the bounded surface dock resets to its top so a newly
projected feature surface never inherits the previous feature's scroll state.

Phase 6 retains this shell boundary while closing lifecycle breadth. Reviewed
Agent archive/delete clears the removed selection before detail refresh so the
shell never polls a deleted Agent. A failed acceptance restores the exact
selected Agent and refreshed dependency truth. Source description remains a
separate immutable Markdown record and Source deletion never analyzes, detaches,
or cascades through Agent/design/build lineage.

## Implemented Bearer-Selected Lounge

```text
browser issues or refreshes an anonymous bearer identity
  -> GET /api/conversations validates the caller's public conversation catalog
  -> frontend selects one public conversation ID per tab or creates one
  -> Corpus authorizes bearer + X-Corpus-Conversation-ID
  -> Corpus reserves the opaque public-to-internal conversation mapping
  -> RouteDeckRuntime.provision_session centrally creates/replays the session
  -> Corpus resolves the persisted conversation principal for that exact internal session
     -> anonymous enters lounge.home and durably claims its declared welcome run
     -> authenticated owner enters workspace.home with its node-scoped public surfaces
  -> projection interaction.request_id identifies the active run generically
  -> SSE subscribers may disconnect and reconnect from a monotonic run cursor
  -> completed history remains canonical RouteDeck state
  -> owner messages use the same detached server-owned run lifecycle
  -> sign-in/register affordance dispatches a typed Lounge operation
  -> RouteDeck commits the legal node transition and new surface projection
```

New conversation is a Corpus shell lifecycle:

```text
header action (disabled during an active RouteDeck interaction)
  -> anonymous: verify current public mapping, provision fresh RouteDeck session
     -> atomically archive old mapping and bind replacement
  -> owner: create an additional public conversation at workspace.home and retain earlier ones
  -> fetch the new conversation's exact authoritative projection
  -> validate and encode its canonical URL with a RouteDeck codec bound to that projection
  -> select the new opaque public ID in tab storage
  -> mount and bootstrap fresh RouteDeck/chat/private-form clients on that canonical URL
  -> dispose the previous client runtime
```

RouteDeck owns each internal session after provisioning. Corpus owns the user
action, public conversation authorization/mapping, and client switch. The Agent
Design Studio is not involved because no agent behavior or topology changes.

Browser and recovery ownership remain Corpus-internal:

```text
selected opaque Corpus conversation
  -> compare per-tab history owner before RouteDeck bootstrap
  -> stale other-conversation history: load authoritative projection and replace URL/state
  -> matching history: preserve Back/Forward
  -> new tab without RouteDeck history: preserve valid deep link
  -> RouteDeck recovery contract reports legal actions internally
  -> Corpus automatically abandons ambiguous navigation, resynchronizes, or replaces conversation
  -> user sees Corpus or Corpus-owned availability copy, never RouteDeck recovery state
```

Ollama or persistence unavailability fails readiness and the user-visible chat
path. There is no canned response or alternate-model execution branch.

## Implemented Client Bootstrap And Recovery

```text
refresh credential is read inside the cross-tab lock
  -> valid refresh rotates atomically and keeps the access token in memory
  -> only a 401 invalid/expired refresh clears local credentials
  -> client issues a fresh anonymous bearer when no valid refresh exists
  -> selected tab conversation is validated against the authorized catalog
  -> a missing, expired, or stale-contract backing session releases only its unusable Corpus mapping
  -> missing catalog creates a new public conversation
  -> RouteDeckBootstrapBoundary resumes that already selected session
  -> active interaction.request_id reconnects the generic run subscriber
  -> ready state mounts Corpus without exposing an internal RouteDeck ID
```

Corpus does not infer entry request IDs, reset authentication on conversation
failure, or impose a client convergence timeout. RouteDeck owns durable turn
authority, restart interruption, cursor replay, and terminal history. Corpus
owns bearer identity, public conversation authorization, and client storage.
Corpus does not expose the backing framework error when a saved contract is no
longer usable; it removes that conversation from the authorized catalog and
allows the client to create a fresh current-contract conversation.

## Implemented Corpus Owner Authentication

```text
anonymous Lounge -> sign-in or registration surface
  -> supervised RouteDeck operation reads encrypted private form
  -> owner + personal organization + membership + revocable token session
  -> atomic adoption of the selected public Corpus conversation
  -> anonymous credentials revoked; owner token pair returned out of RouteDeck state
  -> lounge.authentication_completed
  -> claim-backed owner context provider
  -> session-bound workspace.home
```

Reload and additional clients resolve authorized conversations from the owner
catalog. Anonymous replay after adoption fails. Logout revokes the token
session; the next bootstrap issues a new anonymous identity and conversation
without releasing the owner's durable conversation.

Verification and reset tokens travel in URL fragments. Corpus captures the
fragment before RouteDeck contract/session bootstrap can rewrite browser
history, retains the token only in frontend memory, and immediately removes the
fragment from the visible URL. These token surfaces do not start a Lounge
greeting. Verification is advisory. Reset changes the password and revokes
every owner token session.

Signed-in verification delivery is a Lounge-owned account behavior reached
from `workspace.home` through `workspace.open_verification`. The
`lounge.verification_pending` surface requests delivery only after the owner
explicitly selects Resend verification, reports the real result, and returns
through `lounge.return_to_workspace`.

## Implemented Workspace And Core Agents Slice

```text
authenticated workspace.home
  -> Workspace overview resolves owner scope through an application adapter
  -> real Agent count is read from AgentService
  -> unavailable Source/activity summaries remain explicitly unavailable
  -> workspace.open_agents commits agents.home
  -> authenticated Agent HTTP reads load the owner-scoped inventory
  -> agents.open_create commits agents.create
  -> agents.create_agent validates and persists Agent identity + immutable v1
  -> agents.save_changes checks expected_version and appends immutable v2+
  -> agents.select_agent binds the exact owner-scoped Agent privately
  -> agents.attach_source validates and pins a READY current Source revision
  -> agents.open_source_creation retains the Agent across the real Source Hub path
  -> agents.attach_created_source pins the returned revision and returns
  -> attachment reads resolve display data from the owner-scoped Source gateway
  -> agents.open_attached_source revalidates the persisted exact revision
  -> Workspace reload reports the persisted Agent count
```

Agent mutations exist only as supervised RouteDeck Operations. Agent HTTP is
read-only. The frontend Agent store owns domain query/loading/error state but
never copies current node, legal operations, projection versions, review, or
recovery state from RouteDeck. Cross-feature navigation references are
injected through declared contracts at application composition. Agents owns
only the immutable association identities and attachment timestamp; Source
display data, inventory, processing jobs and ToolRouter revision artifacts
remain in their existing owners. Attachment DTOs resolve the current display
name through the exact owner-scoped Source revision or fail truthfully if it is
unavailable. Reattaching a Source after its current revision changes is a
conflict, never an overwrite.

## Implemented Source Hub API Intake And Durable Processing Path

```text
owner Home -> workspace.open_sources
  -> RouteDeck commits sources.home and projects sources.home
  -> Source Hub lists the authenticated Workspace inventory
  -> sources.open_api_creation exposes API YAML plus optional Markdown intake
  -> API connector-owned authenticated same-origin upload route validates bytes
  -> SourceService persists one owner-scoped revision and durable job link
  -> repository publishes revision metadata before the discoverable Source pointer
  -> Source-scoped cross-process lock keeps inventory reads coherent with lifecycle mutations
  -> Huey queues only the opaque durable job ID; no in-process fallback exists
  -> source-worker marks queued -> running and invokes the registered connector
  -> explicit API/ToolRouter bridge invokes ToolRouterAdapter for that revision
  -> normalized OpenAPI bundle + resource_first_v1 graph + MiniLM index persist
  -> revision and durable job become ready/succeeded or failed with evidence
  -> Source Hub polling reloads the persisted terminal state
  -> ready revision presents persisted semantic groups and individually selectable recorded stages
  -> projected sources-api-connection private form accepts credential material
  -> sources.save_api_connection carries no public secret arguments
  -> encrypted vault record + revision-bound non-secret profile metadata persist
  -> owner explicitly selects the exact effective revision, saved profile, and GetProductTypes or GetProductTags
  -> sources.test_api_connection rechecks owner/source/revision/profile/credential version
  -> credential resolves just in time inside the API execution adapter
  -> exact reviewed effective API definition validates one request and response; no retry or fallback exists
  -> immutable redacted success or failure identity persists without headers, bodies, query values, or secrets
  -> sources.propose_contract_revision reproduces the accepted repaired-parent + twelve-patch chain without transport
  -> owner-scoped proposal persists exact hashes, patch records, local target and evidence
  -> proposal projects through the RouteDeck detail slot while Source Hub stays active
  -> sources.approve_contract_revision stages durable required review from an opaque proposal entity
  -> accept-time guard/service recheck the exact owner, current parent and complete persisted plan
  -> acceptance creates a READY immutable child revision; rejection leaves the parent current
  -> READY revision's existing ToolRouter artifact yields one exact API-operation inventory
  -> owner explicitly classifies every discovered operation include or exclude
  -> sources.save_api_operation_curation appends an immutable record under exact expected-current CAS
  -> stale/concurrent input remains failed; Source Hub refetches the authoritative selection
  -> curation history/current pointer survive reload and backend restart without executing an API
  -> sources.prepare_routed_api_test opens a stable non-executing detail surface from agent or surface
  -> server binds planning to the exact authenticated owner, conversation and RouteDeck session
  -> current curation becomes ToolRouter's retrieval corpus before unchanged routing
  -> ambiguity exposes candidates without preselection; an exact typed choice reroutes one endpoint
  -> missing non-secret input appends same-lineage records under exact current-record CAS
  -> profile-managed authentication contributes only non-secret parameter identity
  -> ready, waiting and unresolved multi-step plans persist with api_call_count fixed at zero
  -> reload/backend restart retain the exact plan; other conversations and owners remain isolated
  -> explicit sources.retry_processing requeues only the failed linked job
```

Source identity, revisions, tenancy, RouteDeck behavior, and list/get/retrieve/
evalset HTTP contracts are generic. API upload HTTP/configuration is owned by
`features/sources/connectors/api/`; its `toolrouter.py` bridge alone translates
between the API engine port and the replaceable
`corpus.integrations.toolrouter` facade.
The private ToolRouter engine owns OpenAPI/graph/retrieval/evalset algorithms;
it owns no product node or owner/session behavior.

The live product has twelve nodes: eight `lounge.*` nodes, one
`workspace.home` node, two `agents.*` nodes, and one `sources.home` node. The
Source Hub surface includes inventory, API YAML/optional Markdown intake,
durable status, detail, semantic graph groups, exact recorded-stage inspection,
  protected revision-bound connection-profile saving, explicit one-call safe
  GetProductTypes/GetProductTags checks, immutable redacted check history,
  transport-free immutable contract proposal/required-review behavior, exact
  non-executing operation curation with immutable CAS history,
  conversation-bound non-executing route preparation and clarification, and
  explicit retry. Phase C retained 8/8 passing browser assertions including
  real Medusa success/failure, reload/restart, owner isolation, desktop/mobile
  evidence and a safe trace; its immutable recorder status remains failed only
  for a sign-out abort diagnostic after the backend logged 204. Phase D run
  `20260807T212855Z-f8596ef591` passed 9/9 with fresh processing, exact
  inventory, explicit decisions, visible stale-CAS recovery, reload/restart,
  owner isolation, desktop/mobile evidence, continuous video and safe trace.
  Phase E run `20260808T000249Z-c67d5b0004` passed 13/13 with real curated
  ToolRouter ambiguity, typed same-lineage clarification, current-request and
  managed-profile provenance, zero calls, reload/restart, three-conversation
  isolation, second-owner isolation, desktop/mobile evidence, continuous
  video and safe trace. Ordered pause/resume/step graph replay, compiled
  read/write execution, deployed-agent clarification, unknown-write recovery,
  Source deletion, and later lifecycle features remain outside these slices.

## Feature Evaluation Evidence

Behavior and conversation evaluation exercise the compiled runtime directly:

```text
Studio-owned behavior, action plan, or adaptive conversation definition
  -> isolated Corpus HTTP conversation
  -> declared real setup through product Operations
  -> RouteDeck operation dispatch and node transitions
  -> durable operation/session/domain/projection evidence and transcript
  -> deterministic bound outcome and checkpoint assertions
  -> semantic judge only for conversational plans
  -> immutable .runtime/evaluations result artifact
  -> atomic latest-evidence index entry keyed by evaluation ID
  -> Studio compares that entry with the current definition hash
```

Each definition therefore reports its own current, stale, failed, or not-run
state. Running one evaluator definition never displaces the latest evidence for
an unrelated definition.

Product-journey evaluation exercises the rendered product separately:

```text
Studio-owned product journey
  -> disposable Corpus backend/frontend and SQLite state
  -> official Playwright Chromium interaction
  -> real private surfaces, RouteDeck dispatch and Corpus auth transitions
  -> Mail.tm mailbox plus real Gmail SMTP when mail is required
  -> screenshot, trace, transcript and backend-state assertions
  -> pass or retained product failure artifact
```

The public Lounge boundary recorder additionally exercises the combined
conversation-to-Surface lifecycle on one page: public privacy response -> Sign
in -> immediate Back to Lounge. RouteDeck keeps the projected Surface inert
while its store is not `live`, then accepts the operation after authoritative
resynchronization. The artifact retains browser errors and aborted transport
requests separately so navigation/teardown cancellation cannot masquerade as a
successful application response.

The Design Studio walkthrough separately proves governance and authoring UX at
desktop and representative mobile dimensions. Its current Step 2 validation is
recorded in `docs/superpowers/validation/2026-08-07-step2-studio-governance.md`.

The product runner owns isolated ports and databases and removes its runtime
after execution. It does not mutate normal development databases, invent mail
delivery, or turn a failed user-visible outcome into success.

## Agent Creation And Release

```text
source manifests + owner intent
  -> Agent Designer
  -> immutable design revision plus visible shared topology/hash
  -> accepted design and build request
  -> Agent Builder compiles the same topology into an immutable RouteDeck Application
  -> exact runtime build and NavGraph
  -> Sandbox
  -> Evaluation queues one exact case/build/revision attempt
  -> source worker persists queued/running/terminal state with no automatic retry
  -> explicit retry appends lineage only from the exact failed current attempt
  -> Channels and deployment configuration
  -> Deployment
  -> Operations
```

## Governed Improvement

```text
sandbox evidence + evaluation evidence + production evidence
  -> Learning candidate
  -> owner review
  -> accepted change request
  -> new design and agent-configuration revision
```

## Deployed Agent Interaction

```text
channel event
  -> deployed agent revision and channel binding
  -> RouteDeck node scope
  -> model and legal source/tool execution
  -> RouteDeck state transition and surface projection
  -> channel-compatible response
```
