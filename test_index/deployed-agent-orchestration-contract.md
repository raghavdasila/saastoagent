# Deployed Agent API Orchestration Contract

Date: 2026-05-25

## Scope

Validation and anti-drift rules for public deployed SaaS agent chat when it
uses generated OpenAPI actions through the agent orchestration layer.

## Contract

- Public chat must not expose internal resource ids, endpoint paths, operation
  ids, trace ids, cart ids, auth headers, or raw tool names.
- Router missing-input behavior must be consumed by the SaaS agent
  orchestrator, not surfaced directly to the buyer.
- Missing inputs are classified as:
  - internal dependencies: opaque ids, path ids, parent resource ids
  - public fields: size, quantity, email, address, region, shipping choice,
    payment choice, confirmation
- Internal dependencies resolve from `execution_frame_v1.variables` or from
  generated OpenAPI actions.
- Write dependency resolution requires an approved domain policy. Without one,
  the flow creates a `domain_policy_gap` learning candidate and returns a
  public-safe policy-needed response.
- Approved policy hints apply only to the SaaS agent and generated action path
  chain they were approved for.
- The state frame shape is generic variables, not Medusa-specific state.

## Current Evidence

- `python -m pytest backend/tests -q`: passed, 171 tests.
- `npm run type-check`: passed.
- API orchestration tests cover missing-input classification, policy gaps,
  approved policy continuation, and public-safe behavior.
- State variable tests cover resource id/scalar persistence and pending choice
  prompts that hide private values.

## Browser Evidence Status

Previous screenshots covered:

- product list
- buyer asks for Medusa T-Shirt
- buyer asks to add L size to cart
- policy-needed response without exposing cart id

Full checkout has not passed browser E2E yet.

## Required Next Validation

```powershell
cd agent-lab-powered-projects/saastoagent-v0.1/frontend
npm run e2e:medusa:docker
```

Passing browser evidence must include:

- no raw internal ids in public transcript
- no raw endpoint paths or operation ids in public transcript
- product/variant resolution from prior result context
- cart creation or reuse through approved policy
- add-line-item chain
- checkout continuation failure, if any, routed to owner-safe diagnostics
  instead of public internal prompts
