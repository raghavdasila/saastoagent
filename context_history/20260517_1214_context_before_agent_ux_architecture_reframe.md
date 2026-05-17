# SaaStoAgent v0.1 Context

Last Updated: May 16, 2026 18:26
Project: SaaStoAgent v0.1
Status: Agent-first RouteDeck reset implemented on top of the unified backend app graph. The product shell is now chat-first, RouteDeck/graph internals are hidden behind diagnostics, and free-text turns use an app-owned router adapter contract instead of visible typed action-id prompts.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Live State

- SaaStoAgent frontend dev default: `http://localhost:3000`
- SaaStoAgent backend health: `/api/health`
- Unified app graph package: `backend/services/app_graph/`
- App-owned turn router: `backend/services/app_graph/router.py`
- Unified app graph routes: `backend/routes/app_graph.py`
- Agent-first frontend shell: `frontend/src/components/appGraph/AppGraphShell.tsx`
- RouteDeck framework project: `../routedeck/`
- Active reset plan: `plans/saastoagent_v0_1_graph_first_reset_plan.md`
- Current guardrail tests: `backend/tests/test_app_graph_contract.py`

## Product Contract

- `SaaSAgent` is the product and domain authority.
- No workspace/grouping parent exists.
- Medusa Storefront and Medusa Admin should be separate SaaS Agents.
- Every SaaS Agent owns its API connections, generated actions/tools, execution traces, RAG corpus, memory, sandbox learnings, QA evidence, and channels.
- One unified backend app graph owns navigation and capability eligibility across entry, SaaS Agent setup, execution, knowledge, memory, learning, QA, and recovery.
- RouteDeck is infrastructure: it bridges backend state to surfaces, actions, evidence, and diagnostics. It is not product copy and it does not own model credentials.

## Current Implemented Runtime

- Backend graph endpoints:
  - `GET /api/app/graph/snapshot`
  - `POST /api/app/graph/turn`
  - `POST /api/app/graph/action`
- App graph nodes:
  - `home`, `auth_sign_in`, `auth_register`, `saas_agent_select`, `saas_agent_create`, `agent_home`
  - `connection_configure`, `schema_preview`, `catalog_activation`, `catalog`, `entities`, `actions`
  - `execution_planning`, `needs_input`, `approval_required`, `executing`, `result_review`
  - `knowledge`, `memory`, `learning`, `qa`, `recovery`
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
- `AppGraphShell` now renders:
  - full-width central Agent desk chat
  - natural-language next-step actions/forms from backend state
  - active work surfaces for home, agent overview, connection, schema preview, catalog, entities, actions, knowledge, memory, learning, and QA
  - quiet `Working on` context lens
  - closed diagnostics panel that exposes graph/RouteDeck internals only when opened

## Router Contract

- RouteDeck core remains deterministic and model-free.
- `AppGraphTurnRouter` is app-owned and optional.
- Router providers:
  - `disabled`: default; asks a natural clarification and shows visible next-step labels
  - `openai`: optional, app-supplied `STA_OPENAI_API_KEY` and `STA_APP_GRAPH_ROUTER_MODEL`
  - `ollama`: optional, app-supplied `STA_APP_GRAPH_ROUTER_OLLAMA_URL` and model
- Router decisions are structured as intent, action id, node id, slots, confidence, clarification, provider, and model.
- The backend graph still validates every action against current eligibility before execution.
- Required action fields must be present before a routed action can execute.

## Active Implementation Direction

1. Remove legacy `OperatorGateway`, selected-agent snapshot RouteDeck, and local capability registry after graph-native renderers fully cover their remaining panels.
2. Convert QA from label-driven scripts to graph-authored node/action/evidence scenarios.
3. Add SSE streaming for live graph turns.
4. Run live Medusa Storefront/Admin preview and activation verification when the Medusa target is available.
5. Harden migrations and production approval policy after the working graph spine stabilizes.

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

- Legacy compatibility files still exist and are not mounted by the primary `/app/...` routes.
- QA still needs graph-authored scenario contracts beyond the current guardrails.
- Live Medusa Storefront/Admin preview and activation have not been verified in this pass.
- Production migration hardening remains intentionally out of scope.

## Verification

- `$env:PYTHONPATH='.'; pytest backend/tests/test_app_graph_contract.py -q`: 8 passed.
- `$env:PYTHONPATH='.'; pytest backend/tests -q`: 44 passed.
- `python -m backend.services.route_deck.validate`: passed.
- `npm run type-check` in `frontend/`: passed.
- `npm run build` in `frontend/`: passed.
- Playwright smoke against `http://localhost:3010/app/home`: passed. Agent desk and Working On context rendered, sending `hi` did not expose RouteDeck/graph/action-id product copy, Diagnostics revealed RouteDeck internals only after opening, and console/request failures were zero.
- Follow-up Playwright smoke against `http://localhost:3010/app/home`: passed. A greeting receives a natural assistant response, anonymous Home no longer renders the empty SaaS Agent list below chat, context says `Starting a SaaS Agent`, and console/request failures were zero.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Active reset plan: `plans/saastoagent_v0_1_graph_first_reset_plan.md`
- Full app graph ADR: `decisions/ADR-011-full-application-graph-ownership.md`
- Domain ADR: `decisions/ADR-010-saas-agent-domain-authority.md`
- RouteDeck ADRs: `decisions/ADR-007-routedeck-framework-contract.md`, `decisions/ADR-008-live-entry-streaming-contract.md`, `decisions/ADR-009-langgraph-owned-entry-runtime.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_16-05-2026-6-26PM.md`
