# 2026-05-22 OpenAPI-Driven Medusa E2E Validation

## Scope

This note captures the implementation-backed validation from the horizontal
sandbox hardening pass. It is not a product design proposal. It records what was
actually verified.

## Validated Runtime Shape

The verified flow is:

```text
owner signs up
  -> creates SaaSAgent
  -> opens connection configuration
  -> enters generic base URL, auth metadata, and OpenAPI schema
  -> activates catalog/tools
  -> enables deployed URL
  -> visitor opens /a/:slug
  -> visitor asks for products
  -> ToolRouter/REST path selects and executes a generated read action
  -> result returns to deployed chat
```

The real Medusa test used Medusa only as a target fixture:

- Medusa Docker target ran from `test_targets`
- OpenAPI schema was uploaded through the UI as schema URL data
- deployed chat used SaaStoAgent APIs
- validation did not prove success by calling Medusa directly
- product runtime was not allowed to branch on Medusa names

## Implementation Areas Covered

- Generic OpenAPI setup UI:
  - no target dropdown
  - schema URL and raw OpenAPI textarea paths
  - generic labels/placeholders
- REST catalog discovery:
  - `raw_spec` is persisted in connection config
  - raw spec is preferred over fetched spec URL when present
- Generated tool input hygiene:
  - OpenAPI header/cookie params excluded from generated public tool schemas
  - REST missing-input prompts do not ask for credential headers directly
- Query argument handling:
  - bare list requests do not bind the whole utterance into optional search
    query fields
  - explicit search utterances can still bind search text
- Deployed chat:
  - read request executed through generated REST action
  - public chat remained separate from the RouteDeck builder workbench

## Verification Evidence

- `python -m pytest backend/tests/test_rest_catalog.py backend/tests/test_app_graph_contract.py -q`
  - `45 passed in 19.28s`
- `npm run type-check` in `frontend`
  - passed
- `docker compose up -d --build frontend`
  - rebuilt/restarted frontend/backend successfully
- `npm run e2e:docker` in `frontend`
  - passed
  - evidence:
    `C:\Users\ragha\AppData\Local\Temp\saastoagent-ui-e2e-1779437248116`
  - screenshots:
    `builder-activated.png`, `public-storefront-read.png`,
    `builder-approval-approved.png`
- `npm run e2e:medusa:docker` in `frontend`
  - passed
  - owner:
    `medusa-ui-e2e-1779437277860@example.com`
  - slug:
    `live-medusa-1779437277860`
  - deployed URL:
    `http://localhost:3007/a/live-medusa-1779437277860`
  - Medusa backend:
    `http://host.docker.internal:9000`
  - schema served for UI upload:
    `http://host.docker.internal:9110/medusa-store.yaml`
  - evidence:
    `C:\Users\ragha\AppData\Local\Temp\saastoagent-medusa-ui-e2e-1779437277844`
  - screenshots:
    `builder-medusa-activated.png`, `public-medusa-products.png`

Latest trace check for the real Medusa run:

- status: `succeeded`
- approval: `not_required`
- inputs: `{"limit": 5}`
- result returned 4 seeded products including `Medusa T-Shirt`

## Known Limits

- Public deployed chat still exposes raw JSON in the visible transcript.
- Product result rendering needs a short-term collapsible JSON detail UI before
  final product cards are designed.
- Product-to-cart continuity is not solved. The observed follow-up flow failed:
  list products -> choose Medusa T-Shirt -> add L size to cart.
- The failed follow-up must be fixed through generic conversation grounding and
  OpenAPI action orchestration, not Medusa-specific logic.
- RouteDeck/Corpus code remains too coupled and needs a boundary cleanup.

## Validation Rule Going Forward

Backend-only validation is insufficient for this slice. A claim that the
horizontal sandbox path works must include `npm run e2e:docker` or an equivalent
browser-driven replacement. Claims about real target behavior must include
`npm run e2e:medusa:docker` or another UI-driven target fixture run.

## 2026-05-24 Policy-Orchestration Update

The product-to-cart continuity limit above has a first generic implementation:

- public missing path identifiers are classified as internal orchestration
  dependencies
- the parent resource collection is derived from the OpenAPI path
- a generated parent `POST` action can create the internal dependency after an
  owner-approved `domain_policy_gap` Sandbox Learning candidate
- public chat does not expose cart/resource IDs, endpoint paths, operation IDs,
  or trace IDs

Validated commands:

- `python -m pytest backend/tests -q`
  - `133 passed`
- `npm run type-check` in `frontend`
  - passed
- `npm run e2e:medusa:docker` in `frontend`
  - passed

Manual browser validation against the generated Medusa deployment:

- deployed URL:
  `http://localhost:3007/a/live-medusa-1779615126428`
- pre-approval flow:
  `what products do we have` -> `i want to buy medusa tshirt` ->
  `add the L size to cart`
  - public response: owner-approved policy needed
  - leak scan: no `cart id`, endpoint path, operation ID, trace text, or tool
    event text
  - screenshot:
    `C:\Users\ragha\AppData\Local\Temp\saastoagent-medusa-policy-flow-1779615126418\public-medusa-policy-needed.png`
- owner-approved flow:
  - approved learning candidate:
    `trigger_type=domain_policy_gap`
  - repeated public buyer flow returned only:
    `Done. I handled that for you.`
  - leak scan: no `cart id`, generated cart ID, endpoint path, operation ID,
    trace text, or tool event text
  - screenshot:
    `C:\Users\ragha\AppData\Local\Temp\saastoagent-medusa-policy-flow-1779615126418\public-medusa-policy-approved.png`

Trace check for the approved run:

```text
postcarts            POST /store/carts                 succeeded approved_by_policy
postcartsidlineitems POST /store/carts/{id}/line-items succeeded approved_by_policy
```

Remaining limit: the first pass supports one internal dependency step. Checkout,
shipping, payment, and multi-step dependency planning remain later orchestration
work.
