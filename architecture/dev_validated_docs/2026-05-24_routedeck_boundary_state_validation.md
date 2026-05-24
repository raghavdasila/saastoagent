# RouteDeck Boundary State Validation

Date: 2026-05-24
Status: Validated by backend contract tests and frontend type-check

## Scope

This validation covers the RouteDeck/Corpus boundary cleanup:

- Corpus state/action API routes now cross the RouteDeck runtime boundary.
- The stale SaaStoAgent adapter name is removed.
- Frontend SaaSAgent context comes from RouteDeck state.
- Zustand is reduced to UI-local state and does not act as graph/app state.

## Validated Runtime Contract

Backend:

- `/api/corpus/state` calls `route_deck_runtime.snapshot(...)`.
- `/api/corpus/action` calls `route_deck_runtime.dispatch(...)`.
- Route-local conversion helpers preserve RouteDeck graph state, projection,
  location/replace path, active surface, messages, and metadata.
- `CorpusRouteDeckRuntime` satisfies the `RouteDeckRuntime` protocol.
- Backend app graph files do not export/import `SaaStoAgentRouteDeckAdapter`.

Frontend:

- `AppGraphShell` derives active SaaSAgent identity from RouteDeck state.
- `api.withSaaSAgent(...)` makes SaaSAgent request context explicit.
- `saasAgentUiStore` owns UI-only state such as active tabs, drafts, local
  selections, and a mirrored active id.
- RouteDeck operation/node/surface ids used by Corpus live in
  `corpusRouteDeckCatalog.ts`.

## Evidence

- `python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q`
  - Result: `65 passed`
- `npm run type-check` from `frontend`
  - Result: passed
- Backend source scan:
  - no `SaaStoAgentRouteDeckAdapter`
  - no `routedeck_adapter`
  - no `test_routedeck_adapter_contract`

## Not Validated In This Pass

- Docker UI E2E was not rerun after this cleanup.
- Browser-level no-flicker/no-navigation regression coverage still needs to be
  added for surface/auth transitions.
- Public deployed-chat query continuity and raw JSON result UX are still open.
