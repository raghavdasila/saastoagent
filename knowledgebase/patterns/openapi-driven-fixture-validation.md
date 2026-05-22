# Pattern: OpenAPI-Driven Fixture Validation

Date: 2026-05-22

## Finding

Target SaaS fixtures are useful only when they validate the generic SaaStoAgent
runtime. They become harmful when product runtime branches on fixture names,
target-specific paths, or preselected dropdown values.

The validated pattern is:

```text
fixture target
  -> generic connection fields
  -> user-provided OpenAPI schema
  -> generated catalog/tools
  -> deployed chat execution
  -> trace/result validation
```

## Why This Matters

SaaStoAgent is meant to create agents from user-provided SaaS APIs. If Medusa or
another fixture appears in product logic, E2E can pass while proving the wrong
architecture.

## Rules

- Fixture names may live in `test_targets`, E2E scripts, benchmark artifacts,
  and seed datasets.
- Product services/providers/frontend source should not branch on fixture names.
- Setup UI should collect generic connection/schema/auth fields.
- Generated actions should come from OpenAPI discovery.
- Missing-input prompts should not expose credential headers/cookies to public
  visitors.
- Real target validation should run through the UI and deployed chat, not direct
  target API checks.

## Proof From Current Slice

Validated on 2026-05-22:

- `npm run e2e:docker` passed against deterministic mock fixtures.
- `npm run e2e:medusa:docker` passed against real Medusa Docker target.
- Product code scan for `medusa|Medusa|MEDUSA` under backend services/providers
  and frontend source returned no product-runtime matches.
- Latest real Medusa trace used generic input `{"limit": 5}` and returned 4
  seeded products.

## Reuse

Use this pattern for future Shopify, Stripe, GitHub, HubSpot, or other SaaS
fixtures. The fixture can be named in tests; the runtime must remain generic.
