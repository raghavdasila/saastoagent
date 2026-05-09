# SaaStoAgent v0.1 Context

Previous: `20260508_0759_context_before_conversational_entry_canvas.md`
Next: `../context.md`

Last Updated: May 8, 2026 2:29 PM
Project: SaaStoAgent v0.1
Status: Unified main-layout operator experience implemented for entry, auth, setup, and workspace chat. The icon-sidebar workspace layout is now the root surface for `/`, `/login`, `/register`, and `/w/:workspaceId`; central chat remains primary from anonymous entry through operator handoff. Entry/setup and workspace chat remain bridged backend runtimes, with handoff context stored on agent sessions.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

---

## Live State

- Docker Compose runtime is running.
- Frontend: `http://localhost:3007`
- Backend: `http://localhost:8085/api/health`
- Database: `pgvector/pgvector:pg17`.
- DB connectors remain out of immediate scope; the active setup path is REST/OpenAPI.

## Current Product Shape

- `/`, `/login`, `/register`, and `/w/:workspaceId` mount `OperatorGateway` as one unified operator shell.
- The left icon sidebar is always present.
- The central chat rail is always the primary surface.
- The old outer entry card shell is retired from the main UX.
- Anonymous users are no longer forced into sign-in/signup before conversation.
- Anonymous sidebar items expose Chat, Learn/Overview, Setup Draft, Sign In, and Create Account; workspace-only capability is locked/disabled until auth/workspace readiness.
- Authenticated workspace mode exposes Operator Chat, Connections, Knowledge Base, Sessions/Admin, and locked Entities/Actions/QA.
- The entry graph can now:
  - answer SaaStoAgent platform/how-to questions before auth
  - infer setup drafts from natural language before auth
  - offer sign-in/signup as actions and chips
  - preserve `entry_draft` through login/signup, invalid password retry, workspace creation, and REST setup intro
  - keep deterministic executor nodes for email/password, registration, workspace creation, and connection activation
- After signup with a setup draft, authenticated users are routed to `workspace_confirm`; launching the workspace carries the API draft into `connection_draft` at `setup_intro`.
- `Open Chat` now switches `OperatorGateway` into operator mode inside the same layout instead of replacing the page shell.
- Direct `/w/:workspaceId` opens the same unified shell in operator mode.

## Backend Runtime Shape

- `EntryGraphState` now persists:
  - `entry_draft`
  - `platform_question_context`
  - `canvas_artifacts`
  - `follow_up_context`
- `EntryGraphTurnResponse` now includes `ui_artifacts`.
- `EntryActionCard.kind` now includes `chip`.
- `backend/services/entry_runtime/entry_assistant.py` provides the public entry planner:
  - uses `ChatOpenAI.with_structured_output` when `STA_OPENAI_API_KEY` is present
  - falls back to deterministic planning when the LLM is unavailable or disabled
  - only routes to login/register when explicit
  - never creates workspaces or activates APIs for anonymous users
- `backend/services/entry_runtime/platform_kb.py` provides a local platform knowledge corpus with embedding search when available and keyword fallback otherwise.
- Platform KB seed sources:
  - `critical_prompt.md`
  - sibling `saastoagent/docs/saastoagent-runtime-source-of-truth-short.md`
  - sibling `saastoagent/knowledgebase/README.md`
  - current `context.md`
- Deterministic auth/workspace/setup executor stages remain in `stage_auth.py` and `stage_workspace.py`.
- `ChatRequest` accepts optional `handoff_context`.
- `/api/workspaces/{workspace_id}/agent/chat` stores first-turn handoff context on `AgentSession.metadata_`.
- Agent context assembly prepends a concise handoff summary when metadata includes entry/setup context.

## Frontend Runtime Shape

- `OperatorGateway.tsx` now acts as the unified shell, stream/session controller, runtime bridge, and responsive layout owner. It composes:
  - icon sidebar
  - chat thread
  - backend action renderer
  - inline artifact renderer
  - responsive canvas shell
  - optional side panels for entry artifacts or workspace views
- `frontend/src/stores/entryStore.ts` centralizes entry UI state:
  - operator mode
  - active workspace id
  - active sidebar item
  - entry session id
  - agent session id
  - graph state
  - messages
  - input draft
  - busy state
  - available actions
  - UI artifacts
  - active canvas artifact / open / collapsed state
- `useSSEChat` sends `handoff_context` on the first workspace agent request.
- `App.tsx` routes authenticated workspace deep links into `OperatorGateway` instead of a separate `WorkspaceShell` path.
- `frontend/src/types/entry.ts` defines the shared frontend payload types for actions and UI artifacts.
- `UnifiedOperatorMessage` extends the existing chat message shape with `source: entry | agent | system`.
- `frontend/src/types/agent.ts` defines the agent handoff context payload.
- `EntryActionCards.tsx` renders chips separately from standard buttons/forms.
- `EntryCanvasLauncher.tsx` exposes canvas-capable artifacts without mounting the canvas by default.
- `EntryArtifactRenderer.tsx` supports typed widgets:
  - `platform_overview`
  - `onboarding_checklist`
  - `setup_draft_summary`
  - `api_connection_preview`
  - `knowledge_citations`
- Markup artifacts render through a strict display-only sanitizer that removes scripts, event handlers, iframes, forms, external loading elements, and unsafe links.
- `EntryCanvasShell.tsx` only renders when the user opens a canvas artifact. Desktop gets the side canvas; mobile keeps canvas-only artifacts inline after opening.
- Canvas open/closed/collapsed state is frontend-only in this slice.

## Known Gaps

- Browser QA is still pending for the full visible unified shell, canvas/inline responsive behavior, and sidebar state changes.
- Frontend renderer tests are not yet automated; validation is currently type-check/build plus live protocol smoke.
- Backend pytest file exists for the assistant, but the runtime container does not include `pytest`; host pytest cannot import the runtime because host Python lacks `pgvector`. A direct in-container Python harness validated the same assistant assertions.
- The platform KB is intentionally small and static for this slice; later work should add indexed source management and richer citation UX.
- Generated REST tools are persisted but not yet bound into the workspace chat execution loop.
- Direct `/w/:id` deep links now use the unified shell but can still bypass graph-owned REST setup.

## Verification

- `python -m compileall backend` passed.
- `npm run type-check` passed.
- `npm run build` passed.
- Entry store/canvas validation passed by type-check/build: initial artifacts no longer auto-open the canvas; canvas opens through `EntryCanvasLauncher`.
- Unified shell validation passed by type-check/build: `/`, `/login`, `/register`, and `/w/:workspaceId` route through `OperatorGateway`.
- In-container assistant harness passed:
  - anonymous platform question returns KB-backed artifacts
  - pre-auth API description creates `entry_draft`
  - explicit sign-in routes deterministically and preserves draft
- Live `/api/entry/turn` smoke passed:
  - anonymous platform question returns `intent`, chip actions, and `platform_overview`
  - anonymous setup description persists workspace/API draft and emits `setup_draft_summary`
  - register action routes to `display_name` without losing draft
  - invalid password keeps the setup draft
  - valid signup with draft routes to `workspace_confirm`
  - workspace launch returns `setup_intro` and carries API draft into `connection_draft`
- Live bridged handoff smoke passed:
  - anonymous setup draft -> register -> workspace launch -> `setup.open_chat`
  - `operator_ready` returned without visual shell replacement
  - first workspace agent chat request included `handoff_context`
  - agent stream returned message deltas and `stream_end`
  - Postgres `agent_sessions.metadata` contains the stored handoff context

## Immediate Next Steps

1. Browser QA the unified shell on `/`, `/login`, `/register`, and `/w/:workspaceId`.
2. Add frontend renderer tests once a test runner is selected.
3. Add `pytest` or a dedicated backend test image if automated backend tests should run inside Docker.
4. Expand platform KB indexing and citations from the stable SaaStoAgent source set.
5. Wire generated REST tools into the workspace agent chat selection/execution path.

## References

- Vision: `critical_prompt.md`
- Plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- Latest log: `logs/20260508_1429_unified_main_layout_operator_experience.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_08-05-2026-02-29PM.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
