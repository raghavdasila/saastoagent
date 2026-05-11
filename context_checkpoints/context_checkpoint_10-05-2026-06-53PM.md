# Context Checkpoint - 2026-05-10 18:53

## State

SaaStoAgent v0.1 now has a RouteDeck graph-navigation contract and debugger framework for entry/auth/setup/workspace handoff.

RouteDeck replaces the earlier GraphUI naming and is split into:

- product adapter/catalog: `backend/services/route_deck/`
- reusable Python core: `routedeck_framework/routedeck_core/`
- reusable React package: `routedeck_framework/react/`
- framework docs/example: `routedeck_framework/docs/` and `routedeck_framework/examples/minimal-fastapi-react/`

The product shell imports `@routedeck/react` and renders a standalone RouteDeck navigation widget separate from the evidence drawer.

## Runtime And Contract Changes

- `backend/services/route_deck/catalog.py` owns visible node/action/edge/field/policy/test-path definitions.
- `backend/services/route_deck/validate.py` exposes `python -m backend.services.route_deck.validate`.
- `graph_spec.py` keeps executor compatibility while delegating visible manifest data to RouteDeck.
- `ui_actions.py` adapts RouteDeck actions into existing `EntryActionCard` shapes.
- `stage_io.py` validates submitted `selected_action_id` before stage handlers run.
- Invalid selected actions return a recoverable assistant response and valid visible alternatives.
- `EntryGraphTurnResponse` carries `route_deck_snapshot`.
- Frontend state/types retain runtime snapshot, reachable nodes, blocked actions, selected debug node, and debug metadata.

## UI Changes

- RouteDeck compact status strip shows current node, graph node count, next count, valid action count, blocked count, and Map button.
- RouteDeck side map shows:
  - focused current-node graph
  - full-site vertical lane graph
  - allowed actions inspector
  - recovery/input details
  - JSON export
- The full-site graph is now a manifest-sized scrollable SVG canvas with larger reusable nodes and title/badge overlap protection.
- SaaStoAgent hosts the side map in a wider `72rem` drawer on desktop.

## Container Fixes

- Backend Docker image copies `routedeck_framework/`.
- Frontend alias resolves `@routedeck/react` from container-safe paths.
- Docker frontend serves Vite preview instead of dev/HMR to avoid websocket and host `@fs` failures.

## Validation Evidence

- `python -m backend.services.route_deck.validate`: passed.
- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- `docker compose up -d --build frontend`: passed.
- Playwright against `http://localhost:3007` opened Map -> Full graph and confirmed vertical lane order, 11 nodes, 24 paths, no node overlap, no title/badge overlap, and no console errors.

## Still Next

1. Wire generated REST tools into workspace agent execution.
2. Add repo-native tests for RouteDeck sign in, signup, invalid action recovery, direct workspace auth actions, and debugger rendering.
3. Extend RouteDeck beyond entry/auth/setup into REST execution, approvals, QA, and learnings.
4. Enforce or clearly redirect graph-owned setup from direct `/w/:id` deep links when no ready REST connection exists.

## References

- Log: `logs/20260510_1853_routedeck_contract_framework_and_debugger.md`
- ADR: `decisions/ADR-007-routedeck-framework-contract.md`
- Test index: `test_index/route-deck-contract.md`
- Error note: `errors/20260510_routedeck_framework_container_packaging.md`
- Archived previous context: `context_history/20260510_1853_context_before_routedeck_closeout.md`
