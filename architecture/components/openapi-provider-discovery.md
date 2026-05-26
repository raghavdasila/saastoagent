# OpenAPI Provider and Discovery

## Purpose

This component owns the path from a user-provided REST/OpenAPI description to a
normalized SaaS Agent catalog: actions, entities, auth requirements, activation
state, and generated tools.

## Owner Files

- `backend/providers/base.py`
- `backend/providers/rest/adapter.py`
- `backend/providers/rest/parser.py`
- `backend/services/catalog.py`
- `backend/services/discovery/activation.py`
- `backend/services/discovery/engine.py`
- `backend/services/tools/generator.py`
- `backend/routes/connections.py`
- `backend/routes/saas_agents.py`

## Public Interfaces

- API connection create/update/activate routes.
- Provider adapter/parser contracts.
- Discovery activation service.
- Generated action/tool catalog consumed by SaaS Agent runtime.

## Dependent Flows

- Owner API connection setup.
- OpenAPI schema fetch and parse.
- Catalog readiness and action/entity generation.
- Medusa fixture acceptance setup.
- Generated action availability for deployed chat.

## Tests And Evidence

- `backend/tests/test_rest_catalog.py`
- `backend/tests/test_saas_agent_route_deck.py`
- `test_index/saas-agent-foundation-contract.md`
- `docs/medusa-api-agent-test-guide.md`
- `frontend/scripts/e2e-medusa-docker.mjs`

## Update Triggers

Update this component doc and the code map when changing:

- OpenAPI parser behavior.
- Provider adapter output shape.
- Discovery activation readiness.
- Generated action/entity/tool schema.
- API connection auth metadata handling.
- Medusa fixture setup instructions or acceptance criteria.
