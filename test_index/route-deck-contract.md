# RouteDeck Contract And Debugger Validation

Date: 2026-05-21

## Scope

Validation for the RouteDeck contract layer, sibling framework packaging,
graph-owned legality, and the current shared debugger behavior used by
SaaStoAgent diagnostics.

## What To Validate

- RouteDeck manifest/runtime legality remains authoritative over graph
  transitions.
- Existing SaaStoAgent graph contract tests continue to pass after the shell and
  debugger work.
- SaaStoAgent frontend still consumes sibling local package `@routedeck/react`.
- Focus diagnostics use deterministic lane-separated routing:
  - multiple incoming edges do not collapse into one path
  - multiple outgoing edges do not collapse into one path
  - opposite-direction node pairs do not reuse the same geometry
- Full-map diagnostics use a root-centered radial hub topology around `home`
  when present.
- Docked and fullscreen diagnostics render the same shared debugger behavior.
- Navigation canvases stay topology-only; actions/details remain outside the
  canvas until a node/operation is inspected.

## Current Evidence

- `python -m pytest backend/tests/test_app_graph_contract.py -q`: passed, 16
  tests.
- `npm test` in `agent-lab-powered-projects/routedeck/react`: passed, 6 tests.
- `npm run type-check` in SaaStoAgent frontend: passed.
- `npx tsc -p tsconfig.json && npx vite build --outDir dist_verify` in
  SaaStoAgent frontend: passed.
- Session browser QA against the local app confirmed:
  - diagnostics fullscreen opened and remained usable
  - focus view rendered separate `auth_register <-> home` paths
  - full map rendered a root-centered hub layout
  - `29` painted edges resolved to `29` unique routed paths

## How To Run Current Checks

```powershell
python -m pytest backend/tests/test_app_graph_contract.py -q
cd ..\routedeck\react
npm test
cd ..\..\saastoagent-v0.1\frontend
npm run type-check
npx tsc -p tsconfig.json
npx vite build --outDir dist_verify
```

## Follow-Up

Add repo-native browser tests for:

- auth surface opening inside the main shell
- inline proposal/surface rendering
- docked diagnostics focus view
- fullscreen diagnostics radial hub map
