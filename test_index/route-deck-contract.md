# RouteDeck Contract And Debugger Validation

Date: 2026-05-12

## Scope

Validation for the RouteDeck contract layer, sibling framework packaging path, backend adapter, action validation, Docker dependency wiring, and frontend navigation/debugger widget.

## What To Validate

- RouteDeck manifest validates every node, edge, action, field, policy, and test path.
- Existing entry API response shapes remain compatible while `graph_manifest` and `route_deck_snapshot` are populated from RouteDeck.
- Submitted `selected_action_id` values are validated against the current node before stage handlers run.
- Invalid actions return a recoverable assistant response with visible valid alternatives.
- Sensitive auth/API credential fields are marked sensitive and masked in stage artifacts.
- Anonymous entry keeps Sign In and Create Account visible.
- Signup exposes display name, email, and password steps without losing actions.
- Direct `/w/:workspaceId` anonymous routes keep chat available and expose backend-owned auth actions.
- RouteDeck map opens from the standalone nav widget, not the evidence drawer.
- Focus graph highlights current, incoming, and outgoing nodes.
- Full graph renders a top-to-bottom lane layout, uses a manifest-sized scrollable canvas, avoids node/title/badge overlap, and lists allowed actions below.
- Docker frontend serves the preview build without Vite HMR websocket or host `@fs` path failures.
- SaaStoAgent imports framework primitives from sibling package `routedeck_core`, not an in-project framework folder.
- SaaStoAgent frontend consumes sibling local package `@routedeck/react`.
- Docker builds use named sibling RouteDeck contexts and avoid sending unrelated projects into the build context.
- Standalone RouteDeck minimal example builds and runs outside SaaStoAgent on ports `5190` and `8096`.

## Current Evidence

- `python -m backend.services.route_deck.validate`: passed.
- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- RouteDeck sibling import check: `from routedeck_core import RouteDeckManifest` passed.
- RouteDeck sibling tests: `python -m pytest tests` passed.
- RouteDeck minimal example `npm run type-check`: passed.
- RouteDeck minimal example `npm run build`: passed.
- RouteDeck minimal example Docker build/up: passed.
- Docker rebuild: `docker compose up -d --build backend frontend`: passed.
- Playwright against `http://localhost:3007`: clean default entry, opened `Map`, switched to `Full graph`, confirmed 11 node groups and no console errors.
- Playwright against `http://127.0.0.1:5190`: standalone RouteDeck minimal example rendered the styled debugger.

## How To Run Current Checks

```powershell
python -m backend.services.route_deck.validate
python -m compileall backend
cd frontend
npm run type-check
npm run build
cd ..
docker compose up -d --build backend frontend
cd ..\routedeck
python -m pytest tests
cd examples\minimal-fastapi-react\frontend
npm run type-check
npm run build
cd ..
docker compose up -d --build
```

Add repo-native browser tests for sign in, signup, invalid action recovery, direct workspace auth actions, and RouteDeck map rendering before treating this as automated end-to-end coverage.
