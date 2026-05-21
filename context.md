# SaaStoAgent v0.1 Context

Last Updated: May 21, 2026 11:07
Project: SaaStoAgent v0.1
Status: The Corpus-centered workbench shell and the shared RouteDeck debugger
pass are implemented and documented. Continue from semantic hub-map grouping,
browser automation, and remaining RouteDeck compatibility cleanup, not from the
rejected sitemap or page-replacing auth-shell assumptions.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Start Here

- Latest checkpoint: `context_checkpoints/context_checkpoint_21-05-2026-11-07AM.md`
- Previous context archived at:
  `context_history/20260521_1107_context_before_corpus_workbench_and_routedeck_debugger_closeout.md`
- Closeout log:
  `logs/20260521_1107_corpus_workbench_and_routedeck_debugger_closeout.md`
- Validated architecture note:
  `architecture/dev_validated_docs/2026-05-21_corpus_workbench_and_routedeck_debugger_validation.md`
- Framework RouteDeck anchor: `../routedeck/docs/agentic-ui-state-runtime.md`
- Product anti-drift vision: `architecture/route-deck-corpus-vision.md`
- Current plan/status: `plans/routedeck_runtime_store_reset_plan.md`

## Current Architecture

RouteDeck is graph-backed state management for agentic UI, and SaaStoAgent now
consumes it through a single Corpus workbench shell.

```text
CorpusGraphRuntime
  -> SaaStoAgent RouteDeck adapter
    -> generic RouteDeckRuntime
      -> RouteDeckStore
        -> AppGraphShell
          -> topbar and rails
          -> Corpus conversation with fixed composer
          -> inline active surfaces
          -> docked or fullscreen diagnostics
```

The core rules are:

- Graph owns truth, guards, and commits.
- RouteDeck owns the generic runtime/store over the graph.
- Corpus is the central SaaStoAgent product agent and consumes RouteDeck state.
- Auth and active surfaces stay inside the single workbench shell.
- Legal operations are not rendered as raw product UI.
- Visible choices are Corpus-authored proposals, initiated surfaces, or
  diagnostics.
- Diagnostics is read-only and exposes graph/runtime internals when opened.
- The focus debugger uses lane-separated routing; the full map uses a
  root-centered radial hub layout around `home`.

## Implemented This Session

- Refined the Corpus workbench shell, including auth/signup/login flow and
  authenticated topbar/surface behavior.
- Tightened the visual system across the shell, surfaces, buttons, fields, and
  composer container.
- Added fullscreen diagnostics and aligned the graph theme with the new shell.
- Added compact lane-separated routing in shared RouteDeck debugger code so
  sibling and opposite-direction edges do not overlap on the same path.
- Replaced the rejected sitemap full-map layout with a root-centered radial hub
  map.
- Added debugger routing/topology tests in `../routedeck/react/tests/`.
- Updated the RouteDeck runtime doc, plan, flow index, test note, architecture
  validation note, and closeout artifacts.

## Verification

- `python -m pytest backend/tests/test_app_graph_contract.py -q`: 16 passed.
- `npm test` in `agent-lab-powered-projects/routedeck/react`: 6 passed.
- SaaStoAgent frontend `npm run type-check`: passed.
- SaaStoAgent frontend `npx tsc -p tsconfig.json && npx vite build --outDir dist_verify`:
  passed.
- Session browser QA showed:
  - signup/login stayed inside the workbench shell
  - diagnostics fullscreen did not break the composer
  - `auth_register <-> home` rendered as separate focus-graph paths
  - the radial hub full map rendered `29` unique routed paths

## Current Cleanup Status

Keep for now:

- Compatibility `/api/app/graph/*` paths remain debt until tests and remaining
  callers are migrated.
- Historical `OperatorGateway` sections in `SYSTEM_FLOW_INDEX.md` remain as
  compatibility notes, with the active status section superseding them.

## Next Concrete Step

Continue from `plans/routedeck_runtime_store_reset_plan.md`:

1. Add semantic branch labels/grouping to the radial hub map.
2. Add repo-native browser coverage for auth surface opening, inline proposal
   widgets, and docked/fullscreen diagnostics.
3. Remove remaining product-path dependence on compatibility `/api/app/graph/*`
   endpoints.
4. Add LLM/meta-tool adapters backed by the same RouteDeck introspection source
   as diagnostics.
5. Keep tightening shell polish without breaking the permanent central-chat
   model.

## Anti-Drift Reminder

If future implementation reintroduces page-replacing auth shells, raw
legal-operation chips, or sitemap assumptions for the full map, stop and return
to `../routedeck/docs/agentic-ui-state-runtime.md`.
