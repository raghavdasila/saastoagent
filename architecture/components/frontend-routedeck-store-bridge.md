# Frontend RouteDeck Store Bridge

## Purpose

This component owns the frontend bridge between RouteDeck/Corpus backend state
and React product UI. It keeps graph/runtime state projected through typed
contracts while local stores remain limited to display state, drafts, and UI
preferences.

## Owner Files

- `frontend/src/components/appGraph/*.tsx`
- `frontend/src/components/appGraph/*.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/stores/saasAgentUiStore.ts`
- `frontend/src/stores/authStore.ts`
- `frontend/src/stores/themeStore.ts`
- `frontend/src/types/appGraph.ts`
- `frontend/src/types/corpus.ts`
- `frontend/src/types/domain.ts`

## Public Interfaces

- `api.withSaaSAgent(...)`
- Corpus state/action API calls.
- RouteDeck projection rendering.
- Product quick-action and surface dispatch.
- Diagnostics panel props and interactions.
- Zustand stores for local UI state only.

## Dependent Flows

- Owner workbench surface rendering.
- Product quick actions and selected entity actions.
- Chat/click convergence on typed operation dispatch.
- Diagnostics dock/fullscreen rendering.
- `surface_id` hydration and navigation replay.

## Tests And Evidence

- `test_index/route-deck-contract.md`
- `frontend/scripts/e2e-docker.mjs`
- `frontend/scripts/e2e-medusa-docker.mjs`
- `npm run type-check`

## Update Triggers

Update this component doc and the code map when changing:

- Frontend API client request shape.
- RouteDeck/Corpus TypeScript contracts.
- Quick-action filtering or dispatch.
- Diagnostics rendering.
- Local store responsibilities.
- Browser URL or `surface_id` handling.
