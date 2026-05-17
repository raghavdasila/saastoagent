# Essential Validation And QA Fixes

Timestamp: 2026-05-14 06:16 +05:30

## Scope

- Validate whether the completed SaaS Agent foundation works in the running Docker app.
- Run direct live e2e, embedded browser QA, and independent QA-agent validation.
- Fix validation blockers instead of stopping at the first failure.

## Findings And Fixes

- Frontend build initially missed the new `learn` surface in activity icon/view mappings.
  - Fixed `SaaSAgentView`, QA view aliases, and `ActivityBar` icon mapping.
- The `rag_memory_learning_surfaces` QA scenario checked `Save memory` while the Sessions & Memory panel was still on the Sessions tab.
  - Fixed the scenario by clicking the Memories tab before collecting evidence.
- The live Docker database still had old workspace-column shape for some tables.
  - Added a local/dev startup migration before metadata creation to rename old `workspace_id` columns to `saas_agent_id` and preserve the working foundation on existing volumes.
- Embedded browser QA found a runtime 500 after activation on `GET /connections`.
  - Root cause: async SQLAlchemy lazy-load of `connection.activation_state` inside response serialization.
  - Fixed by eager-loading `activation_state` and `credentials` in the connection list query.

## Validation

- `GET http://localhost:8085/api/health` - passed.
- `GET http://localhost:3007` - passed.
- `python -c "from backend.main import app; print(app.title)"` - passed.
- `python -m backend.services.route_deck.validate` - passed.
- `python -m pytest backend/tests/test_learning_service.py backend/tests/test_memory_service.py backend/tests/test_rag_generation.py backend/tests/test_saas_agent_route_deck.py backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 36 passed.
- `npm run type-check` in `frontend/` - passed.
- `npm run build` in `frontend/` - passed with the existing Vite chunk-size warning.
- Direct live API e2e against Docker backend and Petstore OpenAPI - passed:
  - seeded auth and selected SaaS Agent
  - initial RouteDeck at `needs_connection`
  - REST connection creation
  - activation SSE completion
  - catalog generation with 3 entities and 19 actions
  - generated RAG with 1 document and 3 chunks
  - memory create/list
  - chat SSE tool execution
  - RouteDeck transition to `result_review`
- Connection-list regression after activation - passed:
  - returned 1 ready connection, 19 tools, and 19 action nodes.
- Embedded browser QA `rag_memory_learning_surfaces` - passed with zero console errors.
- Embedded browser QA `connection_catalog_preview` - passed with zero console errors after the eager-load fix.
- Independent QA agent - passed health, frontend reachability, Docker stack, full backend tests, frontend type-check, authenticated surface smoke, QA panel visibility, endpoint surface check, Petstore activation, generated RAG, and memory creation.

## Remaining Work

- Live Medusa Storefront/Admin preview and activation smoke still needs an available Medusa target.
- Production migration hardening remains a post-foundation task.
- Approval policy remains foundation-level and should be hardened before production use.
