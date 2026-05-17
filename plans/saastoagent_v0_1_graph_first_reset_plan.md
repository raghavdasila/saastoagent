# SaaStoAgent v0.1 Graph-First Reset Plan

Status: Paused for architecture correction. Graph spine implemented on 2026-05-16; agent-first shell/router reset attempted on 2026-05-16, but the UX contract is not accepted. See `context_checkpoints/context_checkpoint_17-05-2026-12-14PM.md`.

## May 17 Correction

The next plan must reset the agent-turn contract before more implementation.
Current issue: the implementation treats graph action eligibility as visible UI,
so chat becomes an action router with forms/buttons around it.

Correct target:

- graph owns state and eligibility
- RouteDeck bridges state, surfaces, evidence, and diagnostics
- `/turn` produces assistant message, internal capabilities, agent-authored
  proposals, optional active surface, evidence, and diagnostics
- frontend renders proposals, not raw eligible actions
- forms open only after user initiation or accepted proposal

## Principle

One backend-owned application graph rooted at `home` owns navigation, capabilities, action eligibility, context lens, evidence, and recovery. RouteDeck is the only bridge to frontend surfaces.

## Implemented In This Pass

- Added ADR-011 for full app graph ownership.
- Added backend app graph contract and runtime under `backend/services/app_graph/`.
- Added graph-owned endpoints:
  - `GET /api/app/graph/snapshot`
  - `POST /api/app/graph/turn`
  - `POST /api/app/graph/action`
- Added graph nodes for home, auth, SaaS Agent select/create, agent home, connection/schema/catalog, execution/input/approval/result, knowledge, memory, learning, QA, and recovery.
- Added RouteDeck manifest generation and graph/handler parity tests.
- Added frontend `AppGraphShell` for `/app/...` graph routes.
- Compatibility routes hydrate graph context instead of mounting the old operator gateway.

## Implemented In Agent-First Reset

- Rebuilt `AppGraphShell` as a chat-first SaaS Agent desk instead of a graph/debugger shell.
- Removed product-visible RouteDeck/action-id/node/reachable copy; diagnostics now hold internal graph details.
- Added `AppGraphTurnRouter` as an app-owned router adapter with disabled/OpenAI/Ollama provider modes.
- Kept RouteDeck deterministic and model-free; router provider secrets live in SaaStoAgent settings.
- Updated `/api/app/graph/turn` to clarify naturally in no-model mode and execute only eligible structured decisions.
- Added Medusa Storefront, Medusa Admin, and Custom API connection target options.
- Added guardrail tests for router schema behavior, required fields, Medusa options, and hidden product copy.

## Remaining Purge Work

- Remove legacy `OperatorGateway` and local operator capability registry once every existing renderer has a graph-native replacement.
- Replace the snapshot-only selected SaaS Agent RouteDeck endpoint with wrappers over the app graph.
- Convert QA runner scenarios from visible-label scripts to graph-authored node/action/evidence scenarios.
- Add SSE streaming for live graph turns after the synchronous action endpoint is stable.

## Validation

- Backend graph contract plus entry RouteDeck contract: 15 passed.
- Full backend tests: 40 passed.
- Frontend type-check: passed.
- Frontend production build: passed.
- Agent-first focused validation: app graph contract 8 passed; full backend 44 passed; RouteDeck validator passed; frontend type-check/build passed; Playwright smoke passed with no internal RouteDeck/graph/action-id copy before diagnostics.
