# 2026-05-10 18:53 - RouteDeck Contract, Framework, And Debugger

## Summary

Implemented RouteDeck as the graph-navigation contract for SaaStoAgent v0.1 and shaped it as a repo-local framework that can later split into PyPI/npm packages.

The work started from entry/auth/setup dead ends and hardcoded action/node strings. It ended with a backend-owned manifest/runtime snapshot, action validation before stage execution, reusable framework packages, product docs, a standalone navigation widget, and Docker/Playwright validation.

## Implemented

- Renamed the planned GraphUI work to `RouteDeck` everywhere because GraphUI already exists elsewhere.
- Added reusable framework package structure under `routedeck_framework/`:
  - `routedeck_core` Python models, runtime helpers, and validation.
  - `react` TypeScript contracts and `RouteDeckDebugger`.
  - framework architecture, minimal example, packaging roadmap, and FastAPI/React reference example.
- Added SaaStoAgent product adapter/catalog under `backend/services/route_deck/`:
  - node ids
  - action ids
  - node specs
  - edge specs
  - action specs
  - field specs
  - sensitive-field policy
  - test paths
  - manifest validation command
- Refactored entry runtime adapters:
  - `graph_spec.py` delegates visible graph manifest data to RouteDeck.
  - `ui_actions.py` derives action cards from RouteDeck action specs.
  - `stage_io.py` validates `selected_action_id` before handlers run.
  - stage handlers keep dynamic business logic while using RouteDeck ids/specs.
  - invalid actions recover with valid alternatives instead of dead-end copy.
- Extended API/schema/frontend state:
  - `EntryGraphTurnResponse` includes RouteDeck manifest/snapshot metadata.
  - frontend types and store retain runtime snapshot, reachable nodes, blocked actions, selected debug node, and debug metadata.
- Added standalone RouteDeck navigation UI:
  - compact status strip in the workbench.
  - side map overlay separate from evidence/trace UI.
  - focus graph for current/incoming/outgoing nodes.
  - full-site graph with vertical lane layout.
  - allowed-action inspector.
  - JSON export.
- Polished the RouteDeck widget as framework UI:
  - manifest-sized full graph canvas.
  - scrollable graph surface.
  - larger reusable node shapes.
  - current/previous/next/idle node states.
  - width-aware title and badge truncation.
  - widened SaaStoAgent map host to `72rem`.
- Fixed container packaging:
  - backend Docker image copies `routedeck_framework/`.
  - frontend alias resolves `@routedeck/react` from container-safe paths.
  - Docker frontend serves Vite preview to avoid HMR websocket and host `@fs` failures.
- Added docs:
  - `docs/route-deck/*`
  - `routedeck_framework/docs/*`
  - minimal example docs
  - packaging roadmap
- Added tests/docs:
  - `backend/tests/test_route_deck_contract.py`
  - `test_index/route-deck-contract.md`
  - `errors/20260510_routedeck_framework_container_packaging.md`
  - `ADR-007-routedeck-framework-contract.md`

## Validation

- `python -m backend.services.route_deck.validate`: passed.
- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- `docker compose up -d --build frontend`: passed.
- Docker frontend logs show Vite preview serving on port 3000 inside the container.
- Docker backend logs show application startup complete and entry requests returning 200.
- Playwright against `http://localhost:3007`:
  - opened RouteDeck `Map`.
  - switched to `Full graph`.
  - confirmed vertical lane order: system, auth, workspace, terminal.
  - confirmed 11 SVG node groups and 24 SVG path elements.
  - confirmed drawer width 1152px and manifest canvas width 1266px.
  - confirmed no same-row node overlap.
  - confirmed no title/badge overlap.
  - confirmed no browser console errors.

## Remaining Gaps

- Generated REST tools are still persisted but not bound into workspace agent execution.
- Direct `/w/:id` deep links can still bypass graph-owned setup until the user explicitly enters setup/auth.
- Browser QA is smoke-level; sign in, signup, invalid action recovery, and setup variants need repo-native automated tests.
- RouteDeck currently covers entry/auth/setup/workspace handoff; REST execution, approvals, QA, and learnings should adopt it in later slices.

## Updated Documentation

- `context.md`
- `context_history/20260510_1853_context_before_routedeck_closeout.md`
- `context_checkpoints/context_checkpoint_10-05-2026-06-53PM.md`
- `SYSTEM_FLOW_INDEX.md`
- `plans/saastoagent_v0_1_workspace_agent_plan.md`
- `architecture/changelog.md`
- `decisions/README.md`
- `decisions/ADR-007-routedeck-framework-contract.md`
- `test_index/README.md`
- `test_index/route-deck-contract.md`
- `errors/20260510_routedeck_framework_container_packaging.md`
