# SaaStoAgent v0.1 Context

Last Updated: May 9, 2026 9:25 PM
Project: SaaStoAgent v0.1
Status: Unified operator workbench, conversational entry, anonymous workspace chat, responsive context lens, RouteDeck status strip plus side map, evidence drawer, autonomy ladder, backend-owned next actions, and the first RouteDeck contract/debugger slice are implemented. Product/operator naming is corrected: the product is `SaaStoAgent`, and the operator is exactly `Corpus`. Entry/setup remains graph-owned; workspace chat remains a bridged agent runtime. The current focus is browser QA and wiring generated REST tools into chat execution.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

---

## Live State

- Frontend dev URL used during this slice: `http://localhost:3007`.
- Backend health URL: `http://localhost:8085/api/health`.
- Database image: `pgvector/pgvector:pg17`.
- REST/OpenAPI setup is the active integration path; DB connectors remain out of immediate scope.
- If existing dev servers were started before this checkpoint, restart backend/frontend so the new persistent-actions endpoint and CSS are loaded.
- After the latest naming cleanup, restart/reload the frontend before judging visible header copy.

## Current Product Shape

- `/`, `/login`, `/register`, and `/w/:workspaceId` all mount the unified `OperatorGateway` workbench.
- The capability rail, operator status strip, RouteDeck status strip, central intent spine, next action dock, and evidence drawer are always structurally available; canvas, RouteDeck side map, and context lens mount only when needed.
- Anonymous users can:
  - ask SaaStoAgent/platform questions before auth
  - draft workspace/API setup before auth
  - chat in a direct workspace route with a configurable IP rate limit
  - use backend-provided persistent Sign In / Create Account / Learn / Setup quick actions
- Auth/login/signup remain deterministic graph stages for sensitive work.
- Workspace creation and REST setup remain graph-owned after auth.
- Workspace operator chat remains bridged through `/api/workspaces/{workspaceId}/agent/chat`.
- Entry messages and setup draft are preserved through auth, workspace creation, REST setup, and operator handoff.
- The user operating loop is: describe the job -> see readiness -> approve or adjust plan -> let agent act -> inspect evidence -> give feedback or save learning.

## Backend Runtime Shape

- Entry runtime:
  - `POST /api/entry/stream` owns conversational entry/auth/setup.
  - `EntryGraphState` persists `entry_draft`, `connection_draft`, `platform_question_context`, `canvas_artifacts`, and `follow_up_context`.
- `EntryGraphTurnResponse` now separates contextual `available_actions` from global `persistent_actions`.
- `EntryGraphTurnResponse` emits `session_id`, `run_id`, `graph_version`, and `graph_manifest`; the frontend now retains these for the workbench status/evidence surfaces.
  - `graph_manifest` is now populated from the internal RouteDeck contract and includes richer node, edge, action, policy, and test-path metadata.
  - `route_deck_snapshot` exposes current node, reachable nodes, valid/blocked actions, executed nodes, recovery prompts, and diagnostics for the debugger.
  - Reusable RouteDeck framework code lives under `routedeck_framework/` with Python core contracts, React debugger/types, framework docs, and a minimal FastAPI/React example.
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
- `OperatorGateway.tsx` owns the unified workbench runtime bridge and composes stable zones:
  - capability rail
  - operator status strip
  - central intent spine
  - next action dock
  - context lens
  - evidence drawer
  - optional canvas
- `operatorExperience.ts` is the registry-driven capability model for entry/workspace surfaces, readiness states, empty states, failure states, evidence surfaces, and action ids.
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
- Persistent quick actions render through the next action dock near the composer and are not cleared during streaming.
- Contextual action cards render inline under the assistant turn and remain graph-node specific.
- Sidebar Sign In/Create Account/Learn/Setup dispatch backend action ids from persistent actions first, then contextual actions.
- Direct `/w/:workspaceId` can show backend-provided auth quick actions and can switch into entry/auth composer mode without leaving the unified layout.
- `useSSEChat` avoids bogus `Bearer undefined/null`, surfaces non-SSE HTTP failures, and sends first-turn handoff context.
- The right side panel is responsive on mobile through the `.operator-side-panel` CSS class.
- The RouteDeck navigation surface is a compact status strip in the workbench header area plus a right-side map overlay imported from the repo-local `@routedeck/react` package alias; it owns graph navigation/debug visualization.
- The evidence drawer is collapsed by default and exposes runtime ids, graph stage, readiness summary, future tool/trace/learning artifacts, and an advisory autonomy ladder.
- Product chrome and workspace navigation use `SaaStoAgent`.
- The visible operator label is exactly `Corpus`; do not append `operator` to it in UI copy.
- Legacy robotic title copy and awkward generated workspace names from generic talk-to-my-SaaS phrasing are removed from source and cleaned at display time.
- The central chat viewport now uses a clamped height to avoid forcing full-page scroll under the status strip/RouteDeck path strip/action dock/evidence drawer.

## Known Gaps

- Generated REST tools are persisted but not yet bound into workspace agent tool selection/execution.
- The autonomy ladder is visible but advisory until REST execution and approval gates are wired.
- Browser QA should be expanded beyond smoke tests to cover full anonymous/auth/setup/workspace permutations.
- Frontend renderer tests are still not automated in the repo package.
- Backend pytest is not yet wired into a reliable local/container test image.
- Platform KB is still a small static corpus and needs richer source management/citation UX.
- Anonymous workspace chat rate limiting is in-memory and process-local for this slice.
- RouteDeck currently covers entry/auth/setup/workspace handoff; generated REST execution, approvals, QA, and learnings still need to adopt the same contract later.

## Verification

- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Operator workbench baseline compile/build validation passed after adding status strip, capability rail, next action dock, context lens, evidence drawer, autonomy ladder, registry model, and new artifact renderers.
- Follow-up copy/height validation passed after title cleanup, workspace-name normalization, chat viewport clamp, and the final `SaaStoAgent`/`Corpus` split.
- Source search found no visible `Corpus operator`, `SaaSToAgent Operator`, or `It Will Talk To My Saas` matches in frontend source.
- Playwright smoke against a fresh Vite server passed:
  - direct anonymous workspace route keeps chat available
  - mobile side panel fits viewport
  - anonymous landing shows backend-provided persistent auth quick actions
  - direct anonymous workspace route shows backend-provided auth quick actions
  - Sign In quick action enters the email step
- RouteDeck validation command: `python -m backend.services.route_deck.validate`.

## Immediate Next Steps

1. Restart the live dev backend/frontend and browser QA the actual running stack at `localhost:3007`.
2. Wire generated REST tools into workspace agent execution.
3. Add repo-native frontend tests for `OperatorGateway` action dock, capability rail dispatch, evidence drawer, and direct workspace auth transition.
4. Add a backend test image or dependency path for reliable pytest execution.
5. Expand platform KB source indexing and citation display.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- UX research:
  - `knowledgebase/patterns/agentic-workbench-ux-research.md`
- Decisions:
  - `decisions/ADR-003-unified-agentic-operator-experience.md`
  - `decisions/ADR-004-backend-owned-persistent-actions.md`
  - `decisions/ADR-005-widget-canvas-artifact-contract.md`
  - `decisions/ADR-006-operator-workbench-extensibility-contract.md`
- RouteDeck docs:
  - `docs/route-deck/route-deck-overview.md`
  - `docs/route-deck/manifest-reference.md`
  - `docs/route-deck/authoring-guide.md`
  - `docs/route-deck/debugging-guide.md`
  - `docs/route-deck/migration-notes.md`
- Latest log: `logs/20260509_2125_ux_research_and_closeout.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_09-05-2026-09-25PM.md`
- Context archive: `context_history/20260509_2125_context_before_ux_research_closeout.md`
