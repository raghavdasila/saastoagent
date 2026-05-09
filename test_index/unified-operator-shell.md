# Unified Operator Shell Validation

Date: 2026-05-08

## Scope

Validation for the unified main-layout operator experience.

## Coverage

- `/`, `/login`, and `/register` render the same `OperatorGateway` shell.
- `/w/:workspaceId` renders `OperatorGateway` in operator mode instead of a separate workspace page shell.
- Entry mode sends through `/api/entry/stream`.
- Operator mode sends through `/api/workspaces/{workspaceId}/agent/chat`.
- `operator_ready` updates frontend mode/workspace state without replacing the visual shell.
- Unified messages carry a source marker for entry or agent runtime origin.
- First workspace agent request can include `handoff_context`.
- Backend stores handoff context on `AgentSession.metadata_`.
- Agent context assembly includes a concise handoff summary when metadata is present.

## Commands Run

```powershell
python -m compileall backend
npm run type-check
npm run build
```

## Live Protocol Smoke

Validated through the running Docker stack and frontend build:

- anonymous setup draft
- create account
- launch workspace
- select `setup.open_chat`
- receive `operator_ready`
- send first workspace agent chat request with handoff context
- receive agent `message_delta` and `stream_end`
- verify latest `agent_sessions.metadata` contains `handoff_context`

## Remaining Coverage

- Browser QA for sidebar disabled/locked states.
- Browser QA for panel opening without replacing central chat.
- Frontend tests for runtime adapter selection and first agent request payload.
