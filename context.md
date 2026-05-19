# SaaStoAgent v0.1 Context

Last Updated: May 19, 2026 21:23
Project: SaaStoAgent v0.1
Status: RouteDeck runtime-store foundation implemented; continue from the RouteDeck/Corpus anti-drift docs, not the older action-router shell assumptions.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Start Here

- Latest checkpoint: `context_checkpoints/context_checkpoint_19-05-2026-9-23PM.md`
- Previous context archived at: `context_history/20260519_2123_context_before_routedeck_runtime_store_closeout.md`
- Closeout log: `logs/20260519_2123_routedeck_runtime_store_closeout.md`
- Framework RouteDeck anchor: `../routedeck/docs/agentic-ui-state-runtime.md`
- Product anti-drift vision: `architecture/route-deck-corpus-vision.md`
- Current plan/status: `plans/routedeck_runtime_store_reset_plan.md`

## Current Architecture

RouteDeck is graph-backed state management for agentic UI.

```text
CorpusGraphRuntime
  -> SaaStoAgent RouteDeck adapter
    -> generic RouteDeckRuntime
      -> RouteDeckStore
        -> AppGraphShell
          -> Corpus chat
          -> contextual surfaces
          -> read-only diagnostics
```

The core rules are:

- Graph owns truth, guards, and commits.
- RouteDeck owns the generic runtime/store over the graph.
- Corpus is the central SaaStoAgent product agent and consumes RouteDeck state.
- Corpus can choose typed legal operations and allowed surface variants.
- Legal operations are not rendered as raw product UI.
- Visible choices are Corpus-authored proposals, initiated surfaces, or diagnostics.
- Diagnostics is read-only and exposes graph/runtime internals when opened.

## Implemented This Session

- Added RouteDeck runtime/store contracts and frontend store hooks.
- Added a generic HTTP/SSE RouteDeck store factory.
- Added SaaStoAgent RouteDeck adapter around `CorpusGraphRuntime`.
- Rewired `AppGraphShell` to use a configured RouteDeck store.
- Split Corpus chat/proposal streaming from RouteDeck projection/state streaming.
- Added richer diagnostics and graph introspection surfaces.
- Changed the full diagnostics nav map to a sitemap/star layout.
- Changed the manifest graph to semantic navigation routes instead of action edges.
- Removed raw legal-operation chips from the product shell.
- Fixed transition jitter by avoiding full route remounts on graph state transitions.
- Cleanup audit was started, then corrected to stay scoped inside `saastoagent-v0.1`.

## Verification

- `python -m pytest tests -q` in `agent-lab-powered-projects/routedeck`: 14 passed.
- `python -m pytest backend/tests/test_app_graph_contract.py -q`: 12 passed.
- SaaStoAgent frontend `npm run type-check`: passed.
- SaaStoAgent frontend `npm run build`: passed.
- Browser smoke on Docker frontend `http://localhost:3007/app/home`: diagnostics full map showed `22` nodes and `29` routes, no console errors, and no action controls on the nav canvas.

## Current Cleanup Audit

Deletion candidates inside `saastoagent-v0.1` only:

- `.pytest_cache/`
- backend `__pycache__/` folders
- `frontend/dist/`
- `frontend/node_modules/.vite/`

No SaaStoAgent v0.1 source files were identified as deletion targets.

Correction note:

- A root-level `test_targets/` folder and root `.codex-artifacts/` folder were deleted during the first cleanup pass. That was outside the requested SaaStoAgent v0.1 audit scope. `test_targets/` was untracked and must be recreated from its source fixture repos if still needed.

Keep for now:

- Legacy `/api/app/graph/*` code remains compatibility debt because tests and older code may still reference it.
- Older `OperatorGateway` sections in `SYSTEM_FLOW_INDEX.md` remain historical compatibility documentation, but the active status section now points to the RouteDeck runtime-store model.

## Next Concrete Step

Continue the purge from `plans/routedeck_runtime_store_reset_plan.md`:

1. Remove remaining product UI dependence on compatibility `/api/app/graph/*` paths.
2. Add focused browser tests for diagnostics full map and selected-node actions.
3. Add LLM meta-tool adapters backed by the same introspection service as diagnostics.
4. Tighten tests around `frame`, `active`, and `diagnostic` surface roles.
5. Continue product-literal guard coverage for RouteDeck framework source.

## Anti-Drift Reminder

If future implementation makes RouteDeck feel like only a projection DTO or hides RouteDeck state management inside Corpus, stop and return to `../routedeck/docs/agentic-ui-state-runtime.md`.
