# Context Checkpoint — 2026-05-07 12:00

## Project State

**SaaStoAgent v0.1 — Entry Flow UX polish complete.**

Backend-owned entry runtime (SSE streaming, action cards) was built in prior sessions. This session polished the UX: action cards are now inline chat chips, the chip click no longer injects a fake user message, and the bootstrap fallback is resilient to session loss with a clean plain-English message.

---

## Runtime Status

| Service  | Host Port | Status      |
|----------|-----------|-------------|
| Frontend | 3005      | Running, Vite dev (stale — needs force-recreate to see latest changes) |
| Backend  | 8085      | Running     |
| DB       | 5435      | Running     |

> **Note:** Frontend container needs `docker compose up --force-recreate frontend` to serve the chip redesign changes from disk.

---

## What Is True Right Now

### Entry / Auth Flow

- Route `/login` → `OperatorGateway initialIntent="login"` → hits `/api/entry/stream` SSE
- Route `/register` → `OperatorGateway initialIntent="register"`
- Route `/` → `OperatorGateway` (no initial intent) → shows intent chips
- Entry graph nodes: `bootstrap → intent → display_name → email → password → workspace_confirm/select → operator_ready`
- Session state persisted in DB via `EntrySession.current_state`; session ID in `sta_v01_entry_session` cookie
- Action cards are inline chat chips, styled like `FollowUpChips`
- Chip click: fires `selected_action_id` directly, no fake user bubble
- Bootstrap fallback message: "Sign in or create a new account?"
- `bootstrap_node` is session-loss resilient: routes `intent.sign_in` / `intent.register` directly even without a persisted session

### Workspace Flow

- After `operator_ready`: `WorkspaceShell` mounts inline inside `OperatorGateway`
- Real `AgentChat` with SSE streaming, file attachments, follow-up chips, tool cards, citations

### Key Files (Entry Flow)

| File | Role |
|------|------|
| `backend/routes/entry.py` | `/api/entry/stream` SSE + `/api/entry/turn` JSON |
| `backend/services/entry_runtime/graph_executor.py` | LangGraph executor wiring |
| `backend/services/entry_runtime/stage_auth.py` | bootstrap, intent, display_name, email, password nodes |
| `backend/services/entry_runtime/stage_workspace.py` | workspace_confirm, workspace_job, workspace_select, operator_ready |
| `backend/services/entry_runtime/stage_io.py` | Stage execution, artifact/output persistence, SSE emit |
| `backend/services/entry_runtime/ui_actions.py` | Action chip generators per stage |
| `backend/core/schemas/entry.py` | EntryActionCard, EntryGraphTurnRequest/Response |
| `frontend/src/components/OperatorGateway.tsx` | SSE consumer, state machine, message thread |
| `frontend/src/components/entry/EntryActionCards.tsx` | Inline chip component |

---

## Known Gaps

- `STA_OPENAI_API_KEY` still not set → agent chat / embedding calls cannot be smoke-tested
- Frontend container stale — force-recreate needed
- Workspace confirm action chips (launch button) not yet implemented
- Workspace select chips for small lists not yet implemented
- `web_search` tool is still a placeholder

---

## Immediate Next Step

1. `docker compose up --force-recreate frontend` from `saastoagent-v0.1/`
2. Validate chip UX in browser: chips appear in thread, clicking routes immediately
3. Implement workspace confirm chip (launch button)
4. Set `STA_OPENAI_API_KEY` and run authenticated agent chat smoke test
