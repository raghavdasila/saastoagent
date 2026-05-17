# 2026-05-16 17:15 - Graph-First App Reset

## Scope

Implemented the first working graph-first reset spine: backend app graph manifest/runtime/endpoints, frontend graph shell/routes, graph contract tests, ADR, plan, context, and test index updates.

## Code Changes

- Added `backend/services/app_graph/manifest.py` with unified RouteDeck node/action registry.
- Added `backend/services/app_graph/runtime.py` with snapshot, turn, and action handling.
- Added `backend/routes/app_graph.py` and mounted it in `backend/main.py`.
- Added `backend/core/schemas/app_graph.py`.
- Added `frontend/src/components/appGraph/AppGraphShell.tsx`.
- Added `frontend/src/types/appGraph.ts`.
- Switched `frontend/src/App.tsx` to `/app/...` graph routes and compatibility graph hydration.

## Validation

- `python -c "from backend.main import app; print('routes', len(app.routes)); from backend.services.app_graph import validate_app_graph_manifest; print(validate_app_graph_manifest())"` - passed.
- `pytest backend/tests/test_app_graph_contract.py backend/tests/test_route_deck_contract.py -q` with `PYTHONPATH=.` - 15 passed.
- `pytest backend/tests -q` with `PYTHONPATH=.` - 40 passed.
- `npm run type-check` - passed.
- `npm run build` - passed.
- Anonymous app graph snapshot smoke returned `home`, renderer `home`, and auth actions.
- Playwright rendered smoke against `npx vite --host 0.0.0.0 --port 3008` with mocked `/api/app/graph/snapshot` - passed; RouteDeck header, context lens, node strip, auth action, and SaaS Agent create form rendered with zero console errors.
- Added the missing central graph chat to `AppGraphShell`. It keeps a transcript, posts free text to `/api/app/graph/turn`, executes exact visible action ids through `/api/app/graph/action`, and stays graph-owned instead of reviving `OperatorGateway`.
- Playwright rendered smoke against Vite plus Docker backend after central chat fix - passed; central chat rendered, user text appeared, `/turn` returned the structured-action fallback, and there were zero console/request failures.

## Remaining

- Final hardcoding purge for legacy operator files and selected-agent snapshot route.
- Graph-native QA scenarios.
- Structured LLM router constrained to RouteDeck ids.
- Optional SSE graph turn stream.
