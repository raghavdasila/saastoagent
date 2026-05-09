# SaaStoAgent v0.1 Context — Archived 2026-05-07

_This is an archive of context.md as of May 6, 2026 (before the entry flow UX polish session)._

---

# SaaStoAgent v0.1 Context

Last Updated: May 6, 2026
Project: SaaStoAgent v0.1
Status: Slice 2 implemented. The workspace now has a real agent runtime with SSE chat, uploaded-document RAG, per-workspace memory, attachments, and an admin surface. Auth and first-workspace onboarding are also conversational now. Local stack boots cleanly. Full agent-response smoke testing is still blocked until `STA_OPENAI_API_KEY` is set.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

---

## Live State

- Docker Compose runtime is up locally.
- Frontend renders at `http://localhost:3005` and currently lands on `/login` when unauthenticated.
- Backend health at `http://localhost:8085/api/health` returns `{"status":"ok"}`.
- Database is running on `5435` with `pgvector/pgvector:pg17`.
- Postgres init failure was fixed by setting `PGDATA=/var/lib/postgresql/data/pgdata` and rotating to a fresh volume name `saastoagent_v0_1_pgdata17`.
- Frontend dependency volume was refreshed with `docker compose exec frontend npm install` after adding `clsx`, `tailwind-merge`, `react-markdown`, and `remark-gfm`.

## Current Product Shape

- Root `/` — Agent Desk with auth + workspace entry flow.
- `/login` and `/register` now render a conversational auth desk instead of plain forms.
- Workspace `/w/:id` — `ActivityBar` + full-width `AgentCanvas`.
- Chat view — real `AgentChat`, not the old stub. It uses workspace-scoped SSE chat, session history, file upload shortcut, follow-ups, tool cards, source citations, and streamed reasoning display.
- Attachments view — upload/list/delete workspace documents for RAG.
- Admin view — workspace-owner/admin stats, session inspection and deletion, document list with chunk inspector, and memory list with deletion.
- Setup view — `ConnectSetupView` remains UI-only for the REST onboarding slice.
- Entities / Actions / QA remain locked pending later slices.

## Backend Runtime Shape

- Agent endpoints live under `/api/workspaces/{workspace_id}/agent/...`.
- Public-schema models added: `AgentSession`, `AgentMessage`, `AgentDocument`, `AgentDocumentChunk`, `AgentMemory`.
- LangGraph runtime is wired through `graph_builder.py` and `chat_service.py`.
- RAG is backed by uploaded docs + pgvector embeddings.
- Memory is workspace-scoped and embedding-backed.
- Admin routes now include per-session delete and document chunk inspection.

## Frontend Runtime Shape

- New agent UI lives under `frontend/src/components/agent/`.
- SSE client hook: `frontend/src/hooks/useSSEChat.ts`.
- Agent types: `frontend/src/types/agent.ts`.
- Utility merge helper: `frontend/src/lib/cn.ts`.
- `AgentCanvas` now routes `chat`, `attachments`, and `admin` to live components instead of the stub path.
- `workspaceStore.ts` now includes `attachments` and `admin` views.
- Zero-workspace dashboard onboarding is now an inline conversational launch pad; the old workspace creation modal has been removed from the frontend runtime.

## Known Gaps

- `STA_OPENAI_API_KEY` is empty in the current runtime, so real agent chat / embedding calls cannot be fully smoke-tested yet.
- `web_search` is still a placeholder tool and does not call a real provider.
- `ConnectSetupView` is still not wired to real connection activation.
- No authenticated RAG/memory transcript has been recorded yet in this session because the OpenAI key is still missing.

## Immediate Next Step

Set `STA_OPENAI_API_KEY`, restart the stack, then run an authenticated smoke test:
1. Register / sign in
2. Create or enter a workspace
3. Upload a document
4. Ask a RAG-backed question
5. Save and recall memory
6. Inspect sessions/documents/memories from Admin

## References

- Vision: `critical_prompt.md`
- Plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- ADR-001: `decisions/ADR-001-recenter-agentic-product-boundary.md`
- ADR-002: `decisions/ADR-002-agent-first-interface.md`
- Latest logs: `logs/20260506_0839_slice2_true_agentic_runtime.md`, `logs/20260506_0901_agentic_auth_and_launchpad.md`
- Pipeline: `context_pipeline.md`
