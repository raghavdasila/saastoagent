# Context Checkpoint - 2026-05-12 14:47

## State

SaaStoAgent v0.1 has a clean post-RouteDeck entry surface and consumes RouteDeck as a sibling framework package.

RouteDeck now lives at `../routedeck/` with:

- `routedeck_core` Python package
- `@routedeck/react` frontend package
- framework docs and boundary note
- minimal FastAPI/React Docker example
- core contract tests

SaaStoAgent keeps product-specific graph behavior under `backend/services/route_deck/`.

## Runtime And Packaging

- Backend imports RouteDeck primitives from `routedeck_core`.
- Frontend imports debugger UI from `@routedeck/react`.
- SaaStoAgent Docker uses named sibling build contexts for RouteDeck.
- Docker frontend uses `npm install --no-package-lock` to avoid npm local `file:` dependency lock/symlink issues inside the container.
- Standalone RouteDeck example remains separate from SaaStoAgent:
  - frontend `http://127.0.0.1:5190`
  - backend `http://127.0.0.1:8096`
- SaaStoAgent Docker app remains:
  - frontend `http://localhost:3007`
  - backend `http://localhost:8085/api/health`

## UI State

- Default entry no longer shows onboarding/checklist content.
- Default entry no longer opens Platform Overview, Knowledge Sources, or Next Best Action before user interaction.
- Platform overview remains available when explicitly requested.
- Canvas collapse switches to a narrow rail so the chat column regains width.
- Artifact cards use responsive sizing instead of horizontally squished card rows.
- RouteDeck status strip and side map remain the graph navigation/debug surface.

## Validation Evidence

- RouteDeck import check: passed.
- RouteDeck `python -m pytest tests`: passed, 2 tests.
- RouteDeck minimal frontend `npm run type-check`: passed.
- RouteDeck minimal frontend `npm run build`: passed.
- RouteDeck minimal Docker build/up: passed.
- SaaStoAgent `python -m backend.services.route_deck.validate`: passed.
- SaaStoAgent `python -m compileall backend`: passed.
- SaaStoAgent frontend `npm run type-check`: passed.
- SaaStoAgent frontend `npm run build`: passed.
- SaaStoAgent Docker build/up for backend/frontend: passed.
- Playwright smoke against `http://localhost:3007`: clean default page, RouteDeck Full graph with 11 node groups, no console errors.
- Playwright smoke against `http://127.0.0.1:5190`: styled RouteDeck minimal example rendered.

## Known Caveats

- Browser QA is still smoke-level.
- Backend pytest is not yet a reliable full-suite test path.
- Generated REST tools are persisted but not bound into workspace agent execution.
- Direct `/w/:id` deep links can still bypass graph-owned setup until the user explicitly enters setup/auth.
- RouteDeck currently covers entry/auth/setup/workspace handoff; REST execution, approvals, QA, and learnings should adopt it next.

## Resume Path

Next session should begin with REST/OpenAPI upload and generated tool binding:

1. Review `context.md`, `SYSTEM_FLOW_INDEX.md`, and `docs/route-deck/`.
2. Inspect existing REST connection activation and generated action/tool persistence.
3. Implement OpenAPI upload/inspection UX if missing.
4. Bind generated tools into workspace agent execution.
5. Extend RouteDeck snapshots/actions into REST execution, approval, QA, and learning flows.

## References

- Latest log: `logs/20260512_1447_routedeck_sibling_framework_closeout.md`
- Context archive: `context_history/20260512_1447_context_before_routedeck_sibling_closeout.md`
- RouteDeck framework: `../routedeck/`
- RouteDeck ADR: `decisions/ADR-007-routedeck-framework-contract.md`
- RouteDeck test index: `test_index/route-deck-contract.md`
