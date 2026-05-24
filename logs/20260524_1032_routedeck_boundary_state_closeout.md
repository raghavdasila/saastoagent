# 2026-05-24 10:32 IST - RouteDeck Boundary And State Closeout

## Scope

This session focused on correcting the RouteDeck/Corpus/SaaStoAgent boundary
after the product direction was clarified:

- RouteDeck is reusable state management for agentic apps.
- Corpus is the SaaStoAgent product layer that consumes RouteDeck.
- LangGraph/backend services own execution and graph truth.
- React renders RouteDeck-projected state.
- Zustand remains frontend-local UI state only, not the app graph source of
  truth.

## Implemented

- Reframed RouteDeck docs and prompts around agentic app state management rather
  than navigation-only runtime language.
- Split backend Corpus RouteDeck responsibilities into named helpers:
  - `CorpusRouteDeckRuntime`
  - `CorpusRouteDeckStateProjector`
  - `CorpusOperationPolicy`
  - `CorpusSurfaceRegistry`
  - navgraph helpers
- Replaced stale SaaStoAgent adapter naming with `CorpusRouteDeckRuntime`.
- Routed `/api/corpus/state` through `route_deck_runtime.snapshot(...)`.
- Routed `/api/corpus/action` through `route_deck_runtime.dispatch(...)`.
- Kept natural-language turn streaming on `CorpusGraphRuntime`, while empty
  Corpus stream subscriptions use RouteDeck projection events.
- Removed `backend/services/app_graph/routedeck_adapter.py`.
- Removed `SaaStoAgentRouteDeckAdapter` imports, exports, aliasing, and tests.
- Added route-local conversion helpers from RouteDeck runtime/dispatch objects
  to Corpus response DTOs.
- Added backend contract tests proving RouteDeck-shaped routes do not call
  `corpus_graph_runtime.corpus_state(...)` or
  `corpus_graph_runtime.corpus_action(...)`.
- Added behavior tests for state/action conversion preservation.
- Moved frontend RouteDeck constants into `corpusRouteDeckCatalog.ts`.
- Renamed frontend Zustand state from `saasAgentStore` to
  `saasAgentUiStore`.
- Changed builder surfaces to derive active SaaSAgent context from RouteDeck
  state and pass SaaSAgent context explicitly through `api.withSaaSAgent(...)`.
- Removed the global API/storage fallback that made local storage act like an
  implicit app-state source of truth.
- Kept the surface-opening state connected to the RouteDeck React hook so
  surface transitions can show "Opening surface" instead of falling through to
  route-level navigation symptoms.

## Important Boundary Outcome

The current frontend boundary is:

```text
RouteDeckStore
  -> graph node, projection, legal operations, active surface, location,
     active SaaSAgent id

saasAgentUiStore (Zustand)
  -> mirrored active id for legacy shell ergonomics, selected tabs, drafts,
     chat pane state, UI selections
```

Zustand does not replace RouteDeck and RouteDeck does not replace all local UI
state. RouteDeck owns agentic application state. Zustand sits beside it for
ephemeral UI-only state that is not graph truth.

## Verification

- `python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q`
  - Result: `65 passed`
- `npm run type-check` from `frontend`
  - Result: passed
- Backend source scan for stale adapter names:
  - no `SaaStoAgentRouteDeckAdapter`
  - no `routedeck_adapter`
  - no `test_routedeck_adapter_contract`

Docker browser E2E was not rerun in this closeout. The latest Docker UI E2E and
Medusa Docker E2E evidence remains from the May 22 closeout.

## Carry Forward

1. Run `npm run e2e:docker` and `npm run e2e:medusa:docker` after the next
   runtime-affecting change.
2. Fix public deployed-chat raw JSON result rendering.
3. Fix query continuity for list -> select product -> choose variant -> cart.
4. Continue removing product use of compatibility `/api/app/graph/*` routes.
5. Add browser regression coverage for no-page-navigation surface opening and
   no flicker during auth/surface transitions.
