# Corpus System Flow Index

These are product/runtime relationships, not Navgraphs. The proposed RouteDeck
Navgraph is maintained separately in the design notebook.

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
state; Corpus does not duplicate those contracts in either drawer.

## Implemented Bearer-Selected Lounge

```text
browser issues or refreshes an anonymous bearer identity
  -> GET /api/conversations validates the caller's public conversation catalog
  -> frontend selects one public conversation ID per tab or creates one
  -> Corpus authorizes bearer + X-Corpus-Conversation-ID
  -> Corpus reserves the opaque public-to-internal conversation mapping
  -> RouteDeckRuntime.provision_session centrally creates/replays the session
  -> RouteDeck enters lounge.home and durably claims its declared welcome run
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
  -> owner: create an additional public conversation and retain earlier ones
  -> select the new opaque public ID in tab storage
  -> mount fresh RouteDeck/chat/private-form clients
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
  -> missing catalog creates a new public conversation
  -> RouteDeckBootstrapBoundary resumes that already selected session
  -> active interaction.request_id reconnects the generic run subscriber
  -> ready state mounts Corpus without exposing an internal RouteDeck ID
```

Corpus does not infer entry request IDs, reset authentication on conversation
failure, or impose a client convergence timeout. RouteDeck owns durable turn
authority, restart interruption, cursor replay, and terminal history. Corpus
owns bearer identity, public conversation authorization, and client storage.

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

## Implemented Sources And API Connector Debug Path

```text
owner Home -> workspace.open_sources
  -> RouteDeck commits sources.home and projects sources.debug
  -> evidence rail exposes API collection -> graph/index -> retrieval -> reviewed evalset
  -> API connector-owned authenticated same-origin upload route
  -> SourceService creates one owner-scoped immutable revision in processing
  -> API connector validates JSON/YAML and calls its ApiSourceEngine port
  -> explicit API/ToolRouter bridge invokes ToolRouterAdapter
  -> normalized OpenAPI bundle + resource_first_v1 graph + MiniLM index persist
  -> revision becomes ready or records an explicit failed state
  -> retrieval reloads graph/embeddings and returns a neutral Source decision
  -> optional evalset run invokes local Gemma generation
  -> deterministic validation -> independent local Qwen review
  -> accepted reviewed-candidate export or explicit quarantine/failure
```

Source identity, revisions, tenancy, RouteDeck behavior, and list/get/retrieve/
evalset HTTP contracts are generic. API upload HTTP/configuration is owned by
`features/sources/connectors/api/`; its `toolrouter.py` bridge alone translates
between the API engine port and the replaceable
`corpus.integrations.toolrouter` facade.
The private ToolRouter engine owns OpenAPI/graph/retrieval/evalset algorithms;
it owns no product node or owner/session behavior.

The live product now has ten nodes: eight `lounge.*` nodes, one
`workspace.home` node, and one `sources.home` node. The Sources surface is an authenticated experimental debug
surface, not Agent Designer, an execution Sandbox, or a public deployed Web
channel. The four evidence stages are UI state derived from the Source,
retrieval, and evalset results; they are not additional product or RouteDeck
nodes.

## Agent Creation And Release

```text
source manifests + owner intent
  -> Agent Designer
  -> accepted design
  -> Agent Builder
  -> draft agent revision
  -> Sandbox
  -> Evaluation and evalsets
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
