# Log - 2026-05-08 2:29 PM - Unified Main-Layout Operator Experience

## Accomplished

- Reworked routing so `/`, `/login`, `/register`, and `/w/:workspaceId` use the same `OperatorGateway` shell.
- Replaced the visual handoff from entry into `WorkspaceShell` with an in-place mode switch inside the icon-sidebar + central-chat layout.
- Added unified frontend state for entry/operator mode, active workspace, entry session id, agent session id, sidebar selection, messages, actions, artifacts, and canvas state.
- Kept entry/setup and workspace chat as separate backend runtimes, bridged by the shared composer in the unified shell.
- Added optional `handoff_context` to workspace agent chat requests and persisted that context on `AgentSession.metadata_`.
- Added agent context assembly support for a concise handoff summary from entry/setup context.
- Preserved entry messages through `Open Chat` so the transition into operator mode does not visually reset the conversation.

## Files Changed

- `backend/core/schemas/agent.py`
- `backend/routes/agent.py`
- `backend/services/agent/chat_service.py`
- `frontend/src/App.tsx`
- `frontend/src/components/OperatorGateway.tsx`
- `frontend/src/hooks/useSSEChat.ts`
- `frontend/src/stores/entryStore.ts`
- `frontend/src/types/agent.ts`
- `frontend/src/types/entry.ts`
- `context.md`
- `SYSTEM_FLOW_INDEX.md`
- `test_index/README.md`
- `test_index/unified-operator-shell.md`

## Decisions

- The main workspace-style layout is now the source of truth for every entry point.
- Canvas/panels remain optional and never auto-open on initial anonymous landing.
- Backend graphs were not merged in this slice; the frontend bridges `/api/entry/stream` and `/api/workspaces/{workspaceId}/agent/chat`.
- Handoff context is metadata for the first agent chat session, not a replacement for persisted workspace or connection state.

## Validation

- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Live smoke passed:
  - anonymous setup draft
  - register
  - workspace launch
  - `setup.open_chat`
  - workspace agent stream with `handoff_context`
  - persisted `agent_sessions.metadata` containing handoff context

## Next Steps

- Browser QA the unified shell across `/`, `/login`, `/register`, and `/w/:workspaceId`.
- Add frontend tests for sidebar state, runtime bridge selection, and handoff request payloads.
- Wire generated REST tools into workspace agent execution.
