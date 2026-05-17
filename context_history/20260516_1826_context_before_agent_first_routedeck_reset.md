# SaaStoAgent v0.1 Context

Last Updated: May 16, 2026 17:15
Project: SaaStoAgent v0.1
Status: Graph-first reset spine implemented. The backend app graph is now the target navigation and capability authority, rooted at `home`, with RouteDeck snapshots driving frontend routes, actions, context lens, evidence, and surfaces. Existing SaaS Agent domain services remain in use behind graph handlers. Final hardcoding purge and graph-native QA are still pending.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Live State

- SaaStoAgent frontend dev default: `http://localhost:3000`
- SaaStoAgent backend health: `/api/health`
- Unified app graph package: `backend/services/app_graph/`
- Unified app graph routes: `backend/routes/app_graph.py`
- Frontend graph shell: `frontend/src/components/appGraph/AppGraphShell.tsx`
- RouteDeck framework project: `../routedeck/`
- Existing SaaS Agent domain services:
  - CRUD/stats: `backend/routes/saas_agents.py`
  - connections/catalog: `backend/routes/connections.py`, `backend/services/catalog.py`
  - activation: `backend/services/discovery/activation.py`
  - execution: `backend/services/agent/rest_operator.py`
  - RAG: `backend/services/agent/rag_service.py`
  - memory: `backend/services/agent/memory_service.py`
  - learning: `backend/services/agent/learning_service.py`
- Active reset plan: `plans/saastoagent_v0_1_graph_first_reset_plan.md`
- Foundation plan retained for history: `plans/saastoagent_v0_1_saas_agent_foundation_plan.md`

## Product Contract

- `SaaSAgent` is the product and domain authority.
- No workspace/grouping parent exists.
- Medusa Storefront and Medusa Admin should be separate SaaS Agents.
- Every SaaS Agent owns its API connections, generated actions/tools, execution traces, RAG corpus, memory, sandbox learnings, QA evidence, and channels.
- One unified app graph now owns navigation and capability eligibility across entry, SaaS Agent setup, execution, knowledge, memory, learning, QA, and recovery.

## Current Implemented Runtime

- Backend graph endpoints:
  - `GET /api/app/graph/snapshot`
  - `POST /api/app/graph/turn`
  - `POST /api/app/graph/action`
- App graph nodes:
  - `home`
  - `auth_sign_in`
  - `auth_register`
  - `saas_agent_select`
  - `saas_agent_create`
  - `agent_home`
  - `connection_configure`
  - `schema_preview`
  - `catalog_activation`
  - `catalog`
  - `entities`
  - `actions`
  - `execution_planning`
  - `needs_input`
  - `approval_required`
  - `executing`
  - `result_review`
  - `knowledge`
  - `memory`
  - `learning`
  - `qa`
  - `recovery`
- Frontend graph routes:
  - `/app/home`
  - `/app/:nodeId`
  - `/app/agents/:saasAgentId`
  - `/app/agents/:saasAgentId/:nodeId`
- Compatibility routes:
  - `/` redirects to `/app/home`
  - `/login` redirects to `/app/auth_sign_in`
  - `/register` redirects to `/app/auth_register`
  - `/agents/:saasAgentId` hydrates graph context
- `AppGraphShell` renders:
  - graph-provided persistent rail actions
  - graph-provided current node and reachable nodes
  - graph-provided action dock/forms
  - central graph chat backed by `/api/app/graph/turn`
  - graph-provided active surface renderer
  - graph-provided context lens
  - graph-provided evidence/diagnostics drawer
- Free text no longer uses English phrase-list routing in the new app graph. Until a structured model router is added, graph turns ask the user to choose eligible typed RouteDeck actions.
- Existing `OperatorGateway`, `operatorExperience`, selected-agent snapshot RouteDeck, and some panel-local controls still exist as compatibility/renderer debt. They are no longer mounted by the primary `/app/...` routes.

## Active Implementation Direction

1. Delete or rewrite the legacy frontend workflow ownership code after graph-native renderers fully cover it:
   - `frontend/src/components/OperatorGateway.tsx`
   - `frontend/src/lib/operatorExperience.ts`
   - local capability registry authority in `saasAgentStore.ts`
   - panel-local route/view jumps
2. Replace `backend/services/saas_agent_route_deck.py` snapshot inference with wrappers over the unified app graph.
3. Convert QA from label-driven scripts to graph-authored node/action/evidence scenarios.
4. Add structured LLM routing constrained to known RouteDeck node/action ids.
5. Add optional SSE graph turn streaming.
6. Run live Medusa Storefront/Admin preview and activation verification when the Medusa target is available.

## Slice Operating Rule

Each slice must be implemented, tested, repaired if broken, then documented before continuing to the next slice. The mini closeout follows `work_prompt.md` style without stopping the session:

- log in `logs/`
- checkpoint in `context_checkpoints/`
- archive `context.md` to `context_history/` when materially changed
- rewrite `context.md`
- update active plan
- update `SYSTEM_FLOW_INDEX.md` when flows changed
- update or add `test_index/`
- add ADR/docs/architecture only when needed

## Known Gaps

- The graph-first reset is a working spine, not the final purge.
- Legacy selected-agent RouteDeck and OperatorGateway files remain as compatibility debt.
- QA still needs graph-authored scenario contracts.
- Structured LLM routing is not implemented yet.
- Live Medusa Storefront/Admin preview and activation have not been verified in this pass.
- Production migration hardening remains intentionally out of scope.

## Verification

- `python -c "from backend.main import app; print('routes', len(app.routes)); from backend.services.app_graph import validate_app_graph_manifest; print(validate_app_graph_manifest())"`: passed.
- `python -c "import asyncio; from backend.services.app_graph.runtime import app_graph_runtime; from backend.core.schemas import AppGraphRequest; r=asyncio.run(app_graph_runtime.snapshot(request=AppGraphRequest(node_id='home'), user=None, db=None)); print(r.state.node, r.active_surface.renderer, [a.id for a in r.available_actions])"`: passed and returned `home home ['auth.sign_in', 'auth.register']`.
- `$env:PYTHONPATH='.'; pytest backend/tests/test_app_graph_contract.py backend/tests/test_route_deck_contract.py -q`: 15 passed.
- `$env:PYTHONPATH='.'; pytest backend/tests -q`: 40 passed.
- `npm run type-check` in `frontend/`: passed.
- `npm run build` in `frontend/`: passed.
- Playwright rendered smoke against `http://localhost:3008/app/home` with mocked graph snapshot/action responses: passed. It found the RouteDeck header, context lens, `node: home` strip, `auth.sign_in` action, and `saas_agent.create` form with zero console errors.
- Playwright rendered smoke against Vite plus Docker backend after restoring central graph chat: passed. It found the central chat, sent `hello graph`, received the structured-action fallback from `/api/app/graph/turn`, and recorded zero console/request failures.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Active reset plan: `plans/saastoagent_v0_1_graph_first_reset_plan.md`
- Foundation plan: `plans/saastoagent_v0_1_saas_agent_foundation_plan.md`
- Full app graph ADR: `decisions/ADR-011-full-application-graph-ownership.md`
- Domain ADR: `decisions/ADR-010-saas-agent-domain-authority.md`
- RouteDeck ADRs: `decisions/ADR-007-routedeck-framework-contract.md`, `decisions/ADR-008-live-entry-streaming-contract.md`, `decisions/ADR-009-langgraph-owned-entry-runtime.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_16-05-2026-05-15PM.md`
