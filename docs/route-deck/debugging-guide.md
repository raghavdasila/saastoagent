# RouteDeck Debugging Guide

RouteDeck debugging is for developers and owners. It should explain graph state
and runtime decisions without leaking those internals into normal product chat.

## First Questions

When RouteDeck/Corpus behavior looks wrong, answer these in order:

1. What node and surface does RouteDeck say are active?
2. Which operations are legal in the current projection?
3. Which legal operations are hidden/internal?
4. Which operations are blocked, and why?
5. Is the user asking for a product operation, a product surface, or browser
   history/location replay?
6. Did the runtime validate and commit, reject, or ask for review?

## Surfaces To Inspect

Owner UI:

- context/evidence sidebar for selected agent, current work, API readiness,
  tools, and pending approval state
- active surface under the central Corpus conversation
- diagnostics disclosure for graph/runtime internals

Backend endpoints:

- `GET /api/corpus/state`
- `POST /api/corpus/action`
- `GET /api/corpus/stream`
- `GET /api/diagnostics/stream`

Frontend integration:

- `frontend/src/components/appGraph/AppGraphShell.tsx`
- `frontend/src/components/appGraph/corpusOperations.tsx`
- `frontend/src/components/appGraph/corpusRouteDeckClient.ts`

Backend integration:

- `backend/services/app_graph/runtime.py`
- `backend/services/app_graph/corpus_turn_planning.py`
- `backend/services/app_graph/corpus_routedeck_state.py`
- `backend/services/app_graph/corpus_surfaces.py`

## Debugging Chat Navigation

If Corpus asks for unnecessary clarification:

- inspect the current `planning_context`
- confirm the requested product action appears in `legal_operations`
- confirm visible selectable entities include labels and bound args when the UI
  shows selectable records
- confirm peer surfaces appear in `surface_options`
- confirm hidden route operations are not the only way to express the intent

If Corpus emits or exposes internal route operations:

- check that normal planning context excludes `route.open_node`,
  `route.switch_surface`, `route.back`, `route.forward`, and `route.cancel`
- check that UI quick actions filter `operation.id.startsWith("route.")` and
  `invocation_kind === "hidden"`
- check that product surface intents are mapped to internal route dispatch only
  after runtime validation

If chat navigation refreshes the whole page:

- confirm the frontend still uses a single `/app/*` route shell
- confirm graph state changes update the RouteDeck store rather than causing a
  React Router remount
- inspect URL replacement and `surface_id` query handling

## Debugging Browser URL Replay

Browser URLs are validated location replay.

Check:

- path node id
- `saas_agent_id` route/query state
- `surface_id` query value
- whether the requested surface is active and legal for the requested node
- whether a requested review surface corresponds to the current pending
  operation

Invalid combinations should be rejected or recovered. They should not become
ordinary product intent and should not appear in Corpus planning vocabulary.

## Debugging Public Chat Leaks

Public deployed chat should never reveal:

- operation ids
- endpoint paths
- trace ids
- approval ids
- API auth header names or credential prompts
- raw tool event names
- internal slot/resource ids

If a visitor is asked for an API header or internal id, inspect the generated
tool schema and deployed-agent orchestration. Connection-level auth should be
filled privately from stored credentials, not requested from the visitor.

## Debugging Approval Polling

Pending approvals are owner-workbench state for generated side-effect
executions that require owner approval.

If `/approvals/pending` polls every two seconds from unrelated surfaces:

- confirm polling is gated by active agent and approval-relevant UI/state
- confirm manual approve/cancel still invalidates/refetches approvals
- confirm public chat does not receive raw approval ids

## Useful Checks

Backend contracts:

```powershell
python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q
```

Frontend quick-action and shell checks:

```powershell
cd frontend
npm run type-check
```

Full owner/deployed browser paths:

```powershell
cd frontend
npm run e2e:docker
npm run e2e:medusa:docker
```

Search for stale internal leaks:

```powershell
Get-ChildItem -Recurse -File docs architecture decisions |
  Select-String -Pattern "Open node","Switch surface","3005","entry_runtime","backend/services/route_deck/catalog.py"
```
