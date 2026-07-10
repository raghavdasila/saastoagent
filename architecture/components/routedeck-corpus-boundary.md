# RouteDeck and Corpus Boundary

## Purpose

This component owns the owner-workbench boundary between the Corpus product
definition and the RouteDeck framework: product declarations and handlers,
RouteDeck projection, Corpus planning context, typed operation dispatch,
diagnostics, and validation before commit.

The durable rule is:

```text
RouteDeck exposes.
Corpus decides.
Runtime validates and commits.
Product UI renders product language.
Diagnostics expose internals read-only.
```

## Owner Files

- `backend/corpus/schemas/*.py`
- `backend/corpus/graph/definitions.py`
- `backend/corpus/graph/app.py`
- `backend/routes/corpus_graph.py`
- `backend/services/route_deck/*.py`
- `frontend/src/components/corpus/*.tsx`
- `frontend/src/components/corpus/*.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/types/appGraph.ts`
- `frontend/src/types/corpus.ts`

## Public Interfaces

- `GET /api/corpus/state`
- `POST /api/corpus/action`
- `GET /api/corpus/stream`
- `GET /api/diagnostics/stream`
- Browser route state under `/app/*`
- Browser query key `surface_id`

## Dependent Flows

- Owner workbench chat and click actions.
- Product quick actions and projected surface controls.
- RouteDeck diagnostics and debugger views.
- Browser location replay into validated graph state.
- Learning, review, and instructions-save product surfaces.
- Migration toward the RouteDeck Full Flow compiler and shared event/SSE
  architecture.

## Tests And Evidence

- `backend/tests/test_app_graph_contract.py`
- `backend/tests/test_corpus_graph_contract.py`
- `backend/tests/test_corpus_routedeck_runtime.py`
- `backend/tests/test_corpus_routedeck_state.py`
- `backend/tests/test_corpus_turn_planning.py`
- `backend/tests/test_corpus_runtime_structure.py`
- `backend/tests/test_corpus_surface_structure.py`
- `backend/tests/test_routedeck_schema_boundary.py`
- `test_index/route-deck-contract.md`
- `npm run type-check`
- `npm run e2e:docker`
- `npm run e2e:medusa:docker`

## Update Triggers

Update this component doc and `architecture/code-map.md` when changing:

- RouteDeck projection shape or readiness metadata.
- Corpus planning context, operation selection, or clarification rules.
- Hidden/internal route operation filtering.
- `surface_id` handling.
- `/api/corpus/*` or diagnostics endpoint behavior.
- Frontend dispatch path for projected operations.
- Corpus package ownership, pass-through RouteDeck wrappers, or legacy Entry
  contracts.

Also update `decisions/ADR-013-routedeck-corpus-boundary.md` if the boundary
rule itself changes.
