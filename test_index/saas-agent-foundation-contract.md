# SaaS Agent Foundation Contract Validation

## Test Approach

This index tracks the product-contract reset from Workspace to SaaS Agent.
Slice 0 is documentation and architecture-contract work; later slices must add
backend, frontend, RouteDeck, browser, and QA automation as implementation
lands.

## Standing Validation Rule

At the end of every slice:

- run the slice's relevant checks
- fix regressions before proceeding
- update `context.md`, the active plan, `SYSTEM_FLOW_INDEX.md`, this test index
  or a focused sibling entry, and a slice log/checkpoint
- continue to the next slice unless blocked

## Slice 0 Validation

- `ADR-010-saas-agent-domain-authority.md` exists and records `SaaSAgent` as
  the domain authority.
- Active plan is `plans/saastoagent_v0_1_saas_agent_foundation_plan.md`.
- Old workspace plan points to the new plan.
- `context.md` names the new product contract and marks workspace code as
  pending rename, not as future architecture.
- `SYSTEM_FLOW_INDEX.md` records the two RouteDeck layers:
  - Entry RouteDeck
  - SaaS Agent RouteDeck

## Slice 1-2 Validation

- Backend domain names, schemas, routes, ownership fields, entry runtime nodes,
  QA seeds, and RouteDeck IDs use SaaS Agent naming.
- Backend SaaS Agent APIs are mounted at `/api/saas-agents`.
- Frontend direct operator route is `/agents/:saasAgentId`.
- Frontend store/type/component imports use SaaS Agent naming.
- Source scan over `backend` and `frontend/src` has no remaining `workspace`,
  `Workspace`, `/workspaces`, or `/w/` hits outside generated caches.

Checks run:

- `python -m backend.services.route_deck.validate` - passed.
- `python -m pytest backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 28 passed.
- `npm run build` in `frontend/` - passed.

Known environment note:

- The existing RAG import needed local `PyMuPDF`; it was installed during this run
  and `from backend.main import app` now passes.

## Slice 3 Foundation Validation

- Dashboard launch pad exposes editable SaaS Agent name and slug before create.
- Dashboard provides separate Medusa Storefront Agent and Medusa Admin Agent presets.
- Entry RouteDeck launch action is now a form with SaaS Agent name and slug fields.
- Connections view exposes Medusa Storefront/Admin API presets.
- Medusa connection presets use `VITE_MEDUSA_API_BASE_URL` or `http://localhost:9000`.

Checks run:

- `python -m backend.services.route_deck.validate` - passed.
- `python -m pytest backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 28 passed.
- `npm run build` in `frontend/` - passed.

Pending:

- Live Medusa Storefront preview/activation smoke.
- Live Medusa Admin preview smoke with auth expectations.

## Slice 4 SaaS Agent RouteDeck Validation

- SaaS Agent RouteDeck manifest exists at `backend/services/saas_agent_route_deck.py`.
- Manifest includes selected-agent setup, schema preview, catalog activation,
  catalog ready, action inspection, execution planning, input, approval,
  executing, result review, and learning review nodes.
- Backend exposes `GET /api/saas-agents/{saas_agent_id}/route-deck`.
- Runtime snapshot derives current node from real connection/catalog counts.
- Frontend RouteDeck widget switches to the selected SaaS Agent RouteDeck in
  operator mode.
- Context lens/status strip expose selected-agent context and working-on summary.

Checks run:

- `python -c "from backend.main import app; print(app.title)"` - passed.
- `python -m pytest backend/tests/test_saas_agent_route_deck.py backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 30 passed.
- `npm run build` in `frontend/` - passed.

## Slice 5 Execution Surface Validation

- `AgentExecutionTrace` persists generated REST planning/execution state under
  `saas_agent_id`.
- Read-safe generated REST actions create traces, emit tool cards, and record
  success/failure result metadata.
- Missing required inputs create `needs_input` traces.
- Write/destructive/financial generated REST actions create
  `approval_required` traces and do not execute automatically.
- `approve <trace>` resumes a pending trace and executes the generated REST
  action.
- `cancel <trace>` rejects a pending trace without making an API call.
- SaaS Agent RouteDeck derives `needs_input`, `approval_required`, `executing`,
  and `result_review` nodes from the latest trace.

Checks run:

- `python -c "from backend.main import app; print(app.title)"` - passed.
- `python -m pytest backend/tests/test_saas_agent_route_deck.py backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 31 passed.
- `npm run build` in `frontend/` - passed.

## Slice 6 RAG Generation Validation

- Generated API catalog knowledge is ingested into the existing
  `AgentDocument`/`AgentDocumentChunk` RAG tables.
- Generated execution trace knowledge is ingested from recent
  `AgentExecutionTrace` rows.
- Generated knowledge is filtered and stored by `saas_agent_id`.
- Activation refreshes generated catalog RAG after tools are generated.
- Execution finalization refreshes generated trace RAG.
- Knowledge panel exposes a manual `Generate catalog RAG` control.
- Embedding generation falls back to deterministic local vectors when no
  OpenAI API key is configured.

Checks run:

- `python -c "from backend.main import app; print(app.title)"` - passed.
- `python -m pytest backend/tests/test_rag_generation.py backend/tests/test_saas_agent_route_deck.py backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 33 passed.
- `npm run build` in `frontend/` - passed.

## Slice 7 Memory Validation

- Memory embeddings fall back to deterministic local vectors when no OpenAI key
  is configured.
- Chat handles direct `remember ...` requests without relying on model tool
  selection.
- Chat handles direct recall prompts such as `what do you remember`.
- Members can create memories through `POST /agent/memories`.
- Owners/admins can inspect and delete memories in Sessions & Memory.
- Memory save/recall/list/delete remains scoped by `saas_agent_id`.

Checks run:

- `python -c "from backend.main import app; print(app.title)"` - passed.
- `python -m pytest backend/tests/test_memory_service.py backend/tests/test_rag_generation.py backend/tests/test_saas_agent_route_deck.py backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 34 passed.
- `npm run build` in `frontend/` - passed.

## Slice 8 Sandbox Learning Validation

- Failed execution traces can propose learning candidates.
- Missing-input traces can propose learning candidates.
- Learning candidates have proposed/approved/rejected/active state.
- Learn panel lists candidates and exposes approve/reject controls.
- Approved/active learning candidates add ranking hints to generated REST tool
  selection.

Checks run:

- `python -c "from backend.main import app; print(app.title)"` - passed.
- `python -m pytest backend/tests/test_learning_service.py backend/tests/test_memory_service.py backend/tests/test_rag_generation.py backend/tests/test_saas_agent_route_deck.py backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 36 passed.
- `npm run build` in `frontend/` - passed.

## Slice 9 QA And Observability Validation

- QA scenario catalog includes `rag_memory_learning_surfaces`.
- QA scenario action coverage remains synchronized with the frontend QA runner.
- Existing QA gates cover RouteDeck state, action availability, SaaS Agent view,
  catalog counts, API response status, tool calls, visible text, and console errors.

Checks run:

- `python -c "from backend.main import app; print(app.title)"` - passed.
- `python -m pytest backend/tests/test_learning_service.py backend/tests/test_memory_service.py backend/tests/test_rag_generation.py backend/tests/test_saas_agent_route_deck.py backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 36 passed.
- `npm run build` in `frontend/` - passed.

## Post-Implementation Essential Validation - 2026-05-14 06:16

Scope:

- Validate the running Docker app, not only local unit tests.
- Exercise the actual create/connect/activate/catalog/RAG/memory/execution/RouteDeck path.
- Run the embedded browser QA agent and an independent read-only QA agent.

Fixes made during validation:

- Added missing Learn view support to frontend QA/view typing and activity icon mapping.
- Updated the RAG/memory/learning QA scenario to select the Memories tab before checking `Save memory`.
- Added a local/dev startup migration for existing databases that still had renamed `workspace_id` columns.
- Eager-loaded `Connection.activation_state` and `Connection.credentials` in `GET /connections` to fix the async SQLAlchemy `MissingGreenlet` runtime failure after activation.

Checks run after fixes:

- `GET http://localhost:8085/api/health` - passed.
- `GET http://localhost:3007` - passed.
- `python -c "from backend.main import app; print(app.title)"` - passed.
- `python -m backend.services.route_deck.validate` - passed.
- `python -m pytest backend/tests/test_learning_service.py backend/tests/test_memory_service.py backend/tests/test_rag_generation.py backend/tests/test_saas_agent_route_deck.py backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` - 36 passed.
- `npm run type-check` in `frontend/` - passed.
- `npm run build` in `frontend/` - passed with the existing Vite chunk-size warning.
- Direct live API e2e against Docker backend and Petstore OpenAPI - passed:
  - QA reset/login.
  - initial SaaS Agent RouteDeck at `needs_connection`.
  - REST connection create.
  - activation SSE complete with ready status.
  - catalog has 3 entities and 19 actions.
  - generated RAG has 1 document and 3 chunks.
  - memory create/list works.
  - chat stream emits tool execution events.
  - SaaS Agent RouteDeck context reaches `result_review`.
- Connection-list regression after activation - passed:
  - `GET /api/saas-agents/{id}/connections` returns 1 ready connection, 19 tools, and 19 action nodes.
- Embedded browser QA `rag_memory_learning_surfaces` - passed with zero console errors.
- Embedded browser QA `connection_catalog_preview` - passed with zero console errors after the eager-load fix.
- Independent QA agent - passed health, frontend reachability, Docker stack, full backend test suite, frontend type-check, authenticated surface smoke, QA panel visibility, OpenAPI endpoint surface check, Petstore activation, generated RAG, and memory creation.

Residual gaps:

- Live Medusa Storefront/Admin preview and activation are still pending against an available Medusa target.
- Production-grade migration framework is still pending; the current migration is only a local/dev continuity guard for renamed workspace columns.
- Browser validation was headless QA/smoke, not visual design review.

## Future Automated Coverage

- Browser smoke for `/agents/:saasAgentId`.
- RouteDeck contract/browser tests for SaaS Agent runtime snapshots.
- QA scenarios for Medusa Storefront Agent and Medusa Admin Agent as separate
  SaaS Agents.
- Live browser proof for Medusa Storefront/Admin preview, activation, generated
  RAG, read execution, memory save/recall, and learning proposal.
