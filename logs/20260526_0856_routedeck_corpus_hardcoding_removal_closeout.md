# 2026-05-26 08:56 IST - RouteDeck Corpus Hardcoding Removal Closeout

## Scope

This session implemented the accepted hardcoding-removal slice for the
RouteDeck/Corpus boundary and then revalidated both owner-workbench navigation
and deployed-agent checkout from the live Docker app.

The work focused on:

- deleting Python phrase routing from Corpus owner-workbench chat
- restoring model-planned typed-operation selection from RouteDeck context
- keeping RouteDeck product-neutral
- proving the result in browser-driven black-box flows

## What Changed

### Deleted heuristic chat routing

- Removed the deterministic/heuristic router path from:
  - `backend/services/app_graph/runtime.py`
- Deleted the phrase-matching helper family rather than leaving compatibility
  branches or fallback tables.

### Added structured Corpus planning context

- Added:
  - `backend/services/app_graph/corpus_turn_planning.py`
- `planning_context` now exposes:
  - current node and active surface
  - active SaaS Agent summary
  - active surfaces
  - visible selectable entities on the current surface
  - legal operations
  - blocked operations

### Added surface-declared selectable entities

- `SaaSAgentListSurface` now projects visible SaaS Agent rows as selectable
  entities with:
  - `operation_id`
  - exact typed args
  - visible labels/slugs
- This allowed owner-workbench chat to open a listed SaaS Agent without
  hardcoded parsing and without asking for a hidden internal id.

### Tightened planner guidance

- Router prompt now explicitly tells Corpus to:
  - choose only from `planning_context`
  - use visible entity payloads when available
  - prefer `route.switch_surface` for same-node peer-surface changes
- Stream prompt no longer asks for extra confirmation before opening or
  switching a work surface.

### Learning surface semantics

- Added Corpus-owned planning descriptions for Learning peer surfaces:
  - policy gaps
  - failed executions
  - active policies
  - rejected

## Verification Run This Session

### Focused backend verification

```powershell
python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q
```

Result: `81 passed`.

### Broader backend verification

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q
```

Result: `87 passed`.

### Frontend verification

```powershell
cd frontend
npm run type-check
```

Result: passed.

### Docker/browser verification

```powershell
docker compose up -d --build backend
```

Result: passed.

Manual in-app browser verification from the live Docker app:

- `list agents`
- `open Live Commerce 1779760865401`
- `open learning`
- `show rejected`
- `go home`

Observed result:

- owner-workbench chat navigation moved the graph correctly
- `open Live Commerce 1779760865401` opened the selected agent directly from
  the visible list surface
- `show rejected` switched the Learning peer surface through chat

### Docker E2E verification

```powershell
cd frontend
npm run e2e:docker
```

Result: passed.

Artifacts:

- `C:\Users\ragha\AppData\Local\Temp\saastoagent-ui-e2e-1779761987528`

```powershell
cd frontend
npm run e2e:medusa:docker
```

Result: passed.

Artifacts:

- `C:\Users\ragha\AppData\Local\Temp\saastoagent-medusa-ui-e2e-1779762026718`

Checkout result:

- `completed = true`
- `reason = "checkout completed"`

### Diff sanity

```powershell
git diff --check
```

Result: no diff errors; CRLF warnings only.

## Important Findings

### Fixed during live verification

- The owner-workbench planner initially lacked visible selectable-entity context
  for the SaaS Agent list surface.
- That caused chat to ask for an internal id even though the user was looking
  at a visible selectable list.
- The fix was architectural:
  - expose visible selectable entities from the current surface
  - keep selection model-driven over legal typed ops
  - do not reintroduce any phrase matcher

### Remaining debt

A sidecar audit still found boundary debt around browser URL replay and
surface-id hydration:

- frontend popstate replay still assembles a `route.open_node` payload
- snapshot/load still trusts browser-provided `surface_id` too loosely
- `route.open_node` planning schema can still be made more faithful to legal
  navigation

This did not block the verified chat flows, but it is the next cleanup slice.

## Restart Point

Start the next session from:

- `context.md`
- `context_checkpoints/context_checkpoint_26-05-2026-08-56AM.md`
- `docs/superpowers/plans/2026-05-26-routedeck-corpus-hardcoding-removal.md`
- `SYSTEM_FLOW_INDEX.md`
- `test_index/route-deck-contract.md`

Recommended next step:

1. tighten browser URL replay and snapshot surface validation
2. rerun the RouteDeck/Corpus backend suite
3. rerun both Docker browser E2E flows
