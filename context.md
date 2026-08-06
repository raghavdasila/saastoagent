# Corpus Current Context

Updated: 2026-08-06

## Repository Boundary

- Authoritative checkout: `D:\Dev\AI Projects\saastoagent-v0.1`.
- RouteDeck remains a separate repository. The user authorized only the
  completed reliability changes in `packages/core/src/client/http.ts` and
  `packages/core/src/client/reliability.test.ts`; no other RouteDeck change is
  authorized.
- `docs/corpus-agent-design/feature-behavior-notes.md` remains untouched and
  user-owned. Source Hub/API Source internals were excluded from this slice.

## Implemented State

- Corpus now follows the documented modular-monolith feature pattern for
  Lounge, Workspace, and Agents: feature-owned models/schemas/ports/services,
  RouteDeck controllers, HTTP reads where needed, frontend domain clients and
  stores, central adapters/composition, global auth, and central persistence.
- RouteDeck owns nodes, transitions, legal Operations, projection/session
  state, review, and recovery. Feature stores do not copy that state.
- Workspace reports the real Agent count and explicitly marks unavailable
  Source/recent-activity summaries instead of inventing data.
- Core Agents supports owner-scoped identity, immutable configuration versions,
  authenticated reads, supervised create/edit, duplicate-name conflict, and
  optimistic version conflict.
- The generic evaluator executes Studio action plans through real setup and
  RouteDeck dispatch, then checks bound outcomes, node transitions, domain
  state, and projection state. Semantic judging is reserved for conversation
  plans.
- Architecture drift is mechanically checked for Lounge, Workspace, Agents,
  global frontend auth, and shared backend code.
- Architecture visual: `docs/assets/corpus-architecture-boundaries.png`.

## Fresh Evidence

- Full Lounge aggregate: 8/8 passed,
  `.runtime/evaluations/20260806T062952Z-fac606911c/result.json`.
- Workspace quick action passed:
  `.runtime/evaluations/20260806T060822Z-81f55dd99d/result.json`.
- Agent create passed:
  `.runtime/evaluations/20260806T060253Z-3925a7c131/result.json`.
- Agent edit passed:
  `.runtime/evaluations/20260806T060610Z-97d5395b7c/result.json`.
- Rendered Workspace/Agents journey passed:
  `.runtime/evaluations/20260806T061531Z-bf0bc49c7c/result.json` with desktop,
  mobile, trace, one Agent, two immutable versions, and current version 2.
- Backend: 100 passed. Root: 49 passed. Frontend: 58 passed plus typecheck and
  production build. Design Studio: 34 passed plus typecheck/build.
- Architecture boundary, Studio parity, and generated frontend-contract gates
  passed. The frontend build retains only Vite's non-failing chunk-size
  advisory; backend retains one upstream TestClient deprecation warning.
- Authorized RouteDeck core: 89 passed plus typecheck/build.

## Runtime

- Normal local runtime: `docker compose up --build -d backend frontend`.
- Frontend smoke URL: `http://127.0.0.1:5199/`.
- Backend readiness: `http://127.0.0.1:8099/readyz`.
- Evidence runs used isolated local ports recorded in each result artifact and
  disposable SQLite databases.

## Git Boundary

- Earlier authorized Corpus foundation changes were committed as `181651d`.
- The implementation and closeout changes after that commit are not staged or
  committed by this session. Do not infer push permission.
- RouteDeck changes were not staged or committed.

## Next Product Slice

Use the same feature architecture for the next horizontally scoped Corpus
feature. Keep Source internals excluded until their separate lane is explicitly
reconciled. Agent archive/delete, Source attachment, Designer, Sandbox,
deployment, and execution runtime remain outside this completed core slice.

## Documentation Owners

- Closeout checkpoint:
  `context_checkpoints/2026-08-06-feature-architecture-evaluator-workspace-agents.md`
- Closeout log:
  `logs/20260806_feature_architecture_evaluator_workspace_agents.md`
- Architecture: `architecture/components/corpus-feature-architecture.md`
- Source ownership: `architecture/code-map.md`
- Runtime flows: `SYSTEM_FLOW_INDEX.md`
- Validation meaning: `test_index/README.md`
