# RouteDeck Authoring Guide

This guide describes how to change SaaStoAgent's RouteDeck-backed app graph
without reintroducing product/framework drift.

For new product runtime work, start in `backend/services/app_graph/`, not the
older entry-runtime RouteDeck files.

## Authoring Rule

Every new workflow capability needs three aligned pieces:

```text
graph/runtime authority
  -> RouteDeck projection metadata
    -> product UI and Corpus planning context
```

If a user can click it, Corpus should be able to reach the same typed operation
through product-facing context. If Corpus can do it, the graph/runtime must
validate it before commit.

## Add Or Change A Node

1. Add or update the node id in `backend/services/app_graph/manifest.py`.
2. Add the node's action availability and capability metadata in the same
   manifest layer.
3. Add or update the runtime handler in `backend/services/app_graph/runtime.py`.
4. Add or update surface projection in `backend/services/app_graph/corpus_surfaces.py`
   and `backend/services/app_graph/corpus_routedeck_state.py`.
5. Add tests in `backend/tests/test_corpus_graph_contract.py` or
   `backend/tests/test_app_graph_contract.py`.
6. Update docs only after the behavior is validated.

Do not make a React route or local Zustand field the source of graph truth.

## Add Or Change An Operation

1. Define the operation id and metadata in `backend/services/app_graph/manifest.py`.
2. Set `invocation_kind` accurately:
   - `direct` for ready one-click operations
   - `form` for operations that require review/input
   - `entity_selector` for operations that need selected product entities
   - `surface` for product-facing surface opens
   - `hidden` for internal navigation/runtime controls
3. Set required args, accepted arg keys, and readiness metadata so generic UI
   can distinguish direct dispatch from form/selector/review behavior.
4. Implement runtime validation before commit in
   `backend/services/app_graph/runtime.py`.
5. Ensure `backend/services/app_graph/corpus_turn_planning.py` exposes the
   product-facing form of the operation and hides hidden/internal route ops from
   normal planning.

Never add backend phrase tables, alias routers, or deterministic text routers to
map normal chat to operations. Corpus should infer intent from chat history plus
structured planning context.

## Add Or Change A Surface

1. Define the surface in `backend/services/app_graph/corpus_surfaces.py`.
2. Give peer surfaces product-facing labels and descriptions that make sense to
   humans and Corpus.
3. Use a peer surface for alternate views within the same workflow.
4. Use a child/detail node for committed nested work, such as a review of one
   policy candidate or one execution trace.
5. If the surface displays selectable product entities, project those entities
   with bound operation payloads so Corpus can act on what the user sees without
   asking for hidden ids.
6. Render the surface in product UI code under
   `frontend/src/components/appGraph/`.

Surface changes should preserve the standard `surface_id` query key.

## Add Or Change Browser Replay

Browser replay is internal infrastructure.

- Keep direct URL loads and popstate handling validated by the backend.
- Do not expose browser replay as normal Corpus vocabulary.
- Reject or recover invalid node/surface combinations.
- Reject injected review surfaces unless they correspond to the current pending
  operation.
- Keep frontend route handling inside the single `/app/*` shell so chat
  navigation does not remount the page and lose conversation state.

## Add Or Change Product Quick Actions

Product quick actions must filter out:

- `operation.id` starting with `route.`
- `invocation_kind=hidden`
- operations missing required args when `can_dispatch_now=false`

Clickable action controls should dispatch typed operations from the current
RouteDeck projection. They should not call product mutation APIs directly when a
graph operation exists.

## Add Or Change Corpus Planning Context

Use `backend/services/app_graph/corpus_turn_planning.py`.

Normal planning context should include:

- current node and active surface summary
- active SaaS Agent summary
- active surfaces
- product-facing `surface_options`
- visible selectable entities
- product legal operations with accepted args/readiness metadata

Normal planning context should exclude:

- hidden route ops
- blocked operations
- endpoint paths
- trace ids
- approval ids
- raw credentials or connection auth details

Blocked operations may remain available to diagnostics/meta-introspection, not
ordinary deployed or owner chat.

## Validation Checklist

Run focused backend tests after changing graph/runtime/projection behavior:

```powershell
python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q
```

Run frontend type checking after changing product surfaces:

```powershell
cd frontend
npm run type-check
```

Run browser E2E after changing owner navigation, deployment, public chat,
approval, or Medusa-related flows:

```powershell
cd frontend
npm run e2e:docker
npm run e2e:medusa:docker
```
