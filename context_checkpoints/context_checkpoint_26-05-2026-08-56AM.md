# Context Checkpoint - 26 May 2026 08:56 AM IST

## Current State

This checkpoint supersedes `context_checkpoint_25-05-2026-08-01AM.md`.

The hardcoding-removal slice is implemented and validated on the current
worktree.

Current owner-workbench chat navigation is now based on:

```text
AppGraph state
  -> RouteDeck projection
    -> Corpus planning_context
      -> model chooses typed legal op
        -> runtime validates against current projection
          -> graph commits
```

No Python phrase-routing fallback remains in the owner-workbench runtime path.

## Main Runtime Changes

- Added `backend/services/app_graph/corpus_turn_planning.py`.
- Planner context now exposes current location, active surfaces, legal
  operations, blocked operations, and visible selectable entities.
- `SaaSAgentListSurface` now projects visible selectable entities for planner
  use.
- Corpus router/stream prompts were tightened so surface opens/switches do not
  ask for redundant confirmation.
- Learning peer surfaces gained explicit planning descriptions for model
  selection.

## Validation

Latest current-worktree validation:

- `python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q`
  - `81 passed`
- `python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q`
  - `87 passed`
- `npm run type-check` from `frontend`
  - passed
- `docker compose up -d --build backend`
  - passed
- `npm run e2e:docker` from `frontend`
  - passed
- `npm run e2e:medusa:docker` from `frontend`
  - passed
  - checkout completed
- manual in-app browser verification:
  - `list agents`
  - `open Live Commerce 1779760865401`
  - `open learning`
  - `show rejected`
  - `go home`
- `git diff --check`
  - no diff errors; CRLF warnings only

## Known Debt

- frontend popstate/browser replay still constructs a `route.open_node` payload
- snapshot/load still accepts browser-provided `surface_id` too loosely
- `route.open_node` planner schema can still be more faithful to legal
  node/surface combinations
- worktree remains broad and not clean

## Next Step

Tighten browser URL replay and snapshot surface validation without weakening
the RouteDeck/Corpus boundary:

1. reduce frontend-authored navigation replay in
   `frontend/src/components/appGraph/AppGraphShell.tsx`
2. validate requested `surface_id` more strictly in snapshot/load handling
3. rerun:

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q
cd frontend
npm run e2e:docker
npm run e2e:medusa:docker
```
