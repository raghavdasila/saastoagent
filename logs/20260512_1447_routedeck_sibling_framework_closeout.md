# 2026-05-12 14:47 - RouteDeck Sibling Framework Closeout

## Summary

Closed out the RouteDeck sibling-framework extraction, SaaStoAgent integration cleanup, standalone RouteDeck inspection runtime, and post-RouteDeck UI cleanup.

RouteDeck is now a sibling framework project at `agent-lab-powered-projects/routedeck`. SaaStoAgent v0.1 keeps its product-specific adapter/catalog under `backend/services/route_deck/` and consumes RouteDeck through local package boundaries instead of an in-project `routedeck_framework` folder.

## Completed

- Moved reusable RouteDeck framework code into sibling project `../routedeck/`.
- Kept SaaStoAgent product graph behavior in `backend/services/route_deck/`.
- Repointed backend imports from `routedeck_framework.routedeck_core` to `routedeck_core`.
- Added sibling Python dependency through `backend/requirements.txt`.
- Added sibling frontend dependency through `@routedeck/react` in `frontend/package.json`.
- Updated Docker to use named sibling build contexts for RouteDeck.
- Added Docker `.dockerignore` coverage for the sibling framework.
- Kept container frontend installs on `npm install --no-package-lock` to avoid npm local `file:` dependency lock/symlink crashes inside Docker.
- Added RouteDeck framework boundary documentation at `../routedeck/docs/boundary.md`.
- Added RouteDeck core tests in `../routedeck/tests/test_core_contract.py`.
- Kept the standalone RouteDeck minimal FastAPI/React example runnable on:
  - frontend: `http://127.0.0.1:5190`
  - backend: `http://127.0.0.1:8096`
- Preserved the SaaStoAgent default UI cleanup:
  - no default onboarding/checklist artifacts
  - no default Platform Overview or Knowledge Sources on bootstrap
  - no default Next Best Action before interaction
  - cleaner canvas collapse behavior
  - responsive artifact cards instead of horizontal squishing

## Validation

- RouteDeck package import: `from routedeck_core import RouteDeckManifest` passed.
- RouteDeck core tests: `python -m pytest tests` passed with 2 tests.
- RouteDeck minimal frontend:
  - `npm run type-check` passed.
  - `npm run build` passed.
  - `docker compose up -d --build` passed.
- SaaStoAgent backend:
  - `python -m backend.services.route_deck.validate` passed.
  - `python -m compileall backend` passed.
- SaaStoAgent frontend:
  - `npm run type-check` passed.
  - `npm run build` passed.
- SaaStoAgent Docker:
  - `docker compose up -d --build backend frontend` passed.
  - backend started on `8085`.
  - frontend preview served on container port `3000`, host port `3007`.
- Playwright smoke:
  - SaaStoAgent default page at `http://localhost:3007` did not show Platform Overview, Knowledge Sources, onboarding/checklist, or Next Best Action.
  - SaaStoAgent RouteDeck map opened and Full graph rendered 11 node groups with no console errors.
  - RouteDeck minimal example at `http://127.0.0.1:5190` rendered the styled debugger.

## Decisions

- No new ADR was added. ADR-007 remains the RouteDeck decision record and now points at the sibling package shape.
- RouteDeck owns agentic navigation UX contracts and reusable debugging/authoring UI.
- SaaStoAgent owns product graph behavior, auth/workspace semantics, REST setup choices, and adapter/catalog copy.
- The next implementation slice should start with REST/OpenAPI upload, inspection, generated tool binding, and learning loops.

## Known Caveats

- Docker frontend uses `npm install --no-package-lock` inside the container because npm currently crashes on the local `file:` dependency lock/symlink path.
- The checked-in frontend lockfile remains valid for normal host installs/builds.
- RouteDeck browser coverage is still smoke-level; repo-native frontend tests are still needed.
- Backend pytest is still not wired as a reliable full-suite local/container test path.
- `test_targets/` exists outside this work and remains untouched.

## Next Session

Start with generated REST/OpenAPI upload and binding:

1. Upload or ingest an OpenAPI/Swagger spec into a workspace connection.
2. Inspect and normalize generated actions/tools.
3. Bind generated tools into workspace agent selection/execution.
4. Add approval/QA/learning surfaces using the RouteDeck contract instead of inventing a separate navigation model.

## Updated Documentation

- `context.md`
- `context_history/20260512_1447_context_before_routedeck_sibling_closeout.md`
- `context_checkpoints/context_checkpoint_12-05-2026-2-47PM.md`
- `SYSTEM_FLOW_INDEX.md`
- `logs/README.md`
- `context_checkpoints/README.md`
- `context_history/README.md`
- `decisions/README.md`
- `test_index/README.md`
- `test_index/route-deck-contract.md`
