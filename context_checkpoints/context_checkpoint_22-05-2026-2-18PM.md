# Context Checkpoint - 22-05-2026 2:18PM IST

## Current State

SaaStoAgent v0.1 has a verified horizontal sandbox path:

signup -> create SaaSAgent -> connect OpenAPI -> activate catalog/tools ->
enable deployed URL -> public chat -> execution/approval rails.

The latest session removed Medusa hardcoding from product runtime and validated
the generic setup flow against a real Medusa Docker target through UI only.

## Verified Commands

- `python -m pytest backend/tests/test_rest_catalog.py backend/tests/test_app_graph_contract.py -q`
  - `45 passed in 19.28s`
- `npm run type-check` in `frontend`
  - passed
- `docker compose up -d --build frontend`
  - passed
- `npm run e2e:docker` in `frontend`
  - passed
- `npm run e2e:medusa:docker` in `frontend`
  - passed

## Latest Verified Accounts

- Medusa E2E SaaStoAgent owner:
  `medusa-ui-e2e-1779437277860@example.com` / `SaaStoAgent123!`
- Mock E2E SaaStoAgent owner:
  `ui-e2e-1779437248299@example.com` / `SaaStoAgent123!`
- Medusa fixture admin:
  `admin@saastoagent.local` / `Admin123!`

## Important Evidence

- Mock E2E evidence:
  `C:\Users\ragha\AppData\Local\Temp\saastoagent-ui-e2e-1779437248116`
- Medusa E2E evidence:
  `C:\Users\ragha\AppData\Local\Temp\saastoagent-medusa-ui-e2e-1779437277844`
- Real Medusa deployed URL from latest run:
  `http://localhost:3007/a/live-medusa-1779437277860`

## Carry Forward

Do not deepen individual modules yet. Start the next session by addressing:

- RouteDeck/Corpus boundary split. RouteDeck should be framework-clean, while
  Corpus owns SaaStoAgent product conversation and surfaces.
- Raw JSON public result UX. Add collapsible public details as a temporary
  measure.
- Query continuity for product purchase follow-up. The system must ground
  follow-up actions in prior product results and ask natural missing details
  instead of IDs or credential headers.

## Durable Context Links

- ADR: `decisions/ADR-012-openapi-driven-target-fixtures.md`
- ADR: `decisions/ADR-013-routedeck-corpus-boundary.md`
- Dev validation:
  `architecture/dev_validated_docs/2026-05-22_openapi_driven_medusa_e2e_validation.md`
- Knowledgebase:
  `knowledgebase/patterns/openapi-driven-fixture-validation.md`
- Known gap:
  `knowledgebase/patterns/deployed-chat-result-continuity-gap.md`

## Exact Observed Product Follow-Up Failure

The deployed Medusa chat could list products, but the follow-up path failed:

- User asked `what products do we have`.
- Agent returned raw JSON with `Medusa T-Shirt`.
- User asked `i want to buy medusa tshirt`.
- Agent asked for `id`.
- User said `idk`.
- Agent recovered the T-shirt and sizes.
- User asked `add the L size to cart`.
- Agent fell back to a generic missing-detail prompt mentioning unrelated
  routes and `x publishable api key`.

This should be treated as an OpenAPI-driven runtime continuity/orchestration
bug, not as a Medusa-specific hardcode opportunity.
