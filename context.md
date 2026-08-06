# Corpus Current Context

Updated: 2026-08-06

## Current State

Corpus is the authoritative checkout. Lounge, Workspace, and core Agents use
the documented modular-monolith feature pattern: feature-owned domain and
application layers, RouteDeck controllers, central composition/persistence,
global owner identity, and frontend domain stores that do not copy RouteDeck
interaction state.

The generic evaluator executes real setup and RouteDeck Operations, then checks
bound outcomes, node transitions, domain state, and projection state. The
public Lounge recorder also proves the combined chat -> Sign in -> Back to
Lounge path. The linked RouteDeck Surface host keeps projected controls inert
whenever its canonical store is not `live`.

Source Hub/API Source internals remain outside this completed slice.
`docs/corpus-agent-design/feature-behavior-notes.md` remains untouched and
user-owned. `mockruns/` remains local reference-only material.

## Current Evidence

- Lounge aggregate: 8/8, run `20260806T062952Z-fac606911c`.
- Workspace quick action and Agent create/edit action-state evaluations passed.
- Rendered Workspace/Agents journey passed with one Agent, two immutable
  versions, desktop/mobile proof, trace, and persisted current version 2:
  `.runtime/evaluations/20260806T061531Z-bf0bc49c7c/result.json`.
- Public privacy plus post-chat return passed 2/2 with zero HTTP, console, or
  page errors:
  `.runtime/evaluations/20260806T173245Z-898d846f57/result.json`.
- Backend: 100 tests. Repository: 49 tests. Frontend: 58 tests plus strict
  typecheck/build. Design Studio: 35 tests plus strict typecheck/build.
- Architecture boundaries, Studio parity, generated frontend contracts, and
  documentation ownership gates pass.
- Linked RouteDeck React: 23 tests plus strict typecheck/build.

Exact commands, runtime ports, diagnostics, and changed-file ownership are in
`logs/20260806_2350_post_chat_lifecycle_closeout.md`.

## Runtime

- Normal local stack: `docker compose up --build -d backend frontend`.
- Corpus: `http://127.0.0.1:5199/`.
- Backend readiness: `http://127.0.0.1:8099/readyz`.
- Design Studio: `http://127.0.0.1:8782/`.
- The post-chat acceptance run used isolated local ports `5339`/`8239` and
  disposable SQLite state.

## Remaining Product Work

The architecture audit still has three product-governance items: Studio
blocking completeness/readiness, stale Lounge availability guidance, and
Studio current-result selection. Resolve those before claiming the broader
Agents lifecycle release-ready. Agent archive/delete, Source attachment,
Designer, Sandbox, deployment, and execution runtime remain outside this core
slice.

## Restart Owners

- Checkpoint: `context_checkpoints/2026-08-06-post-chat-lifecycle-closeout.md`
- Session log: `logs/20260806_2350_post_chat_lifecycle_closeout.md`
- Architecture: `architecture/components/corpus-feature-architecture.md`
- Corpus/RouteDeck boundary: `architecture/components/corpus-routedeck-boundary.md`
- Source ownership: `architecture/code-map.md`
- Runtime flows: `SYSTEM_FLOW_INDEX.md`
- Validation meaning: `test_index/README.md`
- Audit: `audits/2026-08-06-implemented-feature-architecture-report.md`
