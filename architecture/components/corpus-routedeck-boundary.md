# Corpus And RouteDeck Boundary

## Purpose

Corpus owns product meaning, its primary chat agent, feature operations,
prompts, bindings, surfaces, and owner-visible language.

RouteDeck owns generic legal interaction topology and state mechanics: active
node, transitions, operation legality, session/runtime lifecycle, projections,
conversation transport, identifiers, recovery, and diagnostics.

RouteDeck may report technical state and legal recovery actions to Corpus.
Corpus resolves state, navigation, link, and recovery mechanics internally.
Users never receive RouteDeck errors, identifiers, state codes, or recovery
choices. If automatic recovery cannot restore the product, Corpus shows only
Corpus-owned availability language.

Owner authentication is Corpus-host-owned. RouteDeck receives only an already
authorized internal session ID from the Corpus selector. Lounge owns public
account surfaces and typed continuation into Workspace, while bearer identity,
public conversations, persistence, revocation, and ownership claims stay in
`corpus.auth`.

## Owner Files

- `backend/src/corpus/app/**` - RouteDeck host plus concrete application
  composition roots
- `backend/src/corpus/runtime/**` - persistence and explicitly selected Ollama- or OpenAI-backed agent drivers
- `backend/src/corpus/features/lounge/**` - public Lounge, account journeys,
  bindings, and scoped AgentPolicies
- `backend/src/corpus/features/workspace/**` - Workspace declarations/bindings
- `backend/src/corpus/features/agents/**`, `designer/**`, `builder/**`,
  `sandbox/**`, `evaluation/**`, `channels/**`, `deployment/**`, and
  `operations/**` - owner product domains and their compiled RouteDeck feature
  declarations
- `backend/src/corpus/features/sources/**` - generic Sources lifecycle and
  transport plus connector-owned configuration, HTTP, ports, and bridges
- `backend/src/corpus/integrations/toolrouter/**` - private copied engine and
  replaceable adapter used only by the API Source connector
- `backend/src/corpus/composition.py` - selects all nine host features and the
  Lounge entry
- `frontend/src/app/**` - generic permanent chat shell and Navgraph slot
- `frontend/src/routedeck/**` - client and surface-registry bridge
- `frontend/src/components/ui/**`, `frontend/src/lib/**` - generic shadcn/ui
  primitives and helpers
- `frontend/src/features/lounge/**` - Lounge and account-owned UI
- `frontend/src/features/workspace/**` - Workspace-owned UI
- `frontend/src/features/sources/**` - Sources-owned debug UI and HTTP client
- `backend/src/corpus/auth/**`, `backend/migrations/**` - Corpus owner identity,
  sessions, claims, rate limits, migrations, and mail port

## Public Interfaces

- The ASGI factory is `corpus.main:create_live_app`.
- RouteDeck HTTP is mounted at `/api/routedeck`.
- `lounge.home` is the compiled entry node and renders `lounge.home` in the
  active surface slot.
- Eight Lounge nodes cover public arrival, product help, sign-in, registration,
  forgot/reset, verification confirmation, and signed-in verification delivery.
- Ten session-bound private product nodes cover Workspace, Agents, Designer,
  Sources, Builder, Sandbox, Evaluation, Channels, and Operations. Together
  with the eight Lounge nodes, the current host application contains 18 nodes.
- Every immutable Agent build owns a separate compiled RouteDeck Application.
  Its real executable topology is one `agent_runtime.home` node with the exact
  Designer topology hash, capability-to-curated-operation membership, policies,
  and clarification, ToolRouter-status, and delivery-status surfaces. It is
  persisted and reconstructed by exact build identity; it is not copied into
  the owner host application's navigation graph.
- Account creation and sign-in are supervised Lounge Operations that read
  encrypted RouteDeck private forms, atomically adopt the selected public
  conversation, and publish owner bearer credential transitions through the
  injected Corpus port. The HTTP adapter emits those transitions only as the
  established response headers outside RouteDeck state before entry commits to
  `workspace.home`; RouteDeck never receives, persists, projects, logs, or
  histories credential values.
- Corpus identity APIs are mounted at `/api/auth`; conversation catalog APIs
  are mounted at `/api/conversations`. Public responses never expose internal
  RouteDeck IDs, credential hashes, password state, or membership keys.
- `POST /api/conversations` reserves the host-owned opaque conversation mapping
  and supplies its internal session ID plus a host-generated request ID to
  `RouteDeckRuntime.provision_session(...)`. RouteDeck owns session factory
  execution, canonical durable creation replay/collision, product
  initialization, declared entry-run attachment, and the returned current
  snapshot. The Corpus-supplied session factory resolves the exact persisted
  conversation principal before creation: anonymous sessions use the compiled
  `lounge.home` entry, while authenticated owner sessions start at the existing
  `workspace.home` node with only its node-scoped public surfaces and an exact
  resume capability. Missing or internally inconsistent principal mappings fail
  closed. Corpus releases the reservation if provisioning fails; it does not
  duplicate that framework control flow.
- `POST /api/conversations/{public_id}/replacement` is a Corpus-owned anonymous
  lifecycle operation. Corpus verifies that the active mapping belongs to the
  bearer, provisions a fresh RouteDeck session first, then atomically archives
  the old public mapping and creates the replacement. Owners use the ordinary
  create endpoint and retain all earlier conversations. Neither path exposes a
  RouteDeck session ID or requires a RouteDeck or Design Studio contract.
- Owner-only Source APIs are mounted at `/api/sources`. Source identity and
  retrieval/evalset contracts are generic; API upload transport is
  connector-owned, only the explicit API/ToolRouter bridge imports the public
  adapter, and HTTP never exposes engine paths.
- Hosted-Agent write operations use the exact compiled per-build RouteDeck
  Application. A public session may expose one Corpus-owned pending-action
  review projection, but no external write is sent until the exact RouteDeck
  review is accepted. Reject, stale review, or missing review fails closed.
  Cart creation and add-to-cart are separate reviews; approval is never shared.
- Corpus retains only public typed outcomes and bounded same-session response
  references across deployed turns. Owner-only NavGraph, ToolRouter trace,
  Source, credential, and execution diagnostics remain outside the public
  projection and are available only through authenticated Operations.
- Hybrid evidence is source-aware. Versioned agent commits correlate only to
  the exact RouteDeck session/projection versions, while direct surface commits
  retain their surface provenance. Unmatched model evidence never borrows a
  surface event cursor or hides another detailed operation.
- The frontend consumes the RouteDeck frontend contract and dispatches only
  declared surface affordances.
- The compiled frontend contract is exported deterministically to
  `frontend/src/routedeck/corpus-frontend-contract.generated.json`. Backend
  tests prove that artifact matches `compile_corpus_app()`, and frontend tests
  plus `RouteDeckSurfaceHost` require the product registry to contain exactly
  the compiled component set, including no stale extra components.
- Lounge credential nodes declare RouteDeck's typed
  `conversation_input` policy. RouteDeck projects and resolves that static
  node contract; Corpus chooses which nodes disable chat and owns the
  owner-visible disabled message.
- Credential and one-time-token surfaces project a public `form_handle` while
  private values remain encrypted RouteDeck state. The frontend saves the
  private form, resynchronizes, and dispatches only the declared Operation.
- The frontend has exactly two HTTP boundaries: a bearer-only authorized
  transport for Corpus identity, conversation-catalog, and Sources requests;
  and a conversation transport that wraps it solely to add
  `X-Corpus-Conversation-ID` for RouteDeck requests. RouteDeck has no default
  unauthenticated client path, and Sources receives its bearer transport by
  injection rather than owning a global fetch singleton.
- Session/token contracts and the two transports are platform-neutral. Browser
  bootstrap supplies the current IndexedDB refresh-credential and Web Locks
  rotation adapters, while native clients must provide platform-secure
  credential storage and equivalent rotation coordination; no native adapter
  is implemented or claimed here.
- After the boundary first reaches ready, RouteDeck keeps Corpus mounted during
  background projection resync/reconnect. Corpus providers and initial
  conversation effects therefore retain their lifecycle instead of restarting
  on every canonical event.
- While RouteDeck is bootstrapping, navigating, reconnecting, or resynchronizing,
  projected product Surfaces remain rendered but busy and inert. Corpus does not
  dispatch stale Surface controls or recreate that synchronization gate.
- The Corpus header disables New conversation while a RouteDeck interaction is
  active. Once creation succeeds, the shell mounts a fresh conversation-scoped
  transport, RouteDeck store, private-form state, and chat history before it
  disposes the previous client runtime. Owner identity and bearer-only product
  clients remain mounted across that switch. Before selecting the replacement,
  Corpus fetches its exact authoritative projection and uses a RouteDeck codec
  bound to that projection to validate and encode the canonical URL. This keeps
  session-bound resume validation strict without letting the previous
  conversation's browser path influence the new session bootstrap.
- Browser history is bound per tab to the selected opaque Corpus conversation.
  Before bootstrap, Corpus discards a RouteDeck history entry owned by another
  conversation and aligns to the selected conversation's authoritative
  projection. Same-conversation history and new-tab deep links remain intact.
- Bootstrap navigation ambiguity resolves to the authoritative current
  projection, resync conditions resynchronize automatically, and missing,
  expired, or incompatible conversations use the Corpus conversation lifecycle.
  The shell never exposes framework recovery controls or raw framework errors.
- Corpus captures verification/reset URL fragments before RouteDeck bootstrap;
  RouteDeck remains responsible for route/history synchronization afterward.
- `lounge.home` declares a generic RouteDeck entry turn. RouteDeck derives the
  request ID, durably claims the turn, projects that active request ID, and owns
  model execution independently of SSE subscribers. Corpus contains no Lounge
  node check, greeting request ID, convergence timer, or conversation-failure
  authentication reset.
- Run subscribers reconnect from monotonic cursors. Backend restart interrupts
  the durable turn through existing RouteDeck recovery; it does not resume
  model generation or discard the Corpus identity/conversation mapping.
- Projected active/review surfaces render in a bounded dock immediately above
  the composer and outside the independently scrolling conversation history.
  The surface remains present near the input without being reordered to the
  top of the chat.
- The generic application navigation remains a left rail on desktop and moves
  into a left-side shadcn Sheet opened by the header hamburger on mobile. The
  mobile main grid retains the full viewport remainder so the surface and
  composer stay docked at the bottom rather than rising above an empty track.
- While any Lounge Node is active, the shell identifies the location as
  `Corpus Lounge`, hides private Workspace/Sources navigation, and presents
  only public Lounge locations plus the current account path. The mobile Sheet
  uses the same Lounge-scoped, user-facing vocabulary.
- The generic shell renders RouteDeck's Navgraph in an expandable docked rail
  on desktop and a separate header-triggered shadcn Sheet on mobile; neither
  presentation owns or copies navigation state.
- The shell mounts RouteDeck's framework-owned `RouteDeckInspector`. RouteDeck
  owns its Graph/Agent-context switch, authenticated private/no-store
  inspection lifecycle, topology diagnostics, current default-deny model
  context, reconstructed messages, effective tools, policy provenance, prompt
  composition, limits, exclusions, and invalid/unavailable states. Corpus owns
  only the docked desktop/mobile shell placement around that component; it does
  not interpret or reconstruct inspection data. The desktop shell owns its
  accessible 320–720 px resize affordance, while Corpus themes the mounted
  inspector through RouteDeck's explicit root-class and stable data-attribute
  styling hooks. Mobile continues to use the fixed Sheet width.
- The model adapter uses the native `langchain-ollama` integration; readiness
  verifies the exact configured model through the official Ollama Python SDK.
- A substantive product question from Lounge home is supervised through the
  Product-help transition before the model answers. RouteDeck deduplicates the
  live and newly durable LangGraph tool exchange by tool-call identity so the
  post-operation model call receives one observation and produces the final
  assistant response.
- Event-stream reconciliation pushes browser history when the authoritative
  RouteDeck history entry changes and otherwise replaces it, so Back/Forward
  restore RouteDeck locations instead of leaving the application.

## Core Runtime Rule

```text
Corpus feature definitions own product meaning
  -> application composition selects features and entry node
    -> Corpus authorizes identity and supplies opaque-mapped session/request IDs
      -> RouteDeck provisions and owns legal interaction and durable session state
      -> the active node scopes the Corpus agent
        -> the frontend renders permanent chat plus projected surfaces
```

## Docker Development Topology

`compose.yaml` is a process-orchestration boundary, not a product or framework
boundary. The current product runtime starts its backend and frontend services;
the authoritative Design Studio is a separate Vite workbench:

```text
127.0.0.1:5199 -> Vite frontend -> http://backend:8099
127.0.0.1:8099 -> Corpus backend -> embedded RouteDeck + ToolRouter
127.0.0.1:8782 -> RouteDeck Agent Design Studio workbench (host Vite process)
Corpus backend -> http://host.docker.internal:11434 -> host Ollama
```

The Compose `notebook` service on `127.0.0.1:8771` is stale and excluded from
the current startup command. The isolated R1 prototype on `8783` is also stale.
See `docs/local-runtime-runbook.md` for the authoritative procedure.

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
- The broader proposed 53-node notebook Navgraph remains a design artifact, not
  a runtime claim. The live owner application contains 18 product nodes, while
  each immutable Agent build has its own one-node executable RouteDeck
  Application with exact capabilities and surfaces derived from the accepted
  Designer topology.
- Corpus has used explicit, user-authorized RouteDeck fixes where a framework
  contract gap was proven. Each change and purpose is retained under `audits/`;
  the Designer topology alignment required no new RouteDeck modification.
- The ignored Corpus benchmark remains evidence only and is never an import,
  build, runtime, or test dependency. Separately, the ToolRouter sibling was
  used as the verified source of a namespaced, hash-manifested engine snapshot;
  the sibling path itself is not a runtime dependency.
- Frontend primitives are generated from the pinned shadcn 4.13.1
  Radix-Nova registry and remain generic; Lounge and Workspace styling stays
  inside the product feature packages.
- Ollama execution uses `langchain-ollama==1.1.0`; readiness uses the official
  `ollama==0.6.2` SDK. OpenAI execution uses `langchain-openai==1.3.5` with
  the Responses API, and readiness verifies the exact model through OpenAI's
  models endpoint. No adapter switches provider on failure.

## Tests And Evidence

- `.\.venv\Scripts\python.exe -m pytest backend\tests -q` protects host,
  configuration, feature compilation, bindings, runtime, readiness, and HTTP
  bearer identity, conversation selection, and live host behavior.
- `pnpm --dir frontend test`, `typecheck`, and `build` protect the generic shell,
  owner session context, credential UX, pre-bootstrap fragment capture/removal,
  bearer bootstrap, cross-tab refresh coordination, selective stale-token
  reset, active-run reconnection, composer lockout, surface registration,
  continuation behavior, surface/composer sibling placement, mobile
  application-navigation drawer, and the Sources debug interaction contract.
- `.\.venv\Scripts\python.exe scripts\export_frontend_contract.py --check`
  verifies the checked-in Corpus frontend contract without rewriting it.
- `backend/tests/integrations/toolrouter/**` and `backend/tests/sources/**`
  protect exact snapshot provenance, adapter ingestion/reload/retrieval/evalset
  behavior, connector neutrality, source lifecycle, tenancy, HTTP, and the
  RouteDeck Sources node.
- From the sibling RouteDeck checkout, `pnpm --filter @routedeck/react test`,
  `typecheck`, and `build` protect the normalized bootstrap boundary, legal
  recovery actions, and the built package artifacts consumed by Corpus.
- `.\.venv\Scripts\python.exe scripts\smoke_live.py` exercises anonymous
  bearer issuance, opaque conversation selection, declared entry and user runs,
  deliberate SSE disconnect/reconnect, idempotent attachment, real Ollama, and
  durable conversation history.
- `python -m scripts.smoke_restart_recovery_isolated` brackets a real local backend
  process stop inside a disposable runtime. It creates fresh Corpus auth and
  RouteDeck databases plus a source-data root in one owned temporary directory,
  migrates the auth database, starts the backend on loopback, and removes the
  entire runtime after successful verification. Failure preserves the exact
  directory and backend log for inspection. It creates an isolated verified
  owner and real hashed bearer rows directly without mail,
  creates and authorizes a public conversation through HTTP, claims an active
  RouteDeck run, and persists only the temporary bearer plus the exact
  user/organization/membership, auth-session/access-token hash, and conversation
  relationships needed across restart and safe cleanup. Both databases are
  absolute local file-backed SQLite paths owned by the harness, and
  backend/origin URLs are credential-free loopback HTTP URLs. Prepare owns
  the state path through an atomic exclusive-create reservation before any DB or
  HTTP mutation. Verification proves the exact owner identity and public
  conversation remain authorized and the run is durably interrupted. Cleanup
  validates exclusive ownership of every persisted relationship, including no
  shared organization or extra membership/session/token/conversation, before a
  single delete transaction; any mismatch deletes nothing and retains state.
  Successful cleanup cascades the temporary auth/conversation rows and removes
  the state file before the orchestration layer removes both databases. The
  normal `.runtime` databases are never selected or mutated. Direct execution
  of the lower-level `smoke_restart_recovery.py` prepare/verify primitive is
  disabled. This is explicit local verification tooling, not a product
  authentication or recovery path.
- Desktop and mobile browser checks cover the rendered shell, real chat,
  bottom surface/composer dock, hamburger navigation drawer, registration
  navigation/failure, return transition, and live Navgraph.
- `scripts/run_lounge_product_journeys.py` starts disposable Corpus
  backend/frontend pairs with owned SQLite state and exercises Studio-owned
  Lounge journeys through official Playwright Chromium. Mail journeys use the
  real Corpus Gmail SMTP adapter and Mail.tm public API. Result artifacts retain
  transcripts, deterministic backend assertions, screenshots, traces, and
  failures under `.runtime/evaluations/**`; normal development databases are
  not selected.
- `scripts/run_public_lounge_recording.py` protects the combined public chat ->
  Sign in -> Back to Lounge lifecycle. It records both the public-data boundary
  and the first post-resynchronization Surface dispatch, plus screenshot, video,
  trace, HTTP, console, page-error, and aborted-request diagnostics.

The 2026-08-05 product-journey run passed registration/sign-in,
unknown-account recovery neutrality, email verification, and invalid-token
rejection. Duplicate-registration presentation, password-reset
credential/conversation handoff, verification-rate-limit presentation, and
known mail-outage recovery failed with retained evidence. These are Corpus
feature/application integration gaps; no RouteDeck framework change is proven
without a trace contradicting its generic terminal or recovery contracts.

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
