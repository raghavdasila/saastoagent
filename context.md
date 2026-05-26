# SaaStoAgent v0.1 Context

Last Updated: May 26, 2026 08:56 AM IST
Project: SaaStoAgent v0.1
Status: RouteDeck/Corpus hardcoding removal is implemented and live-verified. Corpus now plans from structured RouteDeck context instead of Python phrase routing. Owner-workbench chat navigation and deployed-agent Medusa checkout both passed current Docker/browser validation.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Start Here

- Latest checkpoint: `context_checkpoints/context_checkpoint_26-05-2026-08-56AM.md`
- Previous context archived at:
  `context_history/20260526_0856_context_before_hardcoding_removal_closeout.md`
- Closeout log:
  `logs/20260526_0856_routedeck_corpus_hardcoding_removal_closeout.md`
- Active implementation plan:
  `docs/superpowers/plans/2026-05-26-routedeck-corpus-hardcoding-removal.md`
- RouteDeck human/agent/developer guide:
  `../routedeck/docs/using-routedeck.md`
- RouteDeck framework anchor:
  `../routedeck/docs/agentic-ui-state-runtime.md`
- Boundary ADR:
  `decisions/ADR-013-routedeck-corpus-boundary.md`
- System flow source of truth:
  `SYSTEM_FLOW_INDEX.md`
- RouteDeck test index:
  `test_index/route-deck-contract.md`

## Current Worktree Warning

The worktree is not clean. Do not assume the current repo state is committed.

Before continuing:

```powershell
git status --short
git diff --stat -- agent-lab-powered-projects/saastoagent-v0.1 agent-lab-powered-projects/routedeck
```

There are still broad uncommitted changes in:

- `agent-lab-powered-projects/saastoagent-v0.1`
- `agent-lab-powered-projects/routedeck`
- `research/openapi_toolrouter_training_lab`

Treat the research work as separate from the SaaStoAgent product runtime slice.

## What Changed This Session

### Hardcoding Removed

- Deleted the backend heuristic chat router from `backend/services/app_graph/runtime.py`.
- Corpus owner-workbench chat now follows one path:

```text
AppGraph state
  -> RouteDeck projection
    -> Corpus planning_context
      -> model chooses typed legal op or clarify
        -> runtime validates payload against current projection
          -> graph commits
```

- No phrase tables, alias tables, or compatibility heuristic fallbacks were left in place for owner-workbench navigation.

### Structured Planner Context Added

- Added `backend/services/app_graph/corpus_turn_planning.py`.
- Planner context now exposes:
  - current node and active surface
  - active SaaS Agent summary
  - active surfaces
  - visible selectable entities on the active surface
  - legal operations
  - blocked operations

### Surface-Declared Selectable Entities

- `SaaSAgentListSurface` now projects visible selectable SaaS Agent entities into planning context.
- This lets chat open a listed SaaS Agent by choosing the exact typed `saas_agent.open` payload from current RouteDeck-visible state instead of asking for a hidden internal id.

### RouteDeck/Corpus Navigation Behavior

- App-local proposal/review routing remains removed.
- Review/input work stays graph-owned.
- Route validation still constrains `route.open_node`, `route.switch_surface`, `route.back`, `route.forward`, and `route.cancel`.
- Learning peer surfaces remain generic `route.switch_surface` targets, with Corpus-owned descriptions to help model selection.

## Current Validation

Latest current-worktree verification:

- `python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q`
  - Result: `81 passed`
- `python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q`
  - Result: `87 passed`
- `npm run type-check` from `frontend`
  - Result: passed
- `docker compose up -d --build backend`
  - Result: passed
- `npm run e2e:docker` from `frontend`
  - Result: passed
  - Artifacts: `C:\Users\ragha\AppData\Local\Temp\saastoagent-ui-e2e-1779761987528`
- `npm run e2e:medusa:docker` from `frontend`
  - Result: passed
  - Checkout: completed
  - Artifacts: `C:\Users\ragha\AppData\Local\Temp\saastoagent-medusa-ui-e2e-1779762026718`
- Manual in-app browser verification:
  - `list agents`
  - `open Live Commerce 1779760865401`
  - `open learning`
  - `show rejected`
  - `go home`
- `git diff --check`
  - Result: no diff errors; CRLF warnings only

## Known Debt To Carry Forward

### Browser URL Replay Boundary Debt

A sidecar audit found remaining boundary debt around browser-driven navigation replay:

- frontend popstate handling still assembles a `route.open_node` payload
- snapshot/load still accepts browser-provided `surface_id` too permissively
- `route.open_node` planner schema is still not the cleanest possible expression of legal surface/node combinations

These issues did not break the verified chat flows, but they are the next architectural cleanup target.

### Worktree Scope Is Still Broad

The current diff includes earlier RouteDeck and app-graph work beyond this closeout. Inspect carefully before committing or reshaping the branch.

## Next Concrete Step

Clean up the remaining browser URL replay boundary debt before expanding more features.

Start with:

1. `frontend/src/components/appGraph/AppGraphShell.tsx`
   - remove frontend-authored `route.open_node` replay where possible
2. `backend/routes/corpus_graph.py`
   - tighten snapshot/load handling for requested `surface_id`
3. `backend/services/app_graph/runtime.py`
   - make replay/navigation location validation stricter and more declarative

After that, rerun:

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q
cd frontend
npm run e2e:docker
npm run e2e:medusa:docker
```

## Anti-Drift Reminder

- RouteDeck exposes current legal context; Corpus decides; AppGraph validates and commits.
- RouteDeck shared code stays product-neutral.
- Corpus must not reintroduce phrase routing, alias tables, or hidden nav heuristics.
- Public deployed chat must not expose internal resource ids, endpoint paths, trace ids, operation ids, approval ids, or raw tool labels.
- Medusa remains an acceptance fixture only.
