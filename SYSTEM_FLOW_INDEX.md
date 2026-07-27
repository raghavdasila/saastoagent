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

## Implemented Guest Lounge

```text
browser loads RouteDeck frontend contract
  -> host resumes or creates encrypted-cookie guest session
  -> RouteDeck enters workspace.lounge and projects Lounge surface
  -> Corpus renders the Lounge shell with conversation pending
  -> assistant-initiated LangGraph turn calls configured Ollama model in background
  -> each validated assistant delta updates the visible greeting immediately
  -> conversation is persisted through RouteDeck SQLAlchemy runtime
  -> completed durable greeting replaces transient progress with canonical history
  -> owner message streams through /api/routedeck/chat
  -> sign-in/register affordance dispatches a typed Workspace operation
  -> RouteDeck commits the legal node transition and new surface projection
```

Ollama or persistence unavailability fails readiness and the user-visible chat
path. There is no canned response or alternate-model execution branch.

## Implemented Bootstrap Recovery

```text
RouteDeck store is idle
  -> RouteDeckBootstrapBoundary starts bootstrap
  -> loading state renders the generic Corpus loading shell
  -> ready state mounts Corpus conversation and surfaces
  -> recovery state exposes only RouteDeck-legal actions
  -> Corpus renders product wording and invokes the selected action
  -> start-new choice first revokes Corpus browser auth and owner handle
  -> RouteDeck creates a genuinely new anonymous guest session
  -> ready state remounts the Lounge and restores its conversation
```

Corpus does not inspect `pendingBootstrap`, retained request IDs, uncertain
navigation state, or retry legality. RouteDeck owns those mechanics and the
transition back to ready; Corpus owns the visible wording and auth cleanup
policy around explicit replacement.

## Implemented Corpus Owner Authentication

```text
guest Lounge -> sign-in or registration surface
  -> same-origin Corpus auth mutation
  -> owner + personal organization + membership + revocable auth session
  -> permanent claim over the current guest RouteDeck session
  -> HttpOnly auth cookie + opaque owner-route handle; guest cookie cleared
  -> workspace.authentication_completed
  -> claim-backed owner context provider
  -> session-bound workspace.home
```

Reload and additional browser sessions resolve the owner's durable claim.
Anonymous replay of the adopted guest cookie fails. Logout or recovery revokes
the browser auth session and handle, clears cookies, and creates a new guest
Lounge without releasing the owned RouteDeck session.

Verification and reset tokens travel in URL fragments. Corpus captures the
fragment before RouteDeck contract/session bootstrap can rewrite browser
history, retains the token only in frontend memory, and immediately removes the
fragment from the visible URL. These token surfaces do not start a Lounge
greeting. Verification is advisory. Reset changes the password and revokes
every browser session and owner-route handle.

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

The live product now has eight nodes: seven `workspace.*` nodes and one
`sources.home` node. The Sources surface is an authenticated experimental debug
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
