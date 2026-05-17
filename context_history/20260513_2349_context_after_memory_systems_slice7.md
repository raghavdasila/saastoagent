# SaaStoAgent v0.1 Context

Last Updated: May 13, 2026 23:49
Project: SaaStoAgent v0.1
Status: Slices 0-7 of the SaaS Agent foundation reset are complete. Slice 7 adds explicit SaaS-Agent-scoped memory save/recall/inspection, deterministic local memory embeddings, direct chat memory commands, and manual memory save/delete UI. Live Medusa preview/activation verification is still pending.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Live State

- SaaStoAgent frontend: `http://localhost:3007`
- SaaStoAgent backend health: `http://localhost:8085/api/health`
- RouteDeck framework project: `../routedeck/`
- SaaStoAgent RouteDeck product adapter/catalog: `backend/services/route_deck/`
- SaaS Agent RouteDeck runtime: `backend/services/saas_agent_route_deck.py`
- Generated REST execution surface: `backend/services/agent/rest_operator.py`, `backend/core/models/agent.py`
- SaaS Agent RAG generation: `backend/services/agent/rag_service.py`
- SaaS Agent memory: `backend/services/agent/memory_service.py`, `frontend/src/components/agent/AdminPanel.tsx`
- Active plan: `plans/saastoagent_v0_1_saas_agent_foundation_plan.md`
- Superseded plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`

## Product Contract

- `SaaSAgent` is now the product and domain authority.
- No workspace/grouping parent exists in this foundation pass.
- Medusa Storefront and Medusa Admin should be separate SaaS Agents.
- Every SaaS Agent owns its own RouteDeck runtime snapshot, API connections, generated actions/tools, execution traces, RAG corpus, memory, sandbox learnings, QA evidence, and channels.
- The app has two RouteDeck layers:
  - Entry RouteDeck: public entry, auth, SaaS Agent creation/selection, and handoff.
  - SaaS Agent RouteDeck: selected-agent connection setup, schema preview, catalog activation, action planning, approval, execution, result review, memory, learning, and QA.

## Current Implemented Runtime

- Frontend routes are `/`, `/login`, `/register`, and `/agents/:saasAgentId`.
- Backend SaaS Agent CRUD/stats routes are `/api/saas-agents`.
- Backend connection/catalog/chat/admin/document routes are scoped by `saas_agent_id`.
- Entry/auth/SaaS Agent setup handoff executes through `backend/services/entry_runtime/graph_executor.py`.
- Entry RouteDeck nodes are `bootstrap`, `intent`, `display_name`, `email`, `password`, `saas_agent_select`, `saas_agent_job`, `saas_agent_confirm`, `setup_intro`, `connection_confirm`, and `operator_ready`.
- RouteDeck framework lane contract now uses `saas_agent` instead of `workspace`.
- Frontend state/types/stores use SaaS Agent naming (`useSaaSAgentStore`, `SaaSAgent`, `SaaSAgentStats`).
- REST/OpenAPI activation, generated Actions/Entities canvases, first-pass read-safe generated REST tool execution, structured execution traces, and approval stop/resume controls are implemented against the renamed SaaS Agent model.
- Dashboard launch presets create separate `Medusa Storefront Agent` and `Medusa Admin Agent` SaaS Agents.
- Connections has Medusa Storefront/Admin API presets using `VITE_MEDUSA_API_BASE_URL` or `http://localhost:9000`.
- Backend exposes `GET /api/saas-agents/{saas_agent_id}/route-deck` for selected-agent RouteDeck manifest, runtime snapshot, and context.
- Frontend RouteDeck widget switches from Entry RouteDeck to SaaS Agent RouteDeck in operator mode.
- Context lens/status strip shows the selected SaaS Agent, current SaaS Agent RouteDeck node, working-on summary, and connection/action/tool counts.
- Generated REST execution now persists `agent_execution_traces` with candidate/action/tool, inputs, missing inputs, risk, approval state, result, error, and RouteDeck node.
- Risky generated REST actions stop at `approval_required` and can resume with `approve <trace>` or cancel with `cancel <trace>`.
- SaaS Agent RouteDeck current node now reflects latest execution trace states: `needs_input`, `approval_required`, `executing`, and `result_review`.
- RAG ingestion can generate scoped markdown knowledge documents from generated API catalog and recent execution traces.
- RAG embeddings use OpenAI when configured and deterministic local vectors when no OpenAI key is present.
- Activation refreshes generated catalog RAG after tools are created; execution refreshes trace RAG after result finalization.
- Knowledge panel exposes `Generate catalog RAG`.
- Memory save/recall works without relying on the LLM tool path for direct commands such as `remember ...` and `what do you remember`.
- Members can create memories through `POST /api/saas-agents/{saas_agent_id}/agent/memories`; owners/admins can inspect/delete them in Sessions & Memory.
- Memory embeddings use OpenAI when configured and deterministic local vectors when no OpenAI key is present.

## Active Implementation Direction

1. Continue Slice 8: add sandbox learning candidates from failures, corrections, and repeated missing inputs.
2. Continue Slice 9: add QA/observability coverage and final closeout.
3. Run live Medusa Storefront/Admin preview and activation verification when the Medusa target is available.

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

- Storefront/Admin preview and activation have not been verified against a live Medusa target in this run.
- Sandbox learning is not yet integrated into execution refinement.
- PyMuPDF was installed locally during this run to clear the existing `fitz` import blocker.

## Verification

- `python -m backend.services.route_deck.validate`: passed.
- `python -m pytest backend/tests/test_memory_service.py backend/tests/test_rag_generation.py backend/tests/test_saas_agent_route_deck.py backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py`: 34 passed.
- `npm run build` in `frontend/`: passed.
- `python -m compileall backend`: passed before the frontend rename.
- `python -c "from backend.main import app; print(app.title)"`: passed after local PyMuPDF install.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Active plan: `plans/saastoagent_v0_1_saas_agent_foundation_plan.md`
- Superseded plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- Domain ADR: `decisions/ADR-010-saas-agent-domain-authority.md`
- RouteDeck ADRs: `decisions/ADR-007-routedeck-framework-contract.md`, `decisions/ADR-008-live-entry-streaming-contract.md`, `decisions/ADR-009-langgraph-owned-entry-runtime.md`
- Latest context archive: `context_history/20260513_2230_context_before_saas_agent_backend_frontend_rename.md`
