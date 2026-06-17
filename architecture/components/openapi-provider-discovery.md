# OpenAPI Provider and Discovery

## Purpose

This component owns the path from a user-provided REST/OpenAPI description to a
normalized SaaS Agent catalog: actions, entities, auth requirements, activation
state, generated tools, and setup-time ToolRouter index artifacts.

## Owner Files

- `backend/providers/base.py`
- `backend/providers/rest/adapter.py`
- `backend/providers/rest/parser.py`
- `backend/services/catalog.py`
- `backend/services/discovery/activation.py`
- `backend/services/discovery/engine.py`
- `backend/services/toolrouter/documents.py`
- `backend/services/toolrouter/index_builder.py`
- `backend/services/tools/generator.py`
- `backend/routes/connections.py`
- `backend/routes/saas_agents.py`

## Public Interfaces

- API connection create/update/activate routes.
- Provider adapter/parser contracts.
- Discovery activation service.
- Generated action/tool catalog consumed by SaaS Agent runtime.
- Setup-time router index builder fed only by current `ActionNode` and
  `GeneratedTool` rows.

## Dependent Flows

- Owner API connection setup.
- OpenAPI schema fetch and parse.
- Catalog readiness and action/entity generation.
- Fusion router index readiness after generated tools exist.
- Medusa fixture acceptance setup.
- Generated action availability for deployed chat.

## Router Index Lifecycle

Activation builds the fusion router index during setup, after action discovery
and generated tool creation. The index builder creates bounded endpoint,
parameter, request, response, auth, and graph/resource documents from the
current arbitrary OpenAPI catalog rows. Runtime chat turns read the ready index;
they do not rebuild it.

The router artifacts are generic per SaaS Agent data. They must not contain
Medusa-specific endpoint maps, phrase routers, credential values, decrypted
auth material, or public visitor tokens.

## Tests And Evidence

- `backend/tests/test_rest_catalog.py`
- `backend/tests/test_toolrouter_documents.py`
- `backend/tests/test_toolrouter_index_builder.py`
- `backend/tests/test_toolrouter_activation.py`
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
- Router index document generation, fingerprinting, or readiness rules.
- API connection auth metadata handling.
- Medusa fixture setup instructions or acceptance criteria.
