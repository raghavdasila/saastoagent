# 2026-05-22 14:18 IST - Sandbox Hardening And Medusa E2E Closeout

## Scope

Closed the horizontal hardening session after removing Medusa-specific product
runtime assumptions, validating the generic OpenAPI setup path through UI, and
running a real Medusa Docker target through deployed chat.

## Completed

- Removed Medusa hardcoding from product runtime/UI and replaced it with generic
  OpenAPI/user-config driven setup.
- Removed the setup target dropdown and added raw OpenAPI schema textarea
  support.
- Persisted `raw_spec` on connection configuration and made REST catalog
  discovery prefer raw specs before fetched spec URLs.
- Excluded OpenAPI header/cookie parameters from generated tool schemas and
  REST missing-input prompts.
- Fixed bare list query input extraction so `list products` does not become
  `q=list products`.
- Stabilized route replacement and connection setup hydration for browser E2E.
- Added and ran a real Medusa UI E2E command:
  `npm run e2e:medusa:docker`.
- Verified public deployed chat executes against the live Medusa backend through
  SaaStoAgent, not by direct target API validation.

## Verification

- `python -m pytest backend/tests/test_rest_catalog.py backend/tests/test_app_graph_contract.py -q`
  - `45 passed in 19.28s`
- `npm run type-check` in `frontend`
  - passed
- `docker compose up -d --build frontend`
  - passed
- `npm run e2e:docker`
  - passed
  - account: `ui-e2e-1779437248299@example.com`
  - slug: `ui-e2e-1779437248299`
  - evidence:
    `C:\Users\ragha\AppData\Local\Temp\saastoagent-ui-e2e-1779437248116`
- `npm run e2e:medusa:docker`
  - passed
  - account: `medusa-ui-e2e-1779437277860@example.com`
  - slug: `live-medusa-1779437277860`
  - deployed URL: `http://localhost:3007/a/live-medusa-1779437277860`
  - evidence:
    `C:\Users\ragha\AppData\Local\Temp\saastoagent-medusa-ui-e2e-1779437277844`
- Product-code scan for `medusa|Medusa|MEDUSA` under backend services/providers
  and frontend source returned no product-runtime matches.

## Open Issues For Next Session

- RouteDeck is still too coupled with Corpus in implementation. Split framework
  concerns from Corpus product concerns before deepening modules.
- Public deployed chat should not expose raw JSON directly. Add collapsible
  result details as a temporary UX while product-specific result cards are still
  undecided.
- Query continuity failed for product purchase follow-up:
  `what products do we have` -> `i want to buy medusa tshirt` ->
  `add the L size to cart`.
  The agent exposed/asked for internal IDs and credential header names instead
  of resolving from prior results and asking natural missing details.

## Next Start

Begin with horizontal cleanup:

1. RouteDeck/Corpus boundary split.
2. Collapsible JSON result UI for public deployed chat.
3. Conversation-grounded product/variant/cart follow-up handling.
4. Re-run both Docker E2E commands after changes.

## Durable Docs Added After Closeout Review

- `decisions/ADR-012-openapi-driven-target-fixtures.md`
- `decisions/ADR-013-routedeck-corpus-boundary.md`
- `architecture/dev_validated_docs/2026-05-22_openapi_driven_medusa_e2e_validation.md`
- `knowledgebase/patterns/openapi-driven-fixture-validation.md`
- `knowledgebase/patterns/deployed-chat-result-continuity-gap.md`
