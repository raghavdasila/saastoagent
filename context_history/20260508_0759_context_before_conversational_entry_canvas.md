# SaaStoAgent v0.1 Context

Last Updated: May 8, 2026 7:24 AM
Project: SaaStoAgent v0.1
Status: REST setup repair slice implemented, with entry-session loop fix and LLM-backed setup conversation applied. Entry graph now continues from login/signup and workspace creation into backend-owned REST API setup with conversational collection, structured action forms, and activation progress.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

---

## Live State

- Docker Compose runtime is rebuilt and running.
- Frontend: `http://localhost:3007`
- Backend: `http://localhost:8085/api/health` -> `{"status":"ok"}`
- Database: `pgvector/pgvector:pg17`; REST catalog tables exist in `public`.
- DB connectors remain out of immediate scope; the active setup path is REST/OpenAPI only.

## Current Product Shape

- `/`, `/login`, and `/register` still mount `OperatorGateway`.
- Entry flow is backend-owned over SSE at `/api/entry/stream`.
- Entry turns now carry `session_id` in the request body as well as the `sta_v01_entry_session` cookie. This prevents dev browser/proxy cookie loss from restarting the graph at `bootstrap` on every turn.
- After workspace creation/selection, setup no longer opens the REST form by default. `setup_intro` now uses an LLM-backed planner to converse, infer REST connection details from chat, and only show the form when explicitly requested or useful.
- The graph path now covers:
  - sign in / create account
  - workspace select / create
  - REST API setup prompt
  - structured REST connection form action
  - connection confirmation
  - activation progress events
  - operator chat handoff
- `EntryActionCard` now supports richer action components:
  - `button`
  - `form`
  - `nav`
  - `summary`
- Frontend action rendering is still intentionally thin: it renders backend-supplied fields and posts `selected_action_id` plus `action_payload`.

## Backend Runtime Shape

- New workspace-scoped REST routes:
  - `GET /api/workspaces/{workspace_id}/providers`
  - `POST /api/workspaces/{workspace_id}/connections`
  - `GET /api/workspaces/{workspace_id}/connections`
  - `POST /api/workspaces/{workspace_id}/connections/{connection_id}/activate`
  - `GET /api/workspaces/{workspace_id}/connections/{connection_id}/action-nodes`
  - `GET /api/workspaces/{workspace_id}/connections/{connection_id}/tools`
- New public workspace-scoped catalog tables:
  - `connections`
  - `encrypted_credentials`
  - `connection_activation_state`
  - `action_nodes`
  - `generated_tools`
- REST provider code parses OpenAPI/Swagger specs, extracts action nodes, classifies risk, and generates callable tool schemas.
- `backend/services/entry_runtime/setup_planner.py` provides the entry setup planner. It uses `ChatOpenAI` with structured output when `STA_OPENAI_API_KEY` is present, plus deterministic URL/auth extraction as a fallback and guardrail.
- Activation currently runs:
  - `generate`: OpenAPI -> action nodes
  - `embed`: skipped for this repair slice
  - `tools`: action nodes -> generated tools

## Frontend Runtime Shape

- `EntryActionCards.tsx` now renders both compact buttons and backend-defined forms.
- `OperatorGateway.tsx` submits structured action payloads and renders `setup_step` progress messages from the backend.
- `OperatorGateway.tsx` stores `stream_start` / `entry_turn_result` session ids and includes the current `session_id` on later `/api/entry/stream` calls.
- `WorkspaceShell` and existing workspace chat/admin/attachments surfaces still work after the setup handoff.

## Known Gaps

- Browser click-through QA is still pending for the full REST setup form and activation path.
- No external OpenAPI activation smoke was run against a real public spec to avoid creating test workspace data.
- `STA_OPENAI_API_KEY` is still optional for this repair slice; embeddings and LLM-backed chat/RAG remain separately dependent on it.
- Workspace deep-link `/w/:id` can still bypass the entry graph and land in the workspace shell; later hardening should route no-connection workspaces into the setup surface.
- `ConnectSetupView` is still a workspace panel, not the primary graph-owned setup path.

## Verification

- `python -m compileall backend` passed.
- `npm run type-check` passed.
- `npm run build` passed.
- Docker backend import check passed: `from backend.main import app`.
- Backend health check passed: `http://localhost:8085/api/health`.
- Docker config check confirms `STA_OPENAI_API_KEY` is loaded and `STA_DEFAULT_MODEL` resolves to `gpt-5-mini`.
- Entry graph session continuity smoke passed without relying on browser cookies: `intent -> email -> password` with the same request-body `session_id`.
- Entry setup smoke passed:
  - workspace launch returns `setup_intro`
  - no form action is emitted immediately after launch
  - natural-language API details advance to `connection_confirm`
  - exact OpenAPI spec URL is preserved
- REST catalog table presence verified in Postgres.
- Provider catalog import verified in Docker.

## Immediate Next Steps

1. Browser QA the full entry path:
   - create account
   - create workspace
   - submit REST setup form
   - activate against a known OpenAPI spec
   - confirm handoff into workspace chat
2. Decide whether setup should also be enforced for direct `/w/:id` deep links when no REST connection is ready.
3. Wire generated REST tools into the workspace agent chat selection/execution path.

## References

- Vision: `critical_prompt.md`
- Plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- Latest log: `logs/20260508_0724_llm_backed_setup_conversation.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_08-05-2026-07-24AM.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
