# Context Checkpoint - 2026-05-16 05:15 PM

The graph-first reset spine is implemented.

- New ADR: `decisions/ADR-011-full-application-graph-ownership.md`
- Active reset plan: `plans/saastoagent_v0_1_graph_first_reset_plan.md`
- Backend graph package: `backend/services/app_graph/`
- Backend graph routes: `backend/routes/app_graph.py`
- Frontend graph shell: `frontend/src/components/appGraph/AppGraphShell.tsx`
- Frontend graph routes: `/app/home`, `/app/:nodeId`, `/app/agents/:saasAgentId`, `/app/agents/:saasAgentId/:nodeId`
- Test index: `test_index/graph-first-app-contract.md`

Validation:

- App graph import/manifest smoke: passed.
- Focused backend graph/RouteDeck tests: 15 passed.
- Full backend tests: 40 passed.
- Frontend type-check: passed.
- Frontend build: passed.
- Playwright rendered smoke against the new graph shell with a mocked graph snapshot: passed with zero console errors.

Residual work:

- Remove or rewrite legacy `OperatorGateway`, `operatorExperience`, local capability registry, selected-agent snapshot RouteDeck inference, and label-driven QA after graph-native replacements cover their behavior.
- Add structured LLM router and optional SSE graph turn stream.
