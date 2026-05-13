# System Flow Index - SaaStoAgent v0.1

Last Updated: May 13, 2026

This file is the source of truth for the currently implemented runtime and UX flows.

## Active Primary Flows

1. Unified operator workbench: capability rail + status strip + RouteDeck status strip/side map + central intent spine + contextual lens/evidence drawer
2. Conversational entry graph: public platform Q&A/setup drafting -> login/signup -> workspace create/select -> REST setup -> operator ready
3. REST connection onboarding and activation
4. Workspace operator chat, attachments, and admin inspection
5. Persistent quick actions and next best action dock for global entry/auth/setup actions
6. Anonymous direct workspace chat with IP rate limiting
7. RouteDeck contract and debugger for entry/auth/setup/workspace handoff visibility
8. LangGraph-owned entry/auth/setup runtime with RouteDeck-to-runtime parity enforcement
9. Embedded UI-driven QA panel for real-UI scenario execution and evidence capture
10. Next: REST/OpenAPI upload, inspection, generated tool binding, and workspace agent execution
11. Later: REST execution approvals, QA, tuning, and governed learnings

## Unified Operator Shell

1. `/`, `/login`, `/register`, and `/w/:workspaceId` all render `OperatorGateway`.
2. `OperatorGateway` owns the unified operator workbench:
   - capability rail with visible readiness states
   - operator status strip
   - RouteDeck status strip and side map overlay
   - central intent spine
   - backend-owned next action dock
   - optional context lens and canvas
   - collapsed evidence drawer
   - shared composer
3. `OperatorExperienceMode` selects the runtime adapter:
   - `entry` sends through `/api/entry/stream`
   - `operator` sends through `/api/workspaces/{workspaceId}/agent/chat`
4. `UnifiedOperatorMessage` keeps the existing chat message shape and adds a `source` marker for entry, agent, or system messages.
5. Anonymous capabilities are Intent Spine, Platform Lens, Setup Draft, Sign In, and Create Account.
6. Workspace capabilities are Intent Spine, Connections, Knowledge Base, Sessions & Memory, and locked Entities/Actions/QA.
7. Capability selection opens the context lens/canvas without replacing the central intent spine unless the selected item is Chat.
8. Capability state is registry-driven: Ready, Needs setup, Locked, Running, Needs approval, or Has findings.
9. Canvas artifacts remain closed by default and mount only after the user opens a canvas-capable artifact.
10. `operator_ready` changes mode and workspace context inside the same shell; it does not replace the page with another layout.
11. The next action dock ranks backend-owned actions and shows one recommended next step plus secondary persistent actions.
12. RouteDeck navigation is split into a compact status strip and a right-side map overlay with focused and full-site SVG node-link visualization, allowed-action visibility, blocked-action visibility, and JSON export. The full-site graph uses a vertical lane layout on a manifest-sized scrollable canvas so the widget remains reusable outside this app.
13. The evidence drawer is collapsed by default and exposes graph/session/run ids, readiness evidence, emitted trace/tool/learning widgets, and an advisory autonomy ladder.
14. Direct `/w/:workspaceId` can show backend-provided anonymous auth actions without blocking workspace chat.
15. Product chrome renders `SaaStoAgent`; the operator persona renders exactly as `Corpus`.
16. Legacy persisted workspace names are cleaned at display time so old generated phrasing does not leak into the header.

## RouteDeck Contract

1. `backend/services/route_deck/catalog.py` is the source for visible entry graph nodes, edges, action specs, REST form fields, sensitive-field policy, and test paths.
2. `../routedeck/routedeck_core` is the reusable Python framework layer for manifest models, validation, and runtime snapshot helpers.
3. `../routedeck/react` is the reusable frontend layer for RouteDeck TypeScript contracts and the debugger component.
4. `../routedeck/examples/minimal-fastapi-react` is the minimal reference showing how FastAPI and React consume the framework without SaaStoAgent product code.
5. `../routedeck/routedeck_langgraph` is the optional LangGraph adapter for manifest/handler parity, condition resolver parity, transition assertions, and common grouped graph wiring.
6. `graph_spec.py` delegates `build_graph_manifest()` to RouteDeck while retaining compatibility enums used by the entry runtime.
7. `ui_actions.py` adapts RouteDeck action specs into the existing `EntryActionCard` response shape.
8. `stage_io.py` validates submitted `selected_action_id` values against the current RouteDeck node before running a stage handler.
9. Invalid actions return a recoverable assistant message plus valid visible actions instead of falling into node-specific dead-end copy.
10. `EntryGraphTurnResponse.route_deck_snapshot` exposes current node, reachable nodes, valid actions, blocked actions, executed nodes, recovery prompts, and diagnostics.
11. `python -m backend.services.route_deck.validate` validates the manifest contract.
12. Docker images use named sibling build contexts so they can install RouteDeck without sending unrelated projects into the build context.
13. SaaStoAgent docs live under `docs/route-deck/`; framework docs live under `../routedeck/docs/`.
14. RouteDeck should extend next into REST/OpenAPI upload, generated tool execution, approval gates, QA, and learning surfaces.

## Workbench Extensibility Contract

1. New visible capabilities must register a label, state model, auth/workspace requirement, empty state, failure state, evidence surface, and primary action behavior.
2. The frontend may place and rank actions, but backend graph/runtime remains the source of valid auth, setup, and execution action ids.
3. Status strip data comes from existing graph state, graph manifest, workspace stats, and runtime stream state.
4. Context lens content is capability-specific and can render typed backend artifacts.
5. Evidence drawer content is progressive: runtime metadata and readiness are always available; tool candidates, execution plans, approval requests, trace summaries, and learning candidates appear when backend artifacts emit them. Route/control-flow visualization belongs in the RouteDeck status strip and side map.
6. Autonomy ladder is visible now as the future REST execution policy surface, but backend approval gates remain authoritative until execution is wired.

## Entry Graph Runtime

### Backend

1. `POST /api/entry/stream` starts or resumes an `EntrySession` using cookie `sta_v01_entry_session`.
2. `run_entry_turn()` resolves persisted graph state before request state.
3. `graph_executor.py` builds the executable runtime through `routedeck_langgraph.build_route_deck_state_graph(...)`.
4. The entry topology is `turn_start -> route_action -> group boundary -> concrete stage -> finalize_turn -> END`.
5. `execute_stage()` persists each stage, output, selected action, masked action payload, and SSE events.
6. Node handlers return assistant messages plus backend-owned contextual `available_actions`.
7. `finalize_turn` asserts that handler-produced transitions remain executable RouteDeck edges.
8. `entry_turn_result` carries final graph state, contextual actions, persistent actions, UI artifacts, JWT session payload when issued, and optional path replacement.
9. Anonymous users may ask platform questions and draft setup details, but deterministic executor nodes still own auth, workspace creation, connection creation, and activation.
10. `GET /api/entry/persistent-actions` returns stable backend-owned actions for startup/direct-route surfaces.

### Action Contract

1. `available_actions` are graph-node contextual actions such as workspace launch, setup forms, or connection activation.
2. `persistent_actions` are stable global actions for the current auth/workspace state.
3. Anonymous persistent actions include:
   - `entry.learn.platform`
   - `entry.learn.setup`
   - `intent.sign_in`
   - `intent.register`
4. Deterministic auth nodes suppress conflicting anonymous persistent auth actions while collecting display name, email, or password.
5. Authenticated workspace persistent actions may include setup actions, but do not include a redundant Open Chat action inside the central chat.
6. Frontend sidebar actions dispatch backend action ids from `persistent_actions` first, then `available_actions`.

### Implemented Nodes

| Node | Role |
|------|------|
| `bootstrap` | Starts anonymous/authenticated entry flow, calls the public entry assistant when auth is not explicit |
| `intent` | Conversational public entry assistant; answers platform questions, drafts setup, or routes explicit auth intent |
| `display_name` | Collects optional display name for registration |
| `email` | Collects email |
| `password` | Authenticates or creates user |
| `workspace_select` | Opens an existing workspace or starts a new workspace draft |
| `workspace_job` | Collects the job the operator workspace should own |
| `workspace_confirm` | Creates the workspace |
| `setup_intro` | Prompts for REST API setup after a workspace is selected/created and no ready REST connection exists |
| `connection_confirm` | Confirms REST details, creates the connection, runs activation, and hands off to chat |
| `operator_ready` | Terminal mode switch into unified operator mode inside `OperatorGateway` |

## Entry Frontend

1. `OperatorGateway.tsx` boots the unified shell and sends the first graph turn.
2. `stream_start` returns the entry `session_id`; `OperatorGateway.tsx` stores it and sends it in later turn bodies.
3. `message_delta` events append assistant messages; public entry LLM output now streams live rather than replaying delayed chunks after completion.
4. `stage_completed.output.available_actions` renders contextual action components inline in the thread.
5. `persistent_actions` render through the next action dock near the composer and are not cleared during streaming.
6. Chip actions submit lightweight follow-up prompts from backend payloads.
7. Button/nav actions submit `selected_action_id`.
8. Form actions submit `selected_action_id` plus `action_payload`.
9. `ui_artifacts` are stored in the centralized entry UI store.
10. Inline artifacts render in the chat thread.
11. Canvas-capable artifacts are offered through `EntryCanvasLauncher`; the canvas is closed by default and only mounts after the user opens an artifact.
12. Display-only markup artifacts are sanitized before rendering and reject scripts, handlers, forms, iframes, external loading elements, and unsafe links.
13. Entry thinking stays inside the active streaming assistant bubble rather than showing as a separate transient message bubble.
14. `setup_step` events append activation progress messages.
15. `operator_ready` with `active_workspace_id` switches the unified store to `operator` mode and keeps existing entry messages visible.
16. Direct workspace Sign In/Create Account can temporarily switch the same shell into entry/auth composer mode without replacing the page.
17. `entry_turn_result.graph_manifest`, `graph_version`, `run_id`, and `session_id` are retained for the status strip and evidence drawer.
18. Workbench widget renderer accepts readiness, tool candidate, execution plan, approval request, trace summary, and learning candidate artifacts.
19. The action dock stays visible whenever backend/RouteDeck actions exist, even before the first user message.

## Public Platform Assistant

1. `entry_assistant.py` receives the current anonymous/authenticated entry turn.
2. It resolves action prompt payloads or free-text input.
3. Explicit login/register language routes into deterministic auth nodes.
4. Setup language populates `entry_draft.workspace_job` and `entry_draft.api_draft`.
5. Platform questions search `platform_kb.py`.
6. Retrieval uses OpenAI embeddings when configured and keyword fallback otherwise.
7. The assistant uses live `ChatOpenAI(..., streaming=True)` deltas for public conversational output, and keeps structured-output fallback for non-streamed paths.
8. The assistant emits:
   - assistant message
   - follow-up chips
   - typed widgets
   - optional display-only markup
   - canvas-capable artifacts
9. Authenticated executor stages carry `entry_draft` into workspace creation and setup intro.

## REST Setup Flow

1. `setup_intro` starts as a conversational setup stage backed by `setup_planner.py`.
2. The planner asks for missing API details, infers REST draft fields from chat, and keeps `Add API Details` / `Open Chat` available.
3. Selecting `Add API Details` emits a REST setup form action.
4. The frontend renders backend-defined fields: connection name, base URL, spec URL, auth type, credential, header/query metadata.
5. `setup.rest.configure` validates and stores a connection draft in graph state.
6. Natural-language details can also advance directly to `connection_confirm` when enough details are known.
7. `connection_confirm` emits `Activate API` plus `Edit Details`.
8. `setup.connection.activate` creates:
   - `connections`
   - optional encrypted credential
   - `connection_activation_state`
9. Activation runs:
   - OpenAPI parse and action-node generation
   - embedding step skipped for this repair slice
   - generated tool schema creation
10. Successful activation returns `operator_ready`.
11. Selecting `setup.open_chat` also returns `operator_ready` when a workspace is active.
12. Next work should expose OpenAPI upload/inspection and bind generated tools into the workspace agent execution loop.

## Runtime Bridge And Handoff

1. Entry/setup remains owned by `/api/entry/stream`.
2. Workspace operator chat remains owned by `/api/workspaces/{workspace_id}/agent/chat`.
3. Frontend runtime selection happens in `OperatorGateway` based on `OperatorExperienceMode` plus active entry graph state.
4. `ChatRequest.handoff_context` is accepted only as optional metadata on workspace agent chat requests.
5. `ChatService` stores first-turn handoff context on `AgentSession.metadata_`.
6. Agent context assembly prepends a concise handoff summary when session metadata includes entry/setup context.
7. Handoff context includes entry session id, workspace id/name, entry draft, connection draft, active connection id, and recent entry messages.

## REST Catalog API

All routes are workspace-scoped and require workspace membership.

- `GET /api/workspaces/{workspace_id}/providers`
- `POST /api/workspaces/{workspace_id}/connections`
- `GET /api/workspaces/{workspace_id}/connections`
- `POST /api/workspaces/{workspace_id}/connections/{connection_id}/activate`
- `GET /api/workspaces/{workspace_id}/connections/{connection_id}/activation-state`
- `GET /api/workspaces/{workspace_id}/connections/{connection_id}/action-nodes`
- `GET /api/workspaces/{workspace_id}/connections/{connection_id}/tools`

## Workspace Operator Mode

1. `/w/:workspaceId` renders `OperatorGateway` in operator mode.
2. Anonymous users can chat against an existing workspace through `/api/workspaces/{workspace_id}/agent/chat`.
3. Anonymous chat is IP-rate-limited by `STA_ANONYMOUS_CHAT_MESSAGES_PER_HOUR` and `STA_ANONYMOUS_CHAT_RATE_LIMIT_WINDOW_SECONDS`.
4. Authenticated users still require workspace membership for workspace management, uploads, stats, and admin surfaces.
5. The central chat uses `useSSEChat` and the workspace agent endpoint.
6. Workspace and stats queries populate header/panel context only for authenticated users.
7. Live views:
   - Operator Chat
   - Connections panel
   - Knowledge Base
   - Sessions & Memory
8. Locked views:
   - Entities
   - Actions
   - QA

## Embedded QA

1. The unified shell includes an embedded QA panel for scenario selection, run controls, live logs, verdicts, and export.
2. QA drives the real UI through the composer, action buttons, forms, RouteDeck drawer, and graph controls rather than direct node jumps.
3. Dev-only backend QA endpoints provide scenario catalog, domain model, runtime reset, and deterministic evaluation support.
4. Current scenario coverage targets greeting/intent behavior, public questions, signin/signup cancel and mode switch flows, invalid input recovery, workspace/setup recovery, and RouteDeck map smoke.

## Verification

- Backend compile: `python -m compileall backend`
- Backend Docker import: `docker compose exec -T backend python -c "from backend.main import app; print(app.title)"`
- Backend health: `http://localhost:8085/api/health`
- REST catalog tables verified in Postgres
- Provider catalog verified in Docker
- Frontend type-check: `npm run type-check`
- Frontend build: `npm run build`
- RouteDeck manifest validation: `python -m backend.services.route_deck.validate`
- Backend tests: `python -m pytest backend/tests`
- RouteDeck adapter tests: `cd ../routedeck && python -m pytest tests`
- RouteDeck Docker/browser validation: `docker compose up -d --build frontend`, then Playwright against `http://localhost:3007` opening `Map` -> `Full graph`, confirming vertical lane order, 11 nodes, 24 paths, no same-row node overlap, no title/badge overlap, and no console errors.
- Persistent quick actions smoke: anonymous landing and direct workspace route show backend-provided Sign In/Create Account, and Sign In enters email collection.
- Anonymous workspace smoke: direct workspace chat remains visible without auth.
- Responsive panel smoke: mobile side panel fits a 390x844 viewport.
- Entry session continuity smoke: `/api/entry/turn` progresses `intent -> email -> password` using one request-body `session_id`
- Entry setup smoke: workspace launch returns no immediate form, and natural-language REST details progress to `connection_confirm`
- Conversational entry smoke: anonymous platform Q&A returns chips and artifacts; pre-auth setup draft survives register, invalid password retry, signup, workspace launch, and setup intro.
- In-container assistant harness: platform question, setup draft, and explicit auth routing assertions passed.
- LangGraph runtime tests: RouteDeck node/handler parity, edge/resolver parity, auth/workspace recovery navigation, public assistant streaming, and no fake token chunking regression passed in backend pytest.
- Unified shell build validation: `/`, `/login`, `/register`, and `/w/:workspaceId` route through `OperatorGateway`.
- Bridged handoff smoke: anonymous setup draft -> register -> workspace launch -> `setup.open_chat` -> first workspace agent stream with `handoff_context`; agent session metadata persisted in Postgres.

## Known Flow Gaps

- Direct `/w/:id` deep links can still bypass graph-owned REST setup until the user explicitly enters setup/auth.
- Generated REST tools are persisted but not yet bound into the chat agent execution loop.
- Autonomy ladder is visible as an execution-policy surface, but it is advisory until REST execution approval gates are wired.
- Entity/action browsing remains locked.
- Full browser QA for the responsive unified shell and entry canvas/artifact UX is still pending beyond smoke checks.
- Frontend artifact renderer tests are not yet automated.
