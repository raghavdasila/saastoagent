# Corpus Current Context

Updated: 2026-07-24

## Repository Boundary

- Authoritative checkout: `D:\Dev\AI Projects\saastoagent-v0.1`.
- RouteDeck source dependency: sibling `D:\Dev\AI Projects\routedeck`, linked
  at version 0.1.0 through pnpm `link:` package junctions. Corpus consumes the
  sibling packages' built `dist` exports, not Git or npm-installed copies.
- The ignored `benchmark/saastoagent-v0.1/` is read-only behavior/visual
  evidence and is not a runtime dependency.
- ToolRouter source evidence came from sibling
  `D:\Dev\AI Projects\openapi-toolrouter-benchmark` at main `2611801e` plus
  dirty working-tree bytes. Corpus runs only the repository-contained namespaced snapshot
  recorded by `source_manifest.json`; it does not import the sibling checkout.
- Earlier notebook work is committed alone as `2e2a3d9 docs: add Corpus feature
  behavior notebook`. The ToolRouter implementation remains an uncommitted
  working-tree change so it is not mixed with concurrent auth/UI work.

## Current State

- The fresh-project backend/frontend framework, owner identity, Workspace, and
  the launch-scope Sources/API connector are implemented and runnable.
- The generic backend host owns configuration, lifespan, transport, session
  selection, readiness, and explicit failure behavior without product literals.
- `RouteDeckBootstrapBoundary` now owns bootstrap startup, recovery phase/action
  selection, and ready gating. Corpus owns the recovery copy and revokes its
  browser auth/owner handle before invoking RouteDeck's exposed
  `start_new_session` action. The React host continues to own permanent chat,
  navigation/history, the surface registry, Navgraph slot, and responsive
  desktop/mobile layout.
- Verification/reset fragments are captured before RouteDeck bootstrap can
  replace browser history, retained only in frontend memory, and immediately
  removed from the visible URL.
- The Lounge shell now renders before its real Ollama greeting completes. The
  composer reports the pending conversation, and each validated assistant
  delta is rendered immediately before the durable terminal turn replaces the
  transient progress. Credential and token surfaces skip the greeting entirely.
- The frontend now uses pinned shadcn/Radix-Nova primitives. Suggested actions
  render under the latest assistant response, long content wraps, and
  Workspace styling is feature-owned rather than mixed into the generic shell.
- The live Navgraph remains a docked, in-place expandable desktop rail. At
  mobile width it switches to a shadcn Sheet drawer without changing RouteDeck
  state ownership.
- Workspace has seven live nodes covering Lounge, owner sign-in, registration,
  forgot/reset, verification, and session-bound owner home. Sources adds one
  session-bound `sources.home` node, for eight current live nodes.
- Lounge uses durable anonymous guest sessions and real local Ollama
  `gemma4:latest` responses through native `langchain-ollama`. Readiness uses
  the official Ollama SDK. No canned/model fallback exists.
- Corpus owner authentication is implemented with FastAPI Users behind Corpus
  interfaces, a separate Alembic-managed database, personal organizations,
  revocable hashed sessions, permanent RouteDeck claims, opaque owner-route
  handles, database rate limits, and same-origin APIs.
- Deployed-agent users remain outside this identity subsystem.
- Gmail STARTTLS delivery is configured for `no-reply@saastoagent.com`. The
  real reference and live Corpus verification/reset requests were accepted by
  Gmail; unavailable delivery still fails explicitly without a fallback.
- `features/sources/` owns generic owner-scoped source identity, immutable
  revisions, connector registration, neutral retrieval/evalset contracts,
  same-origin APIs, and the Sources RouteDeck node/debug surface. API is a
  connector, not a product node.
- `integrations/toolrouter/` owns one replaceable facade plus a private exact
  24-module engine snapshot. Only the API connector may import that facade;
  generic Sources files do not contain ToolRouter or endpoint contracts.
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

## Runtime

```powershell
.\scripts\init-local.ps1
.\scripts\run-backend.ps1
.\scripts\run-frontend.ps1
```

- Frontend/smoke URL: `http://127.0.0.1:5199/`
- Backend: `http://127.0.0.1:8099/`
- Persistence: RouteDeck SQLite, `.runtime/corpus-auth.sqlite3`, and
  owner-scoped `.runtime/sources/` revision/artifact trees
- Configuration: ignored `.env.local`, generated from explicit setup
- Models: local Ollama 0.21.0 with `gemma4:latest` and
  `qwen2.5-coder:7b`; pinned MiniLM revision on CPU

## Validation Baseline

- Backend: 52 tests passed in the repository `.venv`; one upstream
  Starlette/httpx deprecation warning only.
- Frontend: 19 tests passed; strict typecheck and production build passed.
- Python dependency check: no broken requirements. Repository unittest suite:
  12 passed.
- Linked RouteDeck React: 13 tests passed; typecheck and package build passed.
- Live smoke passed with guest cookie, real greeting, real user answer, SSE
  completion, and durable `assistant,user,assistant` history.
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

## Locked Boundaries

- Corpus owns product meaning; RouteDeck owns legal interaction state.
- Owner identity is Corpus-host-owned; RouteDeck receives only an authorized
  internal session ID from the consumer-owned selector.
- The broader 53-node notebook remains a proposed design, not a live runtime.
- Sources owns generic lifecycle; connector implementations own source-family
  behavior. The API connector alone translates ToolRouter contracts.
- Failures remain visible failures; no fixture, canned response, or alternate
  provider may masquerade as product success.

## Next Concrete Step

Reconcile Agent Designer behavior and the agent-configuration contract before
choosing planner/executor internals. Then connect the now-proven Sources facade
to Agent Designer without bypassing its connector-neutral contracts.
