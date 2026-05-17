# Context Checkpoint - 16-05-2026 6:26 PM

## Slice

Agent-first RouteDeck reset after the graph-first shell exposed internal graph/RouteDeck language in the product UI.

## Implemented

- Rebuilt `frontend/src/components/appGraph/AppGraphShell.tsx` as a chat-first Agent desk.
- Removed visible product copy for RouteDeck, typed action ids, central graph chat, node chips, and reachability chips.
- Kept RouteDeck graph/version/action/evidence details behind an explicit Diagnostics disclosure.
- Added `backend/services/app_graph/router.py` as an app-owned structured router adapter.
- Added settings for disabled/OpenAI/Ollama router providers without giving RouteDeck its own key.
- Updated `/api/app/graph/turn` to ask natural clarifications by default and execute only validated structured action decisions.
- Added Medusa Storefront, Medusa Admin, and Custom API as visible API target options for connection activation.
- Added app graph guardrail tests for router behavior, required slots, Medusa options, and hidden product copy.

## Validation So Far

- `$env:PYTHONPATH='.'; pytest backend/tests/test_app_graph_contract.py -q`: 8 passed.
- `npm run type-check`: passed.
- `$env:PYTHONPATH='.'; pytest backend/tests -q`: 44 passed.
- `python -m backend.services.route_deck.validate`: passed.
- `npm run build`: passed.
- Playwright smoke against `http://localhost:3010/app/home`: passed with no visible internal graph/RouteDeck copy before diagnostics and no console/request failures.
- Follow-up Playwright smoke against `http://localhost:3010/app/home`: passed with natural `hi` response, no unavailable-action copy, no empty anonymous Home list, user-facing starting context, and no console/request failures.

## Next

- Finish graph-authored QA migration and legacy OperatorGateway purge in the next slice.
