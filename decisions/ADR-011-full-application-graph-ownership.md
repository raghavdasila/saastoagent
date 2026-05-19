# ADR-011: Full Application Graph Ownership

Date: 2026-05-16
Status: Accepted
Supersedes: ADR-009 for application-wide navigation/control ownership
Current status: Graph ownership still stands, but the product contract is now Corpus-first with RouteDeck projections and diagnostics as defined in [../architecture/route-deck-corpus-vision.md](../architecture/route-deck-corpus-vision.md), not raw eligible-action rendering in the product shell.

## Context

The prior foundation split RouteDeck into an entry graph and a selected SaaS Agent snapshot. That proved the domain services, but it left the frontend with too much workflow authority: panel switching, capability registries, path-derived modes, and command-style approval could still decide what the application was doing.

The reset target is one graph-first SaaStoAgent application. A user enters at `home`, selects or creates a SaaS Agent, configures an API, activates catalog/RAG, inspects entities/actions, plans execution, approves or rejects risky work, reviews results, and manages knowledge, memory, learning, QA, and recovery as graph nodes.

## Decision

SaaStoAgent now treats the backend app graph as the application navigation and capability authority.

- The unified graph is rooted at `home`.
- RouteDeck is the bridge from backend graph state to frontend surfaces.
- The frontend renders current node, eligible actions, context lens, evidence, and surface hints from `GET /api/app/graph/snapshot`.
- Frontend action submission uses `POST /api/app/graph/action`.
- Free text may not route by English phrase lists. Until a structured model router is configured, free text returns eligible RouteDeck actions and requires typed action ids.
- URL routes hydrate graph context only. URLs do not bypass backend eligibility.
- SaaS Agent execution, approval, RAG, memory, learning, and QA actions are graph actions, even when existing domain services perform the side effects.

## Contract

Implemented graph endpoints:

- `GET /api/app/graph/snapshot`
- `POST /api/app/graph/turn`
- `POST /api/app/graph/action`

Implemented graph nodes:

`home`, `auth_sign_in`, `auth_register`, `saas_agent_select`, `saas_agent_create`, `agent_home`, `connection_configure`, `schema_preview`, `catalog_activation`, `catalog`, `entities`, `actions`, `execution_planning`, `needs_input`, `approval_required`, `executing`, `result_review`, `knowledge`, `memory`, `learning`, `qa`, and `recovery`.

Implemented frontend graph routes:

- `/app/home`
- `/app/:nodeId`
- `/app/agents/:saasAgentId`
- `/app/agents/:saasAgentId/:nodeId`

Compatibility routes such as `/`, `/login`, `/register`, and `/agents/:saasAgentId` hydrate into graph routes.

## Consequences

- New frontend workflow navigation must come from RouteDeck snapshots/actions, not local capability registries.
- Existing SaaS Agent domain services remain reusable implementation utilities, but they do not own route decisions.
- The legacy Entry RouteDeck and SaaS Agent snapshot route remain compatibility surfaces until the final purge pass removes consumers and stale QA assumptions.
- QA scenarios should reference graph node ids, action ids, evidence, and API/console gates.

## Validation

- `pytest backend/tests/test_app_graph_contract.py backend/tests/test_route_deck_contract.py -q`: 15 passed.
- `pytest backend/tests -q`: 40 passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
