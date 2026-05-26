# System Flow Index - SaaStoAgent v0.1

Last Updated: May 26, 2026 02:21 PM IST

This file is the compact source of truth for the currently implemented runtime
and UX flows. Use `context.md` for current restart state and `README.md` for
setup.

## Active Architecture

```text
Product graph/runtime owns truth, guards, and commits.
RouteDeck exposes validated state, surfaces, legal capabilities, and diagnostics.
Corpus interprets normal user chat against product-facing RouteDeck context.
React renders projected product surfaces and dispatches typed operations.
```

Current anchors:

- Project setup: `README.md`
- Current context: `context.md`
- Product RouteDeck guide: `docs/route-deck/route-deck-overview.md`
- Framework RouteDeck guide: `../routedeck/docs/using-routedeck.md`
- Framework runtime anchor: `../routedeck/docs/agentic-ui-state-runtime.md`
- Product vision: `architecture/route-deck-corpus-vision.md`
- Boundary ADR: `decisions/ADR-013-routedeck-corpus-boundary.md`
- Medusa guide: `docs/medusa-api-agent-test-guide.md`

## Primary Routes And Endpoints

Frontend:

- owner workbench: `http://localhost:3007`
- `/app/home`
- `/app/:nodeId`
- `/app/agents/:saasAgentId`
- `/app/agents/:saasAgentId/:nodeId`
- deployed public chat: `/a/{slug}`

Backend:

- health: `GET /api/health`
- state: `GET /api/corpus/state`
- action: `POST /api/corpus/action`
- stream: `GET /api/corpus/stream`
- diagnostics: `GET /api/diagnostics/stream`
- deployed profile/chat: `/api/deployed-agents/{slug}`

Browser surface query key:

- `surface_id`

## RouteDeck/Corpus Rules

- RouteDeck shared code stays product-neutral.
- Corpus is the SaaStoAgent product agent.
- Corpus plans from structured `planning_context`, not Python phrase routing.
- Corpus chooses product operations, product surface intents, or
  product-safe clarifications.
- Runtime validates every operation before commit.
- Legal operations are not automatically generic quick actions.
- Hidden/internal route operations stay out of normal Corpus planning and
  product quick actions.
- Diagnostics may expose internals; public deployed chat may not.

Internal route operations:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

These are runtime/browser/history infrastructure, not ordinary product actions.

## Owner Workbench Flow

Typical owner flow:

```text
home
  -> auth or dashboard
  -> create/open SaaS Agent
  -> connect API
  -> activate OpenAPI catalog/tools
  -> inspect catalog/actions/entities
  -> configure deployment
  -> review execution/learning/approval surfaces
```

Owner UI rules:

- The central workbench remains mounted while graph state changes.
- Chat-driven navigation should not refresh or remount the full page.
- Product controls dispatch typed operations from RouteDeck projection.
- Forms/review surfaces are graph-owned.
- The context sidebar can show selected agent, current work, API readiness,
  tools, and approval-relevant status.

## Corpus Planning Context

Normal planning context includes:

- current node and active surface summary
- active SaaS Agent summary
- active surfaces
- product-facing `surface_options`
- visible selectable entities with bound typed operation args
- product legal operations with labels, descriptions, accepted args, and
  readiness metadata

Normal planning context excludes:

- hidden route operations
- blocked operations
- endpoint paths
- trace ids
- approval ids
- credential values
- visitor-fillable API auth headers

## Deployed Agent Flow

Public visitor flow:

```text
visitor query
  -> deployed SaaS Agent orchestration
    -> generated OpenAPI action selection/execution
      -> execution-frame variables and policy checks
        -> public-safe response
```

Rules:

- Medusa is an acceptance fixture only.
- Product runtime must remain OpenAPI/user-config driven.
- Public chat must not expose operation ids, endpoint paths, raw tool labels,
  trace ids, approval ids, cart ids, internal slot names, or API auth headers.
- Natural missing details can be requested publicly; internal dependencies must
  be resolved privately or blocked with product-safe policy language.

Known current debt:

- Some natural product queries can still trigger over-technical clarification in
  public chat. Example class: asking for product names can mention the
  publishable-key header. This needs response-shaping/safety hardening.

## Medusa Fixture

Fixture ports:

- backend/admin API: `http://localhost:9000`
- storefront: `http://localhost:8000`
- fixture Postgres: `localhost:5434`

Current verified manual fixture setup in this thread:

- SaaS Agent: `Live Commerce Raghav 1779776944731`
- public URL: `http://localhost:3007/a/live-commerce-raghav-1779776944731`
- connection: `Live Commerce Store API`
- activation: ready, 64 generated actions/tools
- deployment: anonymous enabled
- public prompt `list products`: returned the four Medusa fixture products

Do not write credentials into docs.

## Compatibility Debt

Compatibility routes/endpoints may still exist, but they are not the product UI
contract. New work should target the app graph, Corpus endpoints, and RouteDeck
store path.

Do not add new product behavior to older entry-runtime or selected-agent
RouteDeck paths unless the task is explicitly a migration/purge.

## Validation Index

Fast checks:

```powershell
Invoke-RestMethod http://localhost:8085/api/health
Invoke-WebRequest http://localhost:3007 -UseBasicParsing
cd frontend
npm run type-check
```

Focused backend checks:

```powershell
python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q
```

Broader RouteDeck/Corpus checks:

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q
```

Browser E2E:

```powershell
cd frontend
npm run e2e:docker
npm run e2e:medusa:docker
```
