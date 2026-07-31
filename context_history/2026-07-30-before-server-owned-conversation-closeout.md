# Corpus Current Context (Archived 2026-07-31)

Updated: 2026-07-30

## Repository Boundary

- Authoritative checkout: `D:\Dev\AI Projects\saastoagent-v0.1`.
- `docs/corpus-agent-design/feature-behavior-notes.md` is user-owned and must
  not be edited by Codex.
- RouteDeck source dependency: sibling `D:\Dev\AI Projects\routedeck`, linked
  at version 0.1.0 through pnpm `link:` package junctions. Corpus consumes the
  sibling packages' built `dist` exports, not Git or npm-installed copies.
- RouteDeck implementation changes are never implicit Corpus work. Diagnose
  RouteDeck read-only as needed, but obtain explicit user approval before
  editing, staging, committing, or pushing any file in the sibling checkout.
- The ignored `benchmark/saastoagent-v0.1/` is read-only behavior/visual
  evidence and is not a runtime dependency.
- ToolRouter source evidence came from sibling
  `D:\Dev\AI Projects\openapi-toolrouter-benchmark` at main `2611801e` plus
  dirty working-tree bytes. Corpus runs only the repository-contained namespaced snapshot
  recorded by `source_manifest.json`; it does not import the sibling checkout.
- The runnable Corpus, Sources/ToolRouter integration, owner workspace, and
  Docker development stack are committed on `main` as `9a1753f`.

## Current State

- The fresh-project backend/frontend framework, owner identity, Workspace, and
  the launch-scope Sources/API connector are implemented and runnable.
- The generic backend host owns configuration, lifespan, transport, session
  selection, readiness, and explicit failure behavior without product literals.
- Client bootstrap now issues or rotates opaque bearer credentials, validates
  a per-tab public conversation ID against the authorized catalog, creates a
  conversation only when the catalog is empty, and resumes RouteDeck only
  through the host's internal mapping. Access tokens stay in memory; browser
  refresh credentials use IndexedDB plus Web Locks.
- Post-ready RouteDeck projection resync/reconnect no longer remounts Corpus.
  This prevents owner-session and initial-conversation effects from restarting
  on every event while preserving initial/replacement/error recovery gates.
- Surface integration now fails closed against one source of truth: the
  compiled Corpus frontend contract is checked into the frontend
  deterministically, backend parity is tested, and RouteDeck requires the
  runtime registry to match its unique component set exactly.
- Credential-node composer availability now comes from RouteDeck's typed static
  node contract. Corpus declares the affected nodes and user-facing copy.
- Lounge account mutations remain supervised RouteDeck Operations. Private
  form surfaces project only a public `form_handle`; credential values remain
  encrypted. Successful registration/sign-in atomically adopts the selected
  anonymous conversation and returns owner credentials outside RouteDeck state.
- Owner authentication continuation is refresh-safe: an existing Corpus owner
  session hides credential fields and exposes one explicit retry of the already
  declared `authentication_completed` affordance; there is no automatic retry
  loop or credential replay.
- Approved RouteDeck fix `d24788f` distinguishes an expired exact resume
  capability from a missing/invalid one and returns typed HTTP 410
  `resume_capability_expired`, allowing the existing terminal
  `start_new_session` recovery policy to run.
- Verification/reset fragments are captured before RouteDeck bootstrap can
  replace browser history, retained only in frontend memory, and immediately
  removed from the visible URL.
- `lounge.home` declares its welcome as a generic RouteDeck entry turn.
  RouteDeck owns the derived request ID, durable claim, detached model task,
  cursor replay, restart interruption, and terminal history. Corpus contains no
  Lounge node check, greeting ID, convergence timer, or conversation-failure
  authentication reset.
- The frontend now uses pinned shadcn/Radix-Nova primitives. Suggested actions
  render under the latest assistant response, long content wraps, and
  Workspace styling is feature-owned rather than mixed into the generic shell.
- Active/review surfaces now occupy a bounded bottom dock immediately above
  the composer, outside the independently scrolling conversation. At mobile
  width the Workspace rail opens from a header hamburger Sheet, the Navgraph
  retains its own header drawer, and the surface/composer stay at the bottom of
  the viewport instead of rising above a bottom navigation row.
- The standalone **RouteDeck Agent Design Studio** now lives under
  `docs/corpus-agent-design/workbench`, with Corpus as its active project. It is
  a local prototype for reviewing
  Workspace/Agents user and agent intents, expected behaviors, mock chats,
  provisional RouteDeck design objects, and tightly sandboxed inline surfaces; its labeled seed and
  approvals do not assert implemented product behavior. Codex drives one atomic
  behavior at a time for user review and explicit acceptance. Surfaces render
  immediately above the SuggestedAction row and composer, grow to half the chat region,
  then scroll internally; Operation-only behavior has no surface. The studio
  uses a three-region desktop shell, mobile overlay project navigation,
  centralized light/dark tokens, shared editor-section primitives, and
  data-driven project copy and feature navigation. The version
  20 seed now covers
  behavior-note sections 0–4 with `Lounge 8`, `Workspace 6`, `Agents 9`,
  `Source Hub 5`, and `API Source 9`. Lounge owns unauthenticated product help
  and six approved implementation-backed account entry/recovery behaviors;
  Workspace owns the authenticated home and approved sign-out behavior. Agents
  has no product-level draft-agent concept. New or materially changed feature
  behaviors remain draft for review. Design edits autosave to
  `docs/corpus-agent-design/workbench/design-state.json` through the local Vite
  server; **Export JSON** downloads the current formatted Corpus design without
  replacing autosave, and only the theme preference remains in browser local
  storage. The
  dedicated Feature policies destination contains only feature-scoped
  AgentPolicy instructions. Each behavior is the human-readable design unit
  for one provisional feature Node and owns its Node, Capability, Surface, and
  Operation AgentPolicies. Operations are first-class objects with a name,
  explicit product effect, and expandable contract details; the effect is not
  a restatement of the chat affordance. SuggestedActions are
  separate chat invitations that reference a defined Operation. The studio
  exposes no policy or RouteDeck declaration IDs and makes no compiled or
  effective-policy claim; full identifiers, references, topology, providers,
  guards, transitions, and bindings are deferred to complete extraction.
- The implementation-owned Agent Design parity checker now reports a concise
  root-cause summary by default and retains every scope-level mismatch behind
  `--verbose`. Lounge is parity-clean. The only current mismatch is manifest
  coverage for the separately compiled `workspace` and `sources` features.
- The live Navgraph remains a docked, in-place expandable desktop rail. At
  mobile width it switches to a shadcn Sheet drawer without changing RouteDeck
  state ownership.
- Lounge is a top-level live feature with eight nodes covering public
  arrival/product help, owner sign-in, registration, forgot/reset, verification
  confirmation, and signed-in verification delivery. Workspace owns only its
  session-bound Home node; Sources adds `sources.home`, for ten live nodes.
- Lounge declares feature-, Node-, Capability-, Surface-, and Operation-scoped
  RouteDeck AgentPolicies derived from Design Studio version 20. The shell says
  `Corpus Lounge`, hides private feature navigation until authenticated entry,
  and never presents internal Operation/Node/AgentPolicy identifiers as product
  language.
- Real Lounge product questions transition through the Product-help Operation
  and finish with a normal assistant response. RouteDeck now deduplicates the
  live and durable LangGraph tool exchange before the post-tool model call and
  pushes browser history for event-stream operations when the authoritative
  history entry changes.
- Lounge uses durable public Corpus conversations mapped to internal RouteDeck
  sessions and real local Ollama `gemma4:latest` responses through native
  `langchain-ollama`. Readiness uses the official Ollama SDK. No canned/model
  fallback exists.
- Corpus authentication uses FastAPI Users behind Corpus interfaces, a separate
  Alembic-managed database, anonymous and owner token sessions, hash-only
  credential persistence, rotating refresh, rate limits, atomic conversation
  adoption, and bearer-backed APIs. Direct RouteDeck session creation is
  rejected by the Corpus host.
- Deployed-agent users remain outside this identity subsystem.
- Gmail STARTTLS delivery is configured for `no-reply@saastoagent.com`. The
  real reference and live Corpus verification/reset requests were accepted by
  Gmail; unavailable delivery still fails explicitly without a fallback.
- `features/sources/` owns generic owner-scoped source identity, immutable
  revisions, connector registration, neutral retrieval/evalset contracts,
  same-origin APIs, and the Sources RouteDeck node/debug surface. API is a
  connector, not a product node.
- Generic `SourceSettings` now requires only the explicit persistence root,
  and generic `sources/http.py` exposes only list, get, retrieve, and evalset
  transport. API owns its upload limit and multipart route under
  `connectors/api/`.
- `ApiSourceConnector` depends on the replaceable `ApiSourceEngine` port. The
  single `connectors/api/toolrouter.py` bridge translates ToolRouter contracts;
  concrete registration lives in `app/source_composition.py`.
- `integrations/toolrouter/` owns one replaceable facade plus a private exact
  24-module engine snapshot and every ToolRouter embedding, Ollama, model, and
  timeout value. Generic Sources files do not contain ToolRouter or endpoint
  contracts.
- API upload now performs declared validation/repair, normalized OpenAPI
  persistence, `resource_first_v1` graph/conformance, pinned local MiniLM
  indexing, persisted GRAG retrieval, and source-grounded evalset generation,
  deterministic validation, independent Qwen review, quarantine/export, model
  digest evidence, and token accounting.
- The debug UI is explicitly experimental. Reviewed candidates are not called
  human gold. Agent Designer, Sandbox, public Web, Operations, and deployment
  remain deferred within the launch milestone.
- The Sources debug UI now makes the real ToolRouter proof explicit with a
  four-stage API collection, graph/index, GRAG retrieval, and reviewed-evalset
  rail. These stages are derived surface state, not additional feature nodes.
- The Structure explorer now keeps the complete proposal intact and layers the
  implemented files beside it. Green means implemented, amber means planned,
  and blue means a folder contains both. Evidence is recorded in
  `logs/20260724_toolrouter_video_evidence.md`.
- Docker Compose now owns the local development process topology: separate
  backend, frontend, and notebook services, loopback-only published ports,
  healthy startup, source reload mounts, and persistent `.runtime` data.
- ToolRouter remains embedded in the backend. Its configured Ollama client now
  accepts the explicit container-to-host endpoint while retaining loud failure
  behavior; all ToolRouter settings remain ToolRouter-owned.
- The filtered parent build context admits only the required Corpus and sibling
  RouteDeck source. CPU-only PyTorch reduced the backend image from 8.94 GB to
  2.39 GB without changing the pinned MiniLM CPU runtime.

## Runtime

```powershell
docker compose up --build
```

- Frontend/smoke URL: `http://127.0.0.1:5199/`
- Backend: `http://127.0.0.1:8099/`
- Structure explorer: `http://127.0.0.1:8771/#structure`
- Persistence: RouteDeck SQLite, `.runtime/corpus-auth.sqlite3`, and
  owner-scoped `.runtime/sources/` revision/artifact trees
- Configuration: ignored `.env.local`, generated from explicit setup
- Models: local Ollama 0.21.0 with `gemma4:latest` and
  `qwen2.5-coder:7b`; pinned MiniLM revision on CPU. Ollama remains on the
  host and Compose uses `http://host.docker.internal:11434` explicitly.

## Validation Baseline

- Current bearer/conversation delivery: 66 Corpus backend tests and 31 frontend
  tests pass with strict frontend typecheck/build. The sibling RouteDeck suite
  passes 177 Python tests and 154 TypeScript workspace tests plus typecheck,
  build, Ruff, and mypy. Real HTTP smoke verifies bearer issuance, opaque
  conversation selection, declarative Lounge entry, cursor reconnect,
  idempotent attachment, durable history, and process-restart recovery against
  local Ollama `gemma4:latest`.

- Agent design parity reporting: 4 focused checker tests passed. The real
  default run returned exit 1 with 124 mismatches summarized into seven groups;
  `--verbose` returned the same exit and all 124 detailed evidence lines.
- The former cookie-bound `/api/auth/recover` and client-side greeting timeout
  evidence is superseded. Current recovery reconnects an authorized public
  conversation to its server-owned RouteDeck run; a backend crash durably
  interrupts the claimed turn while preserving identity and conversation.
- RouteDeck Agent Design Studio: 17 tests passed; strict typecheck and
  production build passed. Browser checks at 1440x900 and 390x844 verified the
  branded Corpus project shell, JSON export interaction, separate feature-policy
  destination, mobile project drawer, centralized light/dark themes, internal
  editor scrolling, and zero horizontal overflow or warning/error logs.
- Responsive shell correction: 25 frontend tests passed plus strict typecheck
  and production build. At 390x844 the live browser measured zero horizontal
  overflow, a 161.5px surface dock directly above the composer, composer bottom
  y=834, no bottom navigation row, and one working full-height hamburger
  drawer. At 1440x900 the 240px desktop rail remained and the surface stayed
  directly above the composer. Browser warning/error logs were empty.
- Expired-session recovery change: 63 Corpus backend tests and 23 frontend
  tests passed; frontend strict typecheck and production build passed. The
  sibling RouteDeck FastAPI suite passed 25 tests, focused Ruff checks passed,
  and both repositories' context/documentation checks passed. Rebuilt local
  Docker then reproduced the preserved expired owner route as HTTP
  `410 -> 201 -> event stream 200`; the browser reached a stable Lounge with
  no expired-session copy and no warning/error console entries.
- Post-ready continuity correction: the pre-fix browser switched between the
  application and bootstrap shell 33 times in six seconds while the backend
  recorded 58 session reloads, 58 SSE reconnects, and 116 auth reads in 30
  seconds. After rebuilding, 150/150 samples over 15 seconds stayed on the
  Lounge with zero transitions and zero browser warning/error entries. The
  full RouteDeck React package passed 18 tests plus typecheck/build; Corpus
  passed 23 frontend tests plus typecheck/build.
- Current boundary-fix regression: 60 Corpus backend tests and 22 frontend
  tests passed; frontend strict typecheck and production build passed. The
  sibling RouteDeck checkout passed 520 non-real Python tests, all package
  tests, root typecheck, and root build. Local Ollama was started through the
  installed official executable and the real Corpus readiness tests passed
  against `gemma4:latest`.

- Docker stack: backend, frontend, and notebook healthy; all three smoke URLs
  returned HTTP 200 on the final local run.
- Backend: 59 tests passed on the host lane; clean dependency check. The image
  passes the 57 environment-independent contracts, while its two live tests
  deliberately target host loopback and are therefore run on the host.
- Frontend image: 19 tests passed; strict typecheck and production build passed.
  Repository unittest suite: 15 passed. Compose config, design notebook, and
  context coverage validation passed.
- Docker UI smoke: real Ory `api.yaml` -> 56 endpoints / 477 nodes / 876 edges /
  477 cards -> `ASK_DISAMBIGUATE` retrieval -> reviewed evalset 1/1 accepted,
  zero quarantined, 3,823 offline tokens. Backend recreation retained the
  persisted Source and artifacts.

- Backend: 56 tests passed in the repository `.venv`; one upstream
  Starlette/httpx deprecation warning only.
- Frontend: 19 tests passed; strict typecheck and production build passed.
- Python dependency check: no broken requirements. Repository unittest suite:
  12 passed.
- Linked RouteDeck React: 13 tests passed; typecheck and package build passed.
- Historical cookie-era live smoke passed with a real greeting and user answer;
  it no longer describes the current transport. The current bearer smoke is
  recorded at the top of this validation baseline.
- The shadcn change passed frontend component tests, strict typecheck,
  production build, backend tests, readiness, and the live Ollama smoke.
- Fresh rendered checks passed owner registration/adoption, home continuation,
  reload, explicit verification-delivery failure, logout/fresh guest, sign-in
  resumption, generic reset request, first-field focus, and 390x844 layout with
  no horizontal overflow.
- After configuring Gmail, a fresh live registration adopted a guest session;
  the verification endpoint returned 204 and reset request returned 202 for
  real messages accepted by Gmail for `raghavdasila@highpolar.io`.
- A pre-fix fresh startup trace isolated 14,664 ms of 14,804 ms total startup
  in the real Ollama greeting. After the fix, the rendered verification surface
  appeared in 2,435 ms in the in-app browser, its fragment was absent from the
  visible URL, and the token-backed Verify email action remained enabled.
- A live Corpus assistant-turn probe emitted 82 separate `assistant_delta`
  frames: first delta at 13,419.8 ms and durable `assistant_end` at 14,235.9 ms.
  RouteDeck's gated coordinator test proves progress is published while
  completion remains pending, and the Corpus rendering test proves partial
  progress is visible with streaming status.
- A 2026-07-23 local browser load crossed the linked RouteDeck bootstrap
  boundary, reached RouteDeck `Ready`, and restored the real persisted Lounge
  greeting. Backend `/healthz` and `/readyz` both returned 200.
- The real Ory Kratos v26.2.0 API upload produced 56 endpoints, 316 schemas,
  two security schemes, zero repairs, 477 graph nodes, 876 edges, and 477
  cards. `create a new identity` returned `ASK_DISAMBIGUATE` with
  `low_score_margin` and `api:createRecoveryLinkForIdentity` at 0.4280.
- Real evalset run `api-debug-v1` completed/accepted 1 of 1, quarantined zero,
  recorded 2,936 offline tokens and exact Gemma/Qwen digests, and exported a
  reviewed `api:listIdentitySessions` candidate. A hard page reload retained
  the source/counts and a second retrieval succeeded from persisted artifacts.
- Desktop and 390x844 Sources renders passed; browser warning/error logs were
  empty. Local backend `/readyz` returned 200 after restart.
- A 35-second H.264 browser-evidence walkthrough now records the corrected
  living Structure explorer and the real source metrics, GRAG retrieval result,
  and reviewed evalset result. See
  `logs/evidence/20260724-toolrouter-sources-walkthrough.mp4`.
- A fresh authenticated browser run uploaded the real Ory Kratos `api.yaml`
  and completed all four evidence stages: 56 endpoints, 477 nodes, 876 edges,
  477 cards; `ASK_DISAMBIGUATE` retrieval with `low_score_margin`; and an
  independently reviewed 1/1 evalset with 2,936 offline tokens and zero
  quarantined candidates. The 1440x900 and 390x844 layouts passed and browser
  warning/error logs were empty.
- After the Source boundary refactor, a fresh real authenticated HTTP run used
  Ory Kratos `api.yaml` through the production API-owned upload router. Source
  `ex1IDkDESNq_5EWy` reached ready with 56 endpoints, 477 nodes, 876 edges, and
  477 cards; retrieval returned `ASK_DISAMBIGUATE` / `low_score_margin`; and
  evalset `boundary-proof-65553b771add` completed ready with 1 accepted, 0
  quarantined, and 2,936 offline tokens using exact Gemma/Qwen digests.

## Locked Boundaries

- Corpus owns product meaning; RouteDeck owns legal interaction state.
- Owner identity is Corpus-host-owned; RouteDeck receives only an authorized
  internal session ID from the consumer-owned selector.
- The broader 53-node notebook remains a proposed design, not a live runtime.
- Sources owns generic lifecycle; connector implementations own source-family
  behavior. API upload config/HTTP and the API engine port are connector-owned;
  the explicit API/ToolRouter bridge alone translates ToolRouter contracts.
- Failures remain visible failures; no fixture, canned response, or alternate
  provider may masquerade as product success.

## Next Concrete Step

User-test first-open Lounge, reload during an active response, registration,
sign-in, and sign-out at `http://127.0.0.1:5199/` against a freshly initialized
bearer schema. After acceptance, map the compiled Workspace and Sources
features into the implementation manifest.
