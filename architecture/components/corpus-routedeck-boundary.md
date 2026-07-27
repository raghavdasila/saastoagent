# Corpus And RouteDeck Boundary

## Purpose

Corpus owns product meaning, its primary chat agent, feature operations,
prompts, bindings, surfaces, and owner-visible language.

RouteDeck owns generic legal interaction topology and state mechanics: active
node, transitions, operation legality, session/runtime lifecycle, projections,
conversation transport, identifiers, recovery, and diagnostics.

Owner authentication is Corpus-host-owned. RouteDeck receives only an already
authorized internal session ID from the Corpus selector. Workspace owns product
surfaces and typed continuation, while identity truth, cookies, persistence,
revocation, and ownership claims stay in `corpus.auth`.

## Owner Files

- `backend/src/corpus/app/**` - RouteDeck host plus concrete application
  composition roots
- `backend/src/corpus/runtime/**` - persistence and Ollama-backed agent drivers
- `backend/src/corpus/features/workspace/**` - Workspace declarations/bindings
- `backend/src/corpus/features/sources/**` - generic Sources lifecycle and
  transport plus connector-owned configuration, HTTP, ports, and bridges
- `backend/src/corpus/integrations/toolrouter/**` - private copied engine and
  replaceable adapter used only by the API Source connector
- `backend/src/corpus/composition.py` - selects Workspace, Sources, and the
  Workspace Lounge entry
- `frontend/src/app/**` - generic permanent chat shell and Navgraph slot
- `frontend/src/routedeck/**` - client and surface-registry bridge
- `frontend/src/components/ui/**`, `frontend/src/lib/**` - generic shadcn/ui
  primitives and helpers
- `frontend/src/features/workspace/**` - Workspace-owned UI
- `frontend/src/features/sources/**` - Sources-owned debug UI and HTTP client
- `backend/src/corpus/auth/**`, `backend/migrations/**` - Corpus owner identity,
  sessions, claims, rate limits, migrations, and mail port

## Public Interfaces

- The ASGI factory is `corpus.main:create_live_app`.
- RouteDeck HTTP is mounted at `/api/routedeck`.
- `workspace.lounge` is the compiled entry node and renders
  `workspace.lounge` in the active surface slot.
- Seven Workspace nodes cover Lounge, sign-in, registration, forgot/reset,
  verification, and the session-bound owner home.
- One session-bound `sources.home` node renders `sources.debug`. Together with
  Workspace, the current live application contains eight nodes.
- `workspace.authentication_completed` requires the claim-backed owner context
  provider before RouteDeck can commit entry into `workspace.home`.
- Corpus owner APIs are mounted at `/api/auth`; responses never expose auth
  tokens, RouteDeck IDs, password state, or internal membership keys.
- Owner-only Source APIs are mounted at `/api/sources`. Source identity and
  retrieval/evalset contracts are generic; API upload transport is
  connector-owned, only the explicit API/ToolRouter bridge imports the public
  adapter, and HTTP never exposes engine paths.
- The frontend consumes the RouteDeck frontend contract and dispatches only
  declared surface affordances.
- `RouteDeckBootstrapBoundary` and its normalized recovery state own bootstrap
  startup, retained-request legality, recovery phase selection, and transition
  back to the live application. Corpus renders product copy and invokes only
  the actions RouteDeck exposes. Before `start_new_session`, Corpus revokes the
  current browser auth session and owner-route handle so replacement state is
  a genuinely anonymous guest Lounge.
- Corpus captures verification/reset URL fragments before RouteDeck bootstrap;
  RouteDeck remains responsible for route/history synchronization afterward.
- Lounge greeting execution remains a real RouteDeck conversation turn, but
  the Corpus shell renders its pending state first and then renders RouteDeck's
  typed accumulated progress after every validated assistant delta. Corpus
  does not inspect raw stream events or reproduce durable coordination.
  Credential/token nodes do not initiate that Lounge-only greeting.
- The generic shell renders RouteDeck's Navgraph in an expandable docked rail
  on desktop and a shadcn Sheet on mobile; neither presentation owns or copies
  navigation state.
- The model adapter uses the native `langchain-ollama` integration; readiness
  verifies the exact configured model through the official Ollama Python SDK.

## Core Runtime Rule

```text
Corpus feature definitions own product meaning
  -> application composition selects features and entry node
    -> RouteDeck owns legal interaction and durable session state
      -> the active node scopes the Corpus agent
        -> the frontend renders permanent chat plus projected surfaces
```

## Docker Development Topology

`compose.yaml` is a process-orchestration boundary, not a product or framework
boundary. It runs three independently healthy development services:

```text
127.0.0.1:5199 -> Vite frontend -> http://backend:8099
127.0.0.1:8099 -> Corpus backend -> embedded RouteDeck + ToolRouter
127.0.0.1:8771 -> design notebook
Corpus backend -> http://host.docker.internal:11434 -> host Ollama
```

The backend and frontend images consume the sibling RouteDeck source through a
filtered local build context and preserve its existing package boundaries. The
backend persists RouteDeck, owner-auth, and Source state under bind-mounted
`/data`; Compose does not reinterpret RouteDeck state or expose raw session
identifiers. ToolRouter remains an internal Corpus integration, not another
service.

## Dependencies And Known Risks

- RouteDeck 0.1.0 is linked with pnpm `link:` dependencies to the sibling
  checkout. Corpus resolves `@routedeck/core` and `@routedeck/react` through
  package junctions and consumes their built `dist` exports; it does not fetch
  RouteDeck from Git or the npm registry. Corpus uses the documented
  consumer-owned `RouteDeckSessionSelector`; no RouteDeck auth middleware was
  added or guessed.
- Gmail delivery uses the narrow Corpus-owned standard-library SMTP adapter
  after a successful real STARTTLS reference. Verification fails visibly with
  503 when delivery is unavailable; reset remains generic 202 and logs the
  failure. No alternate provider or synthetic success exists.
- The broader proposed 53-node product Navgraph is not implemented. The live
  contract intentionally contains seven Workspace nodes plus Sources.
- The ignored Corpus benchmark remains evidence only and is never an import,
  build, runtime, or test dependency. Separately, the ToolRouter sibling was
  used as the verified source of a namespaced, hash-manifested engine snapshot;
  the sibling path itself is not a runtime dependency.
- Frontend primitives are generated from the pinned shadcn 4.13.1
  Radix-Nova registry and remain generic; Workspace styling stays inside the
  feature package.
- Ollama execution uses `langchain-ollama==1.1.0`; readiness uses the official
  `ollama==0.6.2` SDK. Neither adapter switches provider on failure.

## Tests And Evidence

- `.\.venv\Scripts\python.exe -m pytest backend\tests -q` protects host,
  configuration, feature compilation, bindings, runtime, readiness, and HTTP
  guest-session behavior.
- `pnpm --dir frontend test`, `typecheck`, and `build` protect the generic shell,
  owner session context, credential UX, pre-bootstrap fragment capture/removal,
  non-blocking incremental greeting bootstrap, composer lockout, surface
  registration, continuation behavior, and the Sources debug interaction
  contract.
- `backend/tests/integrations/toolrouter/**` and `backend/tests/sources/**`
  protect exact snapshot provenance, adapter ingestion/reload/retrieval/evalset
  behavior, connector neutrality, source lifecycle, tenancy, HTTP, and the
  RouteDeck Sources node.
- From the sibling RouteDeck checkout, `pnpm --filter @routedeck/react test`,
  `typecheck`, and `build` protect the normalized bootstrap boundary, legal
  recovery actions, and the built package artifacts consumed by Corpus.
- `.\.venv\Scripts\python.exe scripts\smoke_live.py` exercises a running guest
  session, assistant-initiated turn, real Ollama user turn, SSE completion, and
  durable conversation history.
- Desktop and mobile browser checks cover the rendered shell, real chat,
  registration navigation/failure, return transition, and live Navgraph.

## Invariants

- Corpus remains the primary chat interface across feature nodes.
- RouteDeck does not contain Corpus product literals or source-specific policy.
- Corpus does not reimplement a competing interaction-state store.
- Product surfaces dispatch typed operations; they do not mutate graph state.
- Failures remain failures; unavailable dependencies do not silently fall back.
- Deployed-agent users remain a separate future identity realm.
- Raw browser credentials are never stored in the Corpus auth database.
- The ignored Corpus benchmark and live ToolRouter sibling checkout are not
  implementation dependencies; the checked-in ToolRouter snapshot is private
  integration source governed by its manifest and license boundary.

## Update Triggers

Update this document and `architecture/code-map.md` when changing ownership,
RouteDeck compatibility, model/runtime adapters, Workspace/Sources
nodes/operations, Source connector boundaries, ToolRouter adapter/snapshot,
authentication middleware, public transport, or validation meaning.
