# Context Checkpoint - Corpus Workbench And RouteDeck Debugger

Date: 2026-05-21 11:07 +05:30
Project: SaaStoAgent v0.1

## Session Summary

This session carried the RouteDeck runtime-store reset through the product shell
and the shared debugger.

The accepted shape is now:

```text
Graph owns truth.
RouteDeck owns the generic runtime/store over that graph.
Corpus consumes RouteDeck state inside one permanent workbench shell.
React renders Corpus plus RouteDeck-projected inline surfaces and read-only diagnostics.
```

## Main Architecture Outcomes

- Corpus remains the central SaaStoAgent interaction spine.
- The main composer stays anchored at the bottom of the workbench.
- Auth/signup/login now remain inside the single shell instead of opening a
  second chat shell or page-like auth layout.
- RouteDeck diagnostics can render docked or fullscreen without changing their
  runtime source.
- Focus diagnostics now use compact lane-separated routing to avoid overlapping
  sibling and opposite-direction edges.
- Full-map diagnostics now use a root-centered radial hub layout around `home`
  rather than the rejected sitemap pass.
- The RouteDeck canonical doc now reflects that debugger behavior.

## Files To Read First Next Session

1. `context.md`
2. `architecture/dev_validated_docs/2026-05-21_corpus_workbench_and_routedeck_debugger_validation.md`
3. `../routedeck/docs/agentic-ui-state-runtime.md`
4. `plans/routedeck_runtime_store_reset_plan.md`
5. `frontend/src/components/appGraph/AppGraphShell.tsx`
6. `../routedeck/react/src/RouteDeckDebugger.tsx`

## Implemented Code And Docs

- Corpus workbench shell refinements across the SaaStoAgent frontend.
- Auth and inline-surface flow cleanup inside the main shell.
- Diagnostics fullscreen support and debugger theming updates.
- RouteDeck debugger routing helper extraction for lane-separated focus edges.
- RouteDeck debugger topology helper extraction for the radial hub full map.
- RouteDeck debugger tests for routing and topology behavior.
- Updated SaaStoAgent context, plan, flow index, architecture notes, and test
  index entries.
- Updated RouteDeck canonical runtime documentation.

## Fresh Verification Evidence

- Backend graph contract: `python -m pytest backend/tests/test_app_graph_contract.py -q`
  -> 16 passed.
- RouteDeck React tests: `npm test` in `../routedeck/react` -> 6 passed.
- Frontend type-check: `npm run type-check` in `frontend` -> passed.
- Frontend build: `npx tsc -p tsconfig.json && npx vite build --outDir dist_verify`
  in `frontend` -> passed.

## Browser Evidence From This Session

- Signup/login stayed inside the workbench shell and no second chat shell was
  used.
- Diagnostics fullscreen kept the composer working.
- Focus graph kept `auth_register` and `home` edges visually separate.
- Full map rendered as a hub map centered on `home`, with outward branch
  expansion and `29` unique routed paths.

## Deferred Work

- Add semantic capability labels and clearer branch grouping to the radial hub
  map.
- Add repo-native browser automation for auth, inline surfaces, and diagnostics.
- Remove remaining compatibility `/api/app/graph/*` product usage.
- Add RouteDeck introspection-backed meta-tool adapters for Corpus.

## Notes

- No new ADR was added. The architecture shift fits inside the existing
  RouteDeck runtime-store and RouteDeck/Corpus anti-drift docs.
- Build verification continues to use `dist_verify` while the normal `dist`
  output path is locked on Windows.
