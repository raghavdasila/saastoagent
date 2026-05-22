# ADR-012: OpenAPI-Driven Target Fixtures

Date: 2026-05-22
Status: Accepted

## Context

SaaStoAgent v0.1 uses Medusa Storefront/Admin as acceptance fixtures, but the
product vision is not a Medusa-specific assistant. The builder must create a
SaaSAgent from user-provided connection details and an OpenAPI schema, then let
generated catalog/tools, policy, retrieval, and execution drive the deployed
agent behavior.

During the horizontal sandbox pass, Medusa assumptions appeared in product
runtime and setup UI:

- connection setup exposed target-specific choices
- setup copy implied Medusa-specific paths
- runtime validation risked passing because fixture knowledge leaked into
product behavior

That made the verified slice less valuable. A hardcoded Medusa path can pass
demo tests while violating the product contract.

## Decision

Product runtime must remain OpenAPI/user-config driven. Medusa, or any other
target SaaS, may appear only as fixture/test/demo data unless explicitly moved
behind a generic preset import flow.

The accepted runtime contract is:

- connection fields are generic: name, base URL, OpenAPI URL or raw OpenAPI
  schema, auth type, credential value, and credential placement metadata
- catalog activation discovers from the supplied schema, not from a target
  dropdown
- generated tools and REST execution derive behavior from the OpenAPI document
- target credentials are kept separate from visitor authentication
- credential headers/cookies are not exposed as public missing-input prompts
- E2E validation must exercise the UI setup path and deployed chat path rather
  than directly calling the target API to prove the answer

Fixture rules:

- Medusa Storefront/Admin may remain in `test_targets`, E2E scripts, benchmark
  artifacts, and datasets
- fixture names may appear in tests and evidence
- product services, providers, and frontend source must not branch on Medusa
  names or use Medusa-only routing logic

## Consequences

- Target presets, if added later, must compile into generic connection/schema
  values before activation.
- Acceptance tests must include scans or assertions that prevent target names
  from leaking into product runtime.
- Real target E2E remains valuable only when the app is configured through the
  same UI a user would use.
- Product quality problems discovered with Medusa, such as product-to-cart
  continuity, must be fixed as generic OpenAPI/runtime orchestration issues.

## Validation

Verified on 2026-05-22:

- `python -m pytest backend/tests/test_rest_catalog.py backend/tests/test_app_graph_contract.py -q`
  - `45 passed in 19.28s`
- `npm run type-check` in `frontend`
  - passed
- `npm run e2e:docker` in `frontend`
  - passed
- `npm run e2e:medusa:docker` in `frontend`
  - passed against real Medusa Docker target with UI-driven schema setup
- Product code scan for `medusa|Medusa|MEDUSA` under backend services/providers
  and frontend source returned no product-runtime matches.

## Open Follow-Up

The real Medusa chat proved product listing but exposed a generic runtime
continuity gap for follow-up purchase actions. That must be fixed without
Medusa-specific branching.
