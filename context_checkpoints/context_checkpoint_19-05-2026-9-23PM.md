# Context Checkpoint - RouteDeck Runtime Store Closeout

Date: 2026-05-19 21:23 +05:30
Project: SaaStoAgent v0.1

## Session Summary

This session corrected RouteDeck's direction from passive projection/debugger infrastructure into graph-backed state management for agentic UI.

The user clarified that RouteDeck should be thought of like Redux/MobX/Zustand for agentic applications, albeit graph/LangGraph-backed. The accepted direction is now:

```text
Graph owns truth.
RouteDeck owns the generic runtime/store over that graph.
Corpus is the SaaStoAgent product agent that consumes RouteDeck.
React renders Corpus plus RouteDeck-projected contextual surfaces.
```

## Main Architecture Outcomes

- RouteDeck is the reusable agentic UI state runtime.
- RouteDeckStore is the frontend state-management interface.
- SaaStoAgent consumes RouteDeck through a product adapter.
- Corpus remains the central SaaStoAgent product agent.
- Corpus streams text/proposals separately from RouteDeck state streams.
- Diagnostics is read-only and powered by graph introspection.
- Legal operations are runtime/agent context, not default product UI.
- Navigation diagnostics draw semantic routes only; actions are not graph edges.

## Files To Read First Next Session

1. `../routedeck/docs/agentic-ui-state-runtime.md`
2. `architecture/route-deck-corpus-vision.md`
3. `plans/routedeck_runtime_store_reset_plan.md`
4. `SYSTEM_FLOW_INDEX.md`
5. `context.md`

## Implemented Code And Docs

- RouteDeck runtime/store contracts in `routedeck_core`.
- RouteDeck React store/provider/hooks and generic HTTP/SSE store.
- SaaStoAgent RouteDeck adapter.
- Corpus endpoint/schema reset.
- App shell rewired around RouteDeckStore.
- Semantic manifest route topology.
- Sitemap-style diagnostics full map.
- RouteDeck and SaaStoAgent anti-drift docs.
- Closeout docs and updated flow index.

## Cleanup Audit

Deletion candidates inside `saastoagent-v0.1` only:

- `.pytest_cache/`
- backend `__pycache__/` folders
- `frontend/dist/`
- `frontend/node_modules/.vite/`

No SaaStoAgent v0.1 source files were identified as deletion targets.

Correction note:

- A root-level `test_targets/` folder and root `.codex-artifacts/` folder were deleted during the first cleanup pass. That was outside the requested SaaStoAgent v0.1 audit scope. `test_targets/` was untracked and must be recreated from its source fixture repos if still needed.

Deferred cleanup:

- Legacy `/api/app/graph/*` compatibility endpoints.
- Historical `OperatorGateway` documentation sections.
- Any tests that still assert compatibility-era graph endpoints.

## Verification Evidence

- RouteDeck tests: `python -m pytest tests -q` -> 14 passed.
- SaaStoAgent graph contract tests: `python -m pytest backend/tests/test_app_graph_contract.py -q` -> 12 passed.
- Frontend type-check: `npm run type-check` -> passed.
- Frontend build: `npm run build` -> passed.
- Browser smoke: Docker frontend `http://localhost:3007/app/home`, Diagnostics -> Full map -> `Showing all 22 nodes and 29 routes`, no console errors.

## Next Work

Continue from `plans/routedeck_runtime_store_reset_plan.md`.

Most important next slice:

1. Add automated browser coverage for the diagnostics full map.
2. Add stream-store tests for `connectStream()`.
3. Add Corpus meta-tool adapters backed by shared introspection.
4. Remove product UI use of `/api/app/graph/*` once tests are migrated.
5. Keep checking RouteDeck framework source for SaaStoAgent/SaaSAgent product leakage.
