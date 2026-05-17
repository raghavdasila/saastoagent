# 2026-05-16 18:26 - Agent-First RouteDeck Reset

## Goal

Make the graph-first implementation match the product vision: chat-first SaaS Agent desk, RouteDeck as invisible infrastructure, and graph internals available only for diagnostics.

## Changes

- Replaced the product-facing graph/debugger shell with a central Agent desk conversation.
- Rendered backend-provided next steps as natural labels/forms instead of asking users to type internal action ids.
- Moved RouteDeck graph metadata, node ids, reachable nodes, valid action ids, evidence, and diagnostics into a closed Diagnostics panel.
- Added an app-owned turn router adapter with disabled/OpenAI/Ollama provider modes.
- Kept RouteDeck deterministic and model-free; provider config belongs to SaaStoAgent settings.
- Changed `/api/app/graph/turn` so no-model mode asks for a natural clarification and never executes text without validated structured action output.
- Added Medusa Storefront/Admin/Custom API target choices to connection activation.
- Added guardrails in `backend/tests/test_app_graph_contract.py`.

## Follow-up Correction

- Fixed disabled-router clarification handling so a greeting like `hi` no longer becomes an unavailable-action message.
- Removed the empty anonymous Home work surface below the chat; Home is now the opening state inside the Agent desk when there are no visible SaaS Agents.
- Mapped raw work labels such as `Home` to user-facing context like `Starting a SaaS Agent`.

## Validation

- `$env:PYTHONPATH='.'; pytest backend/tests/test_app_graph_contract.py -q`: 8 passed.
- `$env:PYTHONPATH='.'; pytest backend/tests -q`: 44 passed.
- `python -m backend.services.route_deck.validate`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Playwright smoke against `http://localhost:3010/app/home`: passed. It verified Agent desk rendering, Working On context, clean post-turn copy after sending `hi`, RouteDeck internals hidden until Diagnostics is opened, and zero console/request failures.
- Follow-up Playwright smoke against `http://localhost:3010/app/home`: passed. It verified a natural `hi` response, no `not available from here` copy, no empty `Your SaaS Agents` block on anonymous Home, user-facing `Starting a SaaS Agent` context, and zero console/request failures.

## Pending

- Graph-authored QA migration.
- Legacy compatibility purge.
