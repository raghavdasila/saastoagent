# Corpus Workbench And RouteDeck Debugger Closeout

Date: 2026-05-21 11:07 +05:30

## What Changed

This session turned the RouteDeck runtime-store foundation into a much cleaner
Corpus-centered workbench and finished a substantial debugger follow-through in
the shared RouteDeck layer.

Key product changes:

- Kept the Corpus composer anchored at the bottom of the shell instead of
  letting auth and active surfaces open a second chat shell.
- Smoothed auth/signup/login surface handling so surface opening stays inside
  the main workbench flow.
- Tightened the workbench visual system: warmer light mode, darker neutral dark
  mode, smaller radii, clearer surface cards, and a transparent composer band.
- Added a fullscreen diagnostics mode that reuses the same RouteDeck debugger as
  the docked rail.

Key RouteDeck debugger changes:

- Added compact lane-separated focus-graph routing so sibling and
  opposite-direction edges do not collapse into the same geometry.
- Rejected the interim sitemap full-map layout after QA and replaced it with a
  root-centered radial hub map around `home`.
- Kept the debugger read-only and shared between docked and fullscreen
  diagnostics surfaces.

Documentation changes:

- Rewrote the live `context.md` snapshot and added a new checkpoint/archive/log.
- Updated the active RouteDeck runtime-store plan and `SYSTEM_FLOW_INDEX.md`.
- Updated the RouteDeck contract test note and added a validated architecture
  note for the workbench/debugger pass.
- Updated the canonical RouteDeck runtime doc so it now describes lane-separated
  focus routing and a radial hub full map instead of a sitemap.

## Decisions Made

- Fullscreen diagnostics should explain topology through a root-centered hub map,
  not a sitemap.
- Focused debugger routing should stay compact and curved; the accepted fix is
  per-node lane separation, not large orthogonal elbows.
- RouteDeck remains product-neutral. SaaStoAgent owns shell labels, auth copy,
  and workbench composition, while the debugger behavior lives in shared
  `@routedeck/react`.

## Issues Encountered

- The sitemap pass made the full graph harder to read because the actual product
  topology is hub-driven around `home`, not page-hierarchy driven.
- Windows kept a lock on `frontend/dist/favicon.svg`, so build verification
  continued through `dist_verify` to avoid mutating the locked output path.

## Fresh Verification

- `python -m pytest backend/tests/test_app_graph_contract.py -q`: passed, 16
  tests.
- `npm test` in `agent-lab-powered-projects/routedeck/react`: passed, 6 tests.
- `npm run type-check` in `agent-lab-powered-projects/saastoagent-v0.1/frontend`:
  passed.
- `npx tsc -p tsconfig.json && npx vite build --outDir dist_verify` in
  `agent-lab-powered-projects/saastoagent-v0.1/frontend`: passed.

## Session Browser Evidence

- Diagnostics fullscreen opened without breaking the main composer.
- Focus view showed separate `auth_register <-> home` edge geometry instead of a
  single overlapping arc.
- Full map rendered the radial hub copy and kept `29` painted edges as `29`
  unique routed paths.

## Handoff

Next session should start from:

- `context.md`
- `context_checkpoints/context_checkpoint_21-05-2026-11-07AM.md`
- `architecture/dev_validated_docs/2026-05-21_corpus_workbench_and_routedeck_debugger_validation.md`
- `../routedeck/docs/agentic-ui-state-runtime.md`
- `plans/routedeck_runtime_store_reset_plan.md`

## Next Steps

1. Add semantic branch labels/grouping to the radial hub map so clusters read
   as product capabilities instead of only geometry.
2. Add repo-native browser coverage for auth surface opening, inline proposal
   widgets, and docked/fullscreen diagnostics.
3. Continue purging compatibility `/api/app/graph/*` product-path usage once the
   remaining callers and tests are migrated.
4. Add introspection-backed Corpus/LLM meta tools over the same RouteDeck
   diagnostics source.
