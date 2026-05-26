# RouteDeck Migration Notes

These notes document the current migration state from the older entry/setup
RouteDeck experiment to the active app-graph RouteDeck/Corpus runtime.

## Current Primary Runtime

New product UI and agent-navigation work should target:

- `backend/services/app_graph/`
- `backend/routes/corpus_graph.py`
- `frontend/src/components/appGraph/`
- sibling framework docs under `../routedeck/docs/`

Primary endpoints:

- `GET /api/corpus/state`
- `POST /api/corpus/action`
- `GET /api/corpus/stream`
- `GET /api/diagnostics/stream`

Primary frontend routes:

- `/app/home`
- `/app/:nodeId`
- `/app/agents/:saasAgentId`
- `/app/agents/:saasAgentId/:nodeId`

## Superseded Entry Runtime Shape

Older docs referenced:

- `backend/services/route_deck/catalog.py`
- `entry_runtime/graph_executor.py`
- `entry_runtime/graph_spec.py`
- `OperatorGateway.tsx`

Those paths may still exist as compatibility debt or historical scaffolding, but
they are not the current app-graph authoring path. Do not add new RouteDeck
product behavior there unless the task is explicitly to remove or migrate old
compatibility code.

## Completed Boundary Repairs

- Raw public `/api/routedeck/*` product routes were removed from the primary UI
  contract.
- `/api/corpus/*` routes now cross the RouteDeck runtime boundary.
- RouteDeck v2 navigation operations exist for browser/runtime infrastructure.
- Normal Corpus planning context is product-facing and hides internal route ops.
- Product quick actions filter hidden/internal route operations.
- `surface_id` is the standard surface query parameter.
- Chat-driven surface opens map through product surface intents before runtime
  performs validated internal route dispatch.

## Remaining Migration Risks

- Compatibility endpoints and old route surfaces can keep stale mental models
  alive if docs point to them as primary.
- Public deployed chat can still regress by exposing tool/router internals in
  response text even when the owner workbench boundary is correct.
- Browser URL replay must remain validated location replay, not product intent.

## Migration Rule

When moving old behavior forward, preserve this boundary:

```text
RouteDeck exposes state and legal capabilities.
Corpus decides product intent from normal chat and product context.
Runtime validates and commits.
Product UI renders product language.
Diagnostics expose internals read-only.
```
