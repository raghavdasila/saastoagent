# SaaStoAgent v0.1 Context

Last Updated: May 7, 2026
Project: SaaStoAgent v0.1
Status: Slice 2 implemented. Entry flow UX polished — action chips integrated inline into the chat thread, bootstrap resilient to session loss, no fake user bubbles on chip click. Agent chat + RAG smoke test still blocked until `STA_OPENAI_API_KEY` is set.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

---

## Live State

- Docker Compose runtime is up locally.
- Frontend at `http://localhost:3005` — **stale build**: disk has chip redesign but container needs `docker compose up --force-recreate frontend` to reflect it.
- Backend at `http://localhost:8085/api/health` → `{"status":"ok"}`.
- Database on `5435` with `pgvector/pgvector:pg17`.

## Current Product Shape

- Root `/` — `OperatorGateway` (no initial intent) — shows intent chip prompt.
- `/login` — `OperatorGateway initialIntent="login"` — goes straight to email node.
- `/register` — `OperatorGateway initialIntent="register"` — goes straight to display_name node.
- Entry flow is a backend-owned LangGraph state machine served over SSE (`/api/entry/stream`).
- Action chips appear inline in the message thread after each assistant message; they clear on the next turn.
- Workspace `/w/:id` — `ActivityBar` + full-width `AgentCanvas`.
- Chat — real SSE agent chat with RAG, memory, follow-ups, tool cards, citations.
- Attachments — upload/list/delete workspace documents for RAG.
- Admin — session inspection + deletion, document chunk inspector, memory list.
- Setup — `ConnectSetupView` is UI-only (not wired to backend yet).
- Entities / Actions / QA — locked pending later slices.

## Entry Flow Architecture

```
/api/entry/stream (SSE)
  └─ run_entry_turn()
       └─ LangGraph: bootstrap → intent → display_name → email → password
                                                                → workspace_confirm
                                                                → workspace_select
                                                                → operator_ready
```

- Session state: `EntrySession.current_state` in DB, ID in `sta_v01_entry_session` cookie.
- Action chips: `EntryActionCard` schema; backend emits via `stage_completed.output.available_actions`.
- Frontend: `OperatorGateway.tsx` (SSE consumer) + `EntryActionCards.tsx` (chip component).

## Backend Runtime Shape

- Agent endpoints: `/api/workspaces/{workspace_id}/agent/...`
- Public-schema models: `AgentSession`, `AgentMessage`, `AgentDocument`, `AgentDocumentChunk`, `AgentMemory`
- LangGraph: `graph_builder.py` + `chat_service.py`
- RAG: pgvector-backed uploaded docs
- Memory: workspace-scoped embedding-backed

## Known Gaps

- `STA_OPENAI_API_KEY` not set — agent chat / embeddings untested
- Frontend container stale — needs force-recreate
- Workspace confirm chip (launch button) not yet implemented
- Workspace select chips (small list) not yet implemented
- `web_search` still a placeholder
- `ConnectSetupView` not wired to real activation

## Immediate Next Steps

1. `docker compose up --force-recreate frontend` — validate chip UX in browser
2. Implement workspace confirm chip (launch action)
3. Set `STA_OPENAI_API_KEY`, restart, run authenticated smoke test:
   - Register / sign in → create workspace → upload doc → RAG question → save memory → Admin inspection

## References

- Vision: `critical_prompt.md`
- Plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- ADR-001: `decisions/ADR-001-recenter-agentic-product-boundary.md`
- ADR-002: `decisions/ADR-002-agent-first-interface.md`
- Latest logs: `logs/20260507_1200_entry_flow_ux_polish.md`
- Pipeline: `context_pipeline.md`