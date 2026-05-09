# SaaStoAgent v0.1 Context

Last Updated: May 9, 2026 6:52 PM
Project: SaaStoAgent v0.1
Status: Unified operator shell, conversational entry, anonymous workspace chat, responsive side panel, and persistent quick actions are implemented. Entry/setup remains graph-owned; workspace chat remains a bridged agent runtime. The current focus is QA hardening and wiring generated REST tools into chat execution.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

---

## Live State

- Frontend dev URL used during this slice: `http://localhost:3007`.
- Backend health URL: `http://localhost:8085/api/health`.
- Database image: `pgvector/pgvector:pg17`.
- REST/OpenAPI setup is the active integration path; DB connectors remain out of immediate scope.
- If existing dev servers were started before this checkpoint, restart backend/frontend so the new persistent-actions endpoint and CSS are loaded.

## Current Product Shape

- `/`, `/login`, `/register`, and `/w/:workspaceId` all mount the unified `OperatorGateway` layout.
- The icon sidebar and central chat are always present; canvas and right panels mount only when needed.
- Anonymous users can:
  - ask SaaStoAgent/platform questions before auth
  - draft workspace/API setup before auth
  - chat in a direct workspace route with a configurable IP rate limit
  - use backend-provided persistent Sign In / Create Account / Learn / Setup quick actions
- Auth/login/signup remain deterministic graph stages for sensitive work.
- Workspace creation and REST setup remain graph-owned after auth.
- Workspace operator chat remains bridged through `/api/workspaces/{workspaceId}/agent/chat`.
- Entry messages and setup draft are preserved through auth, workspace creation, REST setup, and operator handoff.

## Backend Runtime Shape

- Entry runtime:
  - `POST /api/entry/stream` owns conversational entry/auth/setup.
  - `EntryGraphState` persists `entry_draft`, `connection_draft`, `platform_question_context`, `canvas_artifacts`, and `follow_up_context`.
  - `EntryGraphTurnResponse` now separates contextual `available_actions` from global `persistent_actions`.
  - `GET /api/entry/persistent-actions` returns backend-owned stable actions for direct routes and non-streaming startup surfaces.
- Persistent actions:
  - anonymous users receive Learn, Setup, Sign In, and Create Account unless they are already in deterministic auth nodes
  - authenticated workspace users can receive setup-oriented persistent actions without reintroducing a redundant Open Chat action
  - action ids are preserved: `intent.sign_in`, `intent.register`, `entry.learn.platform`, `entry.learn.setup`
- Public platform assistant:
  - uses `ChatOpenAI.with_structured_output` when `STA_OPENAI_API_KEY` is configured
  - falls back to deterministic planning when LLM calls are unavailable
  - uses local platform KB retrieval with embedding search when available and keyword fallback otherwise
- Anonymous workspace chat:
  - `/api/workspaces/{workspace_id}/agent/chat` accepts unauthenticated chat when the workspace exists
  - IP rate limit defaults to `10` messages per hour
  - config: `STA_ANONYMOUS_CHAT_MESSAGES_PER_HOUR`, `STA_ANONYMOUS_CHAT_RATE_LIMIT_WINDOW_SECONDS`
- Agent handoff:
  - `ChatRequest.handoff_context` is optional
  - first-turn handoff metadata is stored on `AgentSession.metadata_`
  - agent context assembly prepends a concise handoff summary when present

## Frontend Runtime Shape

- `OperatorGateway.tsx` owns the unified shell, runtime bridge, stream handling, sidebar, chat thread, action rendering, and responsive panel/canvas layout.
- `entryStore.ts` centralizes cross-flow state:
  - mode
  - active workspace id
  - active sidebar item
  - entry and agent session ids
  - graph state
  - messages
  - contextual `availableActions`
  - stable `persistentActions`
  - UI artifacts and canvas state
- Persistent quick actions render in a compact rail near the composer and are not cleared during streaming.
- Contextual action cards render inline under the assistant turn and remain graph-node specific.
- Sidebar Sign In/Create Account/Learn/Setup dispatch backend action ids from persistent actions first, then contextual actions.
- Direct `/w/:workspaceId` can show backend-provided auth quick actions and can switch into entry/auth composer mode without leaving the unified layout.
- `useSSEChat` avoids bogus `Bearer undefined/null`, surfaces non-SSE HTTP failures, and sends first-turn handoff context.
- The right side panel is responsive on mobile through the `.operator-side-panel` CSS class.

## Known Gaps

- Generated REST tools are persisted but not yet bound into workspace agent tool selection/execution.
- Browser QA should be expanded beyond smoke tests to cover full anonymous/auth/setup/workspace permutations.
- Frontend renderer tests are still not automated in the repo package.
- Backend pytest is not yet wired into a reliable local/container test image.
- Platform KB is still a small static corpus and needs richer source management/citation UX.
- Anonymous workspace chat rate limiting is in-memory and process-local for this slice.

## Verification

- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Playwright smoke against a fresh Vite server passed:
  - direct anonymous workspace route keeps chat available
  - mobile side panel fits viewport
  - anonymous landing shows backend-provided persistent auth quick actions
  - direct anonymous workspace route shows backend-provided auth quick actions
  - Sign In quick action enters the email step

## Immediate Next Steps

1. Restart the live dev backend/frontend and browser QA the actual running stack at `localhost:3007`.
2. Wire generated REST tools into workspace agent execution.
3. Add repo-native frontend tests for `OperatorGateway` action rail, sidebar dispatch, and direct workspace auth transition.
4. Add a backend test image or dependency path for reliable pytest execution.
5. Expand platform KB source indexing and citation display.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Decisions:
  - `decisions/ADR-003-unified-agentic-operator-experience.md`
  - `decisions/ADR-004-backend-owned-persistent-actions.md`
  - `decisions/ADR-005-widget-canvas-artifact-contract.md`
- Latest log: `logs/20260509_1852_persistent_quick_actions_and_anonymous_chat.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_09-05-2026-06-52PM.md`
- Context archive: `context_history/20260509_1852_context_before_persistent_quick_actions_closeout.md`
