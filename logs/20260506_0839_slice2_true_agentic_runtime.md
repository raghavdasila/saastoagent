# SaaStoAgent v0.1 — Slice 2 True-Agentic Runtime

Date: 2026-05-06
Project: `agent-lab-powered-projects/saastoagent-v0.1`

## Outcome

Slice 2 is implemented in code and now boots locally as a real agent runtime rather than the old mock shell.

Validated locally:
- `docker compose config` resolves cleanly.
- DB starts successfully on `pgvector/pgvector:pg17`.
- Backend health returns `{"status":"ok"}` on `http://localhost:8085/api/health`.
- Frontend serves successfully on `http://localhost:3005` and renders the auth flow.

Not yet validated end-to-end:
- Real agent chat / embeddings / RAG answer generation, because `STA_OPENAI_API_KEY` is not set in the current runtime.

## Key Changes

### Backend
- Added workspace-scoped agent models in public schema:
  - `AgentSession`
  - `AgentMessage`
  - `AgentDocument`
  - `AgentDocumentChunk`
  - `AgentMemory`
- Added agent schemas and SSE protocol helpers.
- Added LangGraph-backed services:
  - `chat_service.py`
  - `graph_builder.py`
  - `rag_service.py`
  - `memory_service.py`
- Added agent tools:
  - `rag_search`
  - `read_file`
  - `save_memory`
  - `recall_memory`
  - `open_link`
  - `web_search` placeholder
- Added workspace agent routes under `/api/workspaces/{workspace_id}/agent/...`.
- Added admin session delete route to match the admin UI.
- Enabled `vector` extension creation at startup.

### Frontend
- Replaced the stub chat path with a real SSE-driven `AgentChat`.
- Added agent UI components for:
  - streamed chat messages
  - reasoning display
  - tool cards
  - source citations
  - follow-up chips
  - chat input with upload shortcut
- Added `AttachmentsPanel` for workspace documents.
- Added `AdminPanel` for:
  - stats
  - session inspection/deletion
  - document list
  - document chunk inspection
  - memory list/deletion
- Added `attachments` and `admin` views to the activity bar.
- Added `clsx`, `tailwind-merge`, `react-markdown`, and `remark-gfm`.

## Runtime Fixes Applied During Validation

### Postgres init failure
Symptom:
- `initdb: error: directory "/var/lib/postgresql/data" exists but is not empty`

Fix:
- Set `PGDATA=/var/lib/postgresql/data/pgdata`
- Switched the volume name from `saastoagent_v0_1_pgdata18` to `saastoagent_v0_1_pgdata17`

Result:
- DB initializes cleanly and reaches healthy state.

### Frontend dependency mismatch
Symptom:
- Vite failed to resolve `clsx`, `react-markdown`, and related newly added packages because the container used a stale `node_modules` volume.

Fix:
- Ran `docker compose exec frontend npm install`

Result:
- Frontend serves again and the login page renders.

## Remaining Gaps

- `STA_OPENAI_API_KEY` must be set before true chat/RAG/memory behavior can be fully smoke-tested.
- `web_search` is still placeholder-only.
- `ConnectSetupView` is still UI-only.

## Suggested Next Validation

1. Set `STA_OPENAI_API_KEY` in the environment.
2. Restart the stack.
3. Register and sign in.
4. Create or enter a workspace.
5. Upload a PDF or markdown file.
6. Ask a question about the uploaded document.
7. Save a memory and recall it.
8. Verify the admin panel shows sessions, docs, chunks, and memories.
