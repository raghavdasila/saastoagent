# Graph-First App Contract Validation

Date: 2026-05-16

## May 17 Architecture Gap

The tests in this file verify graph/RouteDeck plumbing, but they do not yet
prove alignment with the target agentic UX. Passing tests must not be treated as
product acceptance.

Missing guardrails to add next:

- forms do not render solely because an action is eligible
- visible next steps come from `proposals`, not raw `available_actions`
- generic chat turns answer conversationally and do not repeat menus
- `/turn` returns an agent-turn contract with message, capabilities, proposals,
  optional active surface, evidence, and diagnostics
- diagnostics may expose graph/RouteDeck internals; product UI may not

## Contract Under Test

The unified app graph is the source of truth for navigation and capability eligibility. The frontend renders backend snapshots and submits backend-provided actions; it does not own workflow transitions. RouteDeck internals must remain hidden from the product UI unless diagnostics are explicitly opened.

## Backend Gates

- `backend/services/app_graph/manifest.py` defines the node/action manifest.
- Every manifest node has a graph handler entry in `NODE_HANDLERS`.
- Every graph action has a typed id and declared scope.
- Every action target resolves to a known graph node.
- Free-text turns use the app-owned structured router adapter.
- No-model router mode asks a natural clarification and does not execute text.
- Router decisions cannot execute without current action eligibility and required fields.
- RouteDeck core remains deterministic and model-free.

Automated check:

- `pytest backend/tests/test_app_graph_contract.py -q`

## Frontend Gates

- `/app/home`, `/app/:nodeId`, `/app/agents/:saasAgentId`, and `/app/agents/:saasAgentId/:nodeId` mount `AppGraphShell`.
- Compatibility routes hydrate graph routes.
- The action dock renders `available_actions` from the backend graph response.
- Persistent actions render as natural next steps from the backend graph response.
- The context lens renders `context_lens` from the backend graph response.
- Product-visible shell copy must not expose RouteDeck, typed action ids, node chips, or reachable-node chips.
- RouteDeck internals may appear only inside the Diagnostics disclosure.

Automated checks:

- `npm run type-check`
- `npm run build`

## Current Verification

- `$env:PYTHONPATH='.'; pytest backend/tests/test_app_graph_contract.py -q`: 8 passed.
- `$env:PYTHONPATH='.'; pytest backend/tests -q`: 44 passed.
- `python -m backend.services.route_deck.validate`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Playwright smoke against `http://localhost:3010/app/home`: passed; Agent desk rendered, Working On context rendered, user text stayed free of internal graph/RouteDeck/action-id copy, Diagnostics exposed RouteDeck internals only after opening, and console/request failures were zero.
- Follow-up Playwright smoke against `http://localhost:3010/app/home`: passed; `hi` returned a natural assistant response, the unavailable-action fallback did not appear, anonymous Home did not render an empty SaaS Agent list, and context showed `Starting a SaaS Agent`.
- `pytest backend/tests/test_app_graph_contract.py backend/tests/test_route_deck_contract.py -q`: 15 passed.
- `pytest backend/tests -q`: 40 passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Playwright rendered smoke against `http://localhost:3008/app/home` with mocked graph snapshot/action API: passed; graph header, context lens, node strip, action button, and SaaS Agent create form rendered with zero console errors.
- Playwright rendered smoke against Vite plus Docker backend after restoring central graph chat: passed; `app-graph-chat` rendered, user text posted through the composer, `/api/app/graph/turn` returned the graph-owned structured-action fallback, and there were zero console/request failures.

## Residual Risk

- Legacy files still exist for compatibility and renderer reuse. The current app routes no longer mount `OperatorGateway`, but the final purge should delete or rewrite stale local capability surfaces after graph-native replacements exist.
