# RouteDeck Contract And Debugger Validation

Date: 2026-07-10

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
- Corpus state/action routes cross the RouteDeck runtime boundary instead of
  calling Corpus graph state/action helpers directly.
- Frontend SaaSAgent context comes from RouteDeck state, while Zustand remains
  UI-local state.
- RouteDeck v2 navigation operations update client navigation state:
  - `route.back`
  - `route.forward`
  - `route.cancel`
  - `route.open_node`
  - `route.switch_surface`
- Learning peer surfaces and detail nodes are projected from AppGraph/RouteDeck.
- Learning approve/reject and instructions save dispatch through AppGraph
  operations.
- SaaStoAgent product UI does not expose RouteDeck-node wording.
- Raw public `/api/routedeck/*` product routes are absent.
- Corpus owner-workbench chat does not rely on Python phrase routing.
- Active-surface selectable entities can be projected into planning context so
  visible list items can be opened through typed legal operations.
- Active Corpus backend code lives under `backend/corpus/`; the retired
  `backend/services/corpus/` package is absent.
- Corpus backend contracts import RouteDeck primitives directly and do not
  export active Entry aliases or persistence models.
- Source-boundary tests protect the current vertical-slice package layout while
  the next refactor moves generic runtime/event work into RouteDeck.

## Current Evidence

Checkpoint evidence from 2026-07-10:

- Python 3.12 `compileall` passed for the moved Corpus package, routes, model
  base, and compatibility RouteDeck catalogs.
- Direct execution of the dependency-free source-boundary suites passed 32
  tests: 29 from `test_corpus_runtime_structure.py` and 3 from
  `test_corpus_surface_structure.py`.
- The prior Mac mini Tailscale smoke documented in the session handoff passed
  backend health, `/api/corpus/state`, container compilation, Entry-boundary
  assertions, and the browser register-to-create-agent flow.
- Full dependency-backed pytest was not rerun locally because the available
  bundled Python lacks the backend dependency set; this limitation is carried
  into the checkpoint rather than represented as a pass.

Historical evidence from earlier sessions, not rerun on 2026-07-10:

- `python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q`: passed, 81 tests.
- `python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q`: passed, 87 tests.
- Manual in-app browser verification against the Docker app confirmed:
  - `list agents`
  - `open Live Commerce 1779760865401`
  - `open learning`
  - `show rejected`
  - `go home`
- `npm run e2e:docker`: passed.
- `npm run e2e:medusa:docker`: passed, checkout completed.
- `python -m pytest backend/tests -q`: passed, 171 tests.
- `npm run type-check` in SaaStoAgent frontend: passed.
- `npm test` in `agent-lab-powered-projects/routedeck/react`: passed, 13
  tests.
- `python -m pytest tests -q` in `agent-lab-powered-projects/routedeck`:
  passed, 17 tests.
- `git diff --check`: passed.
- Boundary scans confirmed no active production matches for direct Learning
  review REST mutation from Corpus UI, direct instructions save REST mutation
  from Corpus UI, raw `/api/routedeck/*` route declarations, product-visible
  RouteDeck-node copy, or product literals in RouteDeck production source.

Earlier debugger evidence:

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
python -m pytest backend/tests/test_corpus_runtime_structure.py backend/tests/test_corpus_surface_structure.py backend/tests/test_routedeck_schema_boundary.py -q
python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q
python -m pytest backend/tests -q
cd ..\routedeck\react
npm test
cd ..\..\saastoagent-v0.1\frontend
npm run type-check
npm run e2e:docker
npm run e2e:medusa:docker
npx tsc -p tsconfig.json
npx vite build --outDir dist_verify
```

## Follow-Up

Add repo-native browser tests for:

- auth surface opening inside the main shell
- inline proposal/surface rendering
- docked diagnostics focus view
- fullscreen diagnostics radial hub map
- browser URL replay and `surface_id` hydration validation
