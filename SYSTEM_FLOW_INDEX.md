# System Flow Index - SaaStoAgent v0.1

Last Updated: May 24, 2026

This file is the source of truth for the currently implemented runtime and UX flows.

## Active Architecture Status - May 24, 2026

The RouteDeck/Corpus architecture has been reset around the accepted runtime-store
model.

RouteDeck is graph-backed state management for agentic UI. SaaStoAgent consumes
it through `CorpusRouteDeckRuntime` and `RouteDeckStore`; Corpus remains the
central SaaStoAgent product agent.

Current anchors:

- Framework direction: `../routedeck/docs/agentic-ui-state-runtime.md`
- Product anti-drift vision: `architecture/route-deck-corpus-vision.md`
- Current implementation plan/status: `plans/routedeck_runtime_store_reset_plan.md`

Current rules:

- Graph owns truth, guards, and commits.
- RouteDeck owns the generic runtime/store over the graph.
- Corpus reads RouteDeck state and chooses legal operations.
- Zustand stores only UI-local state and must not be treated as the app graph
  source of truth.
- Legal operations are not raw product UI.
- Legal operations are not necessarily ready to dispatch. Operation metadata
  must distinguish `invocation_kind`, `can_dispatch_now`, required args, and
  missing args.
- Visible user choices are Corpus-authored proposals or initiated surfaces.
- Diagnostics is read-only and may expose graph internals.
- Deployed visitor chat is public-safe and must not expose router internals,
  paths, operation IDs, scores, trace IDs, approval IDs, or raw tool labels.
- Product runtime is OpenAPI/user-config driven. Medusa is an acceptance
  fixture only, not hardcoded product behavior.
- Navigation diagnostics draw semantic route topology, not action edges.
- The active product shell is one Corpus workbench with a fixed bottom composer
  and inline active surfaces.
- Diagnostics can dock in the workbench or expand fullscreen while reusing the
  same shared RouteDeck debugger.

## Graph-First Reset Implemented

As of May 16, 2026, SaaStoAgent has a unified app graph spine rooted at `home`.
RouteDeck is the bridge from backend graph state to frontend navigation, actions,
surface renderers, context lens, evidence, and diagnostics.

As of the May 16 agent-first reset, RouteDeck and graph internals are no longer
product-facing concepts. The primary shell is a chat-first SaaS Agent desk, with
graph metadata available only from an explicit diagnostics disclosure.

Primary RouteDeck/Corpus endpoints:

- `GET /api/corpus/state`
- `GET /api/corpus/stream`
- `POST /api/corpus/action`
- `GET /api/routedeck/projection`
- `GET /api/routedeck/stream`
- `GET /api/diagnostics/stream`

Compatibility app graph endpoints:

- `GET /api/app/graph/snapshot`
- `POST /api/app/graph/turn`
- `POST /api/app/graph/action`

Compatibility endpoints are not the product UI contract and should be removed
after tests and unrelated callers are migrated.

Primary app graph frontend routes:

- `/app/home`
- `/app/:nodeId`
- `/app/agents/:saasAgentId`
- `/app/agents/:saasAgentId/:nodeId`

Compatibility routes hydrate graph context and no longer mount the old operator
gateway as the primary application shell:

- `/`
- `/login`
- `/register`
- `/agents/:saasAgentId`

The legacy Entry RouteDeck and selected SaaS Agent snapshot RouteDeck are now
compatibility debt. New navigation and capability work should target
`backend/services/app_graph/` and `frontend/src/components/appGraph/AppGraphShell.tsx`.

## Product Contract Reset Implemented

As of May 13, 2026, `SaaSAgent` replaces `SaaS Agent` as the product and domain authority.
The existing runtime still contains legacy SaaS Agent-shaped code until the backend and frontend
rename slices land. New work should target the SaaS Agent contract:

- one SaaS Agent is one operational SaaS surface
- Medusa Storefront and Medusa Admin are separate SaaS Agents
- every SaaS Agent owns its own RouteDeck runtime snapshot
- every SaaS Agent owns its connections, generated actions/tools, execution traces,
  RAG corpus, memory, sandbox learnings, QA evidence, and channels
- no SaaS Agent/grouping parent exists in this foundation pass

## Active Primary Flows

1. Agent-first app shell: central chat + backend-provided next steps + quiet context lens + closed diagnostics.
2. App graph flow: home -> auth -> SaaS Agent select/create -> agent home -> connection setup -> schema preview -> catalog activation -> catalog/actions/entities -> execution/input/approval/result -> knowledge/memory/learning/QA/recovery.
3. REST connection onboarding and activation through backend-provided actions,
   raw OpenAPI/schema URL configuration, and user-provided credentials. The
   setup surface must not hardcode Medusa or expose a product-target dropdown.
4. SaaS Agent operator surfaces for catalog, entities, actions, knowledge, memory, learning, and QA as backend-selected renderers.
5. RouteDeck contract and debugger framework for graph/manifest parity, hidden from product UI unless diagnostics are opened.
6. Existing SaaS Agent chat, attachments, admin, learning, RAG, and execution services remain domain utilities behind graph handlers.
7. Current verified horizontal path: Docker UI E2E covers signup, SaaSAgent
   creation, OpenAPI connection, activation, deployment, public chat, Storefront
   read execution, and Admin/write approval fixtures.
8. RouteDeck/Corpus state boundary cleanup is implemented in backend routes and
   frontend state ownership. Next: rerun Docker browser E2E, add no-navigation
   surface transition coverage, add collapsible public JSON result rendering,
   and fix conversation-grounded product/variant/cart follow-up.

## RouteDeck Layers

1. App RouteDeck bridges public entry, auth, SaaS Agent creation/selection, selected-agent setup, execution, knowledge, memory, learning, QA, and recovery.
2. `GET /api/corpus/state` returns RouteDeck runtime state converted into the Corpus state response shape.
3. `POST /api/corpus/action` dispatches through `CorpusRouteDeckRuntime` and returns the Corpus action response shape.
4. `GET /api/corpus/stream` uses RouteDeck projection events for state subscriptions and Corpus turn streaming for natural-language user input.
5. `GET /api/diagnostics/stream` reads RouteDeck snapshot and inspect data.
6. `GET /api/app/graph/snapshot`, `POST /api/app/graph/action`, and `POST /api/app/graph/turn` are compatibility endpoints, not the active product UI contract.
7. `GET /api/saas-agents/{saas_agent_id}/route-deck` is compatibility debt and should be wrapped or removed during the purge slice.

## Agent-First App Shell

1. `/app/...` routes mount `AppGraphShell`.
2. `AppGraphShell` renders the Agent desk as the primary surface.
3. Users see natural next-step labels and forms, not graph/action ids.
4. Home appears as the opening state inside the agent desk, not a separate debugger page.
5. The context lens shows selected agent, current work, API readiness, tools, and pending approval status.
6. Work surfaces appear below the conversation for the current backend-selected surface.
7. Diagnostics is closed by default and is the only product shell location where RouteDeck graph version, current node, reachable nodes, valid action ids, evidence, and raw diagnostics are displayed.
8. Browser URLs hydrate backend graph context but do not locally force workflow state.
9. The app-owned turn router lives in `backend/services/app_graph/router.py`.
10. RouteDeck core does not own model calls, API keys, or autonomous routing policy.

## Legacy Unified Operator Shell

This section documents compatibility debt from the pre-reset shell. Primary routes no longer mount `OperatorGateway`.

1. Older `/`, `/login`, `/register`, and `/agents/:SaaS AgentId` flows rendered `OperatorGateway`.
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
   - `operator` sends through `/api/saas-agents/{SaaS AgentId}/agent/chat`
4. `UnifiedOperatorMessage` keeps the existing chat message shape and adds a `source` marker for entry, agent, or system messages.
5. Anonymous capabilities are Intent Spine, Platform Lens, Setup Draft, Sign In, and Create Account.
6. SaaS Agent capabilities are Intent Spine, Connections, Knowledge Base, Sessions & Memory, and locked Entities/Actions/QA.
7. Capability selection opens the context lens/canvas without replacing the central intent spine unless the selected item is Chat.
8. Capability state is registry-driven: Ready, Needs setup, Locked, Running, Needs approval, or Has findings.
9. Canvas artifacts remain closed by default and mount only after the user opens a canvas-capable artifact.
10. `operator_ready` changes mode and SaaS Agent context inside the same shell; it does not replace the page with another layout.
11. The next action dock ranks backend-owned actions and shows one recommended next step plus secondary persistent actions.
12. RouteDeck diagnostics expose a focused current-node graph with compact
lane-separated routing and a full root-centered hub map. The full map shows all
semantic navigation nodes and route edges, keeps actions out of the canvas, and
shows action details only when inspecting a selected node.
13. The evidence drawer is collapsed by default and exposes graph/session/run ids, readiness evidence, emitted trace/tool/learning widgets, and an advisory autonomy ladder.
14. The context lens shows selected SaaS Agent identity, current SaaS Agent RouteDeck state, working-on summary, and connection/action/tool counts when operator mode is active.
15. Direct `/agents/:SaaS AgentId` can show backend-provided anonymous auth actions without blocking SaaS Agent chat.
16. Product chrome renders `SaaStoAgent`; the operator persona renders exactly as `Corpus`.
17. Legacy persisted SaaS Agent names are cleaned at display time so old generated phrasing does not leak into the header.

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

1. New visible capabilities must register a label, state model, auth/SaaS Agent requirement, empty state, failure state, evidence surface, and primary action behavior.
2. The frontend may place and rank actions, but backend graph/runtime remains the source of valid auth, setup, and execution action ids.
3. Status strip data comes from existing graph state, graph manifest, SaaS Agent stats, and runtime stream state.
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
9. Anonymous users may ask platform questions and draft setup details, but deterministic executor nodes still own auth, SaaS Agent creation, connection creation, and activation.
10. `GET /api/entry/persistent-actions` returns stable backend-owned actions for startup/direct-route surfaces.

### Action Contract

1. `available_actions` are graph-node contextual actions such as SaaS Agent launch, setup forms, or connection activation.
2. `persistent_actions` are stable global actions for the current auth/SaaS Agent state.
3. Anonymous persistent actions include:
   - `entry.learn.platform`
   - `entry.learn.setup`
   - `intent.sign_in`
   - `intent.register`
4. Deterministic auth nodes suppress conflicting anonymous persistent auth actions while collecting display name, email, or password.
5. Authenticated SaaS Agent persistent actions may include setup actions, but do not include a redundant Open Chat action inside the central chat.
6. Frontend sidebar actions dispatch backend action ids from `persistent_actions` first, then `available_actions`.

### Implemented Nodes

| Node | Role |
|------|------|
| `bootstrap` | Starts anonymous/authenticated entry flow, calls the public entry assistant when auth is not explicit |
| `intent` | Conversational public entry assistant; answers platform questions, drafts setup, or routes explicit auth intent |
| `display_name` | Collects optional display name for registration |
| `email` | Collects email |
| `password` | Authenticates or creates user |
| `SaaS Agent_select` | Opens an existing SaaS Agent or starts new SaaS Agent creation |
| `SaaS Agent_job` | Legacy internal draft field; collects the SaaS Agent name before creation |
| `SaaS Agent_confirm` | Creates the SaaS Agent |
| `setup_intro` | Prompts for REST API setup after a SaaS Agent is selected/created and no ready REST connection exists |
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
15. `operator_ready` with `active_saas_agent_id` switches the unified store to `operator` mode and keeps existing entry messages visible.
16. Direct SaaS Agent Sign In/Create Account can temporarily switch the same shell into entry/auth composer mode without replacing the page.
17. `entry_turn_result.graph_manifest`, `graph_version`, `run_id`, and `session_id` are retained for the status strip and evidence drawer.
18. Workbench widget renderer accepts readiness, tool candidate, execution plan, approval request, trace summary, and learning candidate artifacts.
19. The action dock stays visible whenever backend/RouteDeck actions exist, even before the first user message.
20. Assistant message rendering parses markdown sections while streaming; two or more sections render as native `details` panels with test hooks for section counts and summaries.

## Public Platform Assistant

1. `entry_assistant.py` receives the current anonymous/authenticated entry turn.
2. It resolves action prompt payloads or free-text input.
3. Explicit login/register language routes into deterministic auth nodes.
4. Setup language populates the SaaS Agent-name draft field and `entry_draft.api_draft`.
5. Platform questions search `platform_kb.py`.
6. Retrieval uses OpenAI embeddings when configured and keyword fallback otherwise.
7. The assistant uses live `ChatOpenAI(..., streaming=True)` deltas for public conversational output, and keeps structured-output fallback for non-streamed paths.
8. The assistant emits:
   - assistant message
   - follow-up chips
   - typed widgets
   - optional display-only markup
   - canvas-capable artifacts
9. Authenticated executor stages carry `entry_draft` into SaaS Agent creation and setup intro.
10. Sectioned assistant answers are prompted to use explicit Markdown `##` headings, bullet lists, and fenced JSON blocks instead of plain heading-like paragraphs.

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
11. Selecting `setup.open_chat` also returns `operator_ready` when a SaaS Agent is active.
12. Next work should expose OpenAPI upload/inspection and bind generated tools into the SaaS Agent agent execution loop.

## Runtime Bridge And Handoff

1. Entry/setup remains owned by `/api/entry/stream`.
2. SaaS Agent operator chat remains owned by `/api/saas-agents/{saas_agent_id}/agent/chat`.
3. Frontend runtime selection happens in `OperatorGateway` based on `OperatorExperienceMode` plus active entry graph state.
4. `ChatRequest.handoff_context` is accepted only as optional metadata on SaaS Agent agent chat requests.
5. `ChatService` stores first-turn handoff context on `AgentSession.metadata_`.
6. Agent context assembly prepends a concise handoff summary when session metadata includes entry/setup context.
7. Handoff context includes entry session id, SaaS Agent id/name, entry draft, connection draft, active connection id, and recent entry messages.

## REST Catalog API

All routes are SaaS Agent-scoped and require SaaS Agent membership.

- `GET /api/saas-agents/{saas_agent_id}/providers`
- `GET /api/saas-agents/{saas_agent_id}/route-deck`
- `POST /api/saas-agents/{saas_agent_id}/connections`
- `GET /api/saas-agents/{saas_agent_id}/connections`
- `POST /api/saas-agents/{saas_agent_id}/connections/{connection_id}/activate`
- `GET /api/saas-agents/{saas_agent_id}/connections/{connection_id}/activation-state`
- `GET /api/saas-agents/{saas_agent_id}/connections/{connection_id}/action-nodes`
- `GET /api/saas-agents/{saas_agent_id}/connections/{connection_id}/tools`

## SaaS Agent Operator Mode

1. `/agents/:SaaS AgentId` renders `OperatorGateway` in operator mode.
2. Anonymous users can chat against an existing SaaS Agent through `/api/saas-agents/{saas_agent_id}/agent/chat`.
3. Anonymous chat is IP-rate-limited by `STA_ANONYMOUS_CHAT_MESSAGES_PER_HOUR` and `STA_ANONYMOUS_CHAT_RATE_LIMIT_WINDOW_SECONDS`.
4. Authenticated users still require SaaS Agent membership for SaaS Agent management, uploads, stats, and admin surfaces.
5. The central chat uses `useSSEChat` and the SaaS Agent agent endpoint.
6. SaaS Agent and stats queries populate header/panel context only for authenticated users.
7. SaaS Agent RouteDeck query populates the operator RouteDeck widget, current state card, and context lens only for authenticated members.
8. Live views:
   - Operator Chat
   - Connections panel
   - Entities
   - Actions
   - Knowledge Base
   - Sessions & Memory
9. Locked views:
   - QA

## REST Catalog And Execution

1. Connections exposes OpenAPI URL preview, connection creation, activation progress, ready connection summaries, and direct navigation to Actions.
2. `POST /api/saas-agents/{saas_agent_id}/connections/preview` summarizes OpenAPI title/version, servers, method counts, tag counts, warnings, and sample actions before activation.
3. `GET /api/saas-agents/{saas_agent_id}/catalog` returns generated action nodes, generated tools, lightweight inferred entities, and catalog totals.
4. `GET /api/saas-agents/{saas_agent_id}/actions`, `/tools`, and `/entities` expose focused SaaS Agent catalog slices for canvases.
5. Entities are inferred from OpenAPI tags first, then path groups; this is intentionally lighter than the old resource graph canvas.
6. Actions shows generated tools, parameters, risk, approval requirement, action details, and a path back to chat.
7. SaaS Agent chat checks generated REST tools before falling back to the generic document/memory/chat graph.
8. Matched read-safe generated tools can execute directly when required inputs are present or can be inferred from the user message.
9. Every generated REST plan/execution creates an `agent_execution_traces` row with tool/action/connection ids, inferred inputs, missing inputs, candidate summary, risk, approval state, status, result, error, and RouteDeck node.
10. Write, destructive, and financial tools produce an approval-required trace and do not execute automatically.
11. Users can resume a pending approval with `approve <trace>` or reject it with `cancel <trace>`.
12. Execution emits normal `tool_start` and `tool_end` SSE events so existing message tool cards remain the trace surface.
13. SaaS Agent RouteDeck maps latest execution status into `needs_input`, `approval_required`, `executing`, and `result_review`.

## SaaS Agent RAG Generation

1. Uploaded documents continue to ingest into `agent_documents` and `agent_document_chunks`.
2. Generated API catalog knowledge is built from connected APIs, action nodes, and generated tools.
3. Generated execution trace knowledge is built from recent `agent_execution_traces`.
4. Generated RAG documents are stored as markdown documents named `Generated API Catalog` and `Generated Execution Traces`.
5. All generated and uploaded chunks are scoped by `saas_agent_id`.
6. Retrieval uses OpenAI embeddings when `STA_OPENAI_API_KEY` is configured and deterministic local vectors otherwise.
7. Activation refreshes generated catalog RAG after generated tools are ready.
8. Execution finalization refreshes generated trace RAG after result persistence.
9. `POST /api/saas-agents/{saas_agent_id}/agent/rag/generate` manually refreshes generated catalog/trace knowledge.
10. The Knowledge panel exposes a `Generate catalog RAG` control and lists generated/uploaded documents together.

## SaaS Agent Memory

1. `AgentMemory` rows are scoped by `saas_agent_id`, optional `session_id`, and optional `user_id`.
2. Memory embeddings use OpenAI when configured and deterministic local vectors otherwise.
3. Chat handles direct `remember ...` commands by saving memory without waiting for model tool selection.
4. Chat handles direct recall prompts such as `what do you remember` by searching memory.
5. `POST /api/saas-agents/{saas_agent_id}/agent/memories` creates a member-approved memory.
6. `GET /api/saas-agents/{saas_agent_id}/agent/memories` lists memories for the selected SaaS Agent.
7. `DELETE /api/saas-agents/{saas_agent_id}/agent/memories/{memory_id}` deletes memory for owners/admins.
8. Sessions & Memory includes manual memory save, list, and delete controls.
9. The chat system prompt receives recent durable and session memory through `memory_service.get_session_context`.

## Sandbox Learning

1. `AgentLearningCandidate` rows are scoped by `saas_agent_id`.
2. Failed generated REST executions propose `failed_execution` learning candidates.
3. Missing-input generated REST plans propose `missing_inputs` learning candidates.
4. `GET /api/saas-agents/{saas_agent_id}/agent/learnings` lists candidates.
5. `POST /api/saas-agents/{saas_agent_id}/agent/learnings/{candidate_id}/approve` approves a candidate.
6. `POST /api/saas-agents/{saas_agent_id}/agent/learnings/{candidate_id}/reject` rejects a candidate.
7. Operator Learn panel shows candidates and approve/reject controls.
8. Approved/active learnings add a small ranking bonus to future generated REST tool candidates.
9. Rejected learnings remain stored as evidence but do not affect ranking.

## Embedded QA

1. The unified shell includes an embedded QA panel for scenario selection, run controls, live logs, verdicts, and export.
2. QA drives the real UI through the composer, action buttons, forms, RouteDeck drawer, and graph controls rather than direct node jumps.
3. Dev-only backend QA endpoints provide scenario catalog, domain model, runtime reset, and deterministic evaluation support.
4. Current scenario coverage targets greeting/intent behavior, public questions, signin/signup cancel and mode switch flows, invalid input recovery, SaaS Agent/setup recovery, RouteDeck map smoke, REST connection preview/activation, generated Actions/Entities canvases, read-safe generated REST execution, approval-required write behavior, and RAG/memory/learning surface visibility.
5. Evaluation gates now cover SaaS Agent view evidence, API response status, catalog totals, generated tool calls, console errors, visible copy, assistant output, RouteDeck node state, and action availability.
6. Frontend QA action support includes `open_SaaS Agent_view`, `fill_connection_form`, `click_button`, `wait_for_catalog`, `collect_SaaS Agent_catalog`, `send_operator_chat`, and a Petstore setup helper for catalog/operator scenarios.
7. Backend tests fail if a QA scenario references an action that the frontend runner does not implement.

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
- RouteDeck Docker/browser validation: Playwright against `http://localhost:3007/app/home`, open Diagnostics -> Full map, confirm `Showing all 22 nodes and 29 routes`, no action controls on the canvas, selected-node actions only in the inspection panel, and no console errors.
- Persistent quick actions smoke: anonymous landing and direct SaaS Agent route show backend-provided Sign In/Create Account, and Sign In enters email collection.
- Anonymous SaaS Agent smoke: direct SaaS Agent chat remains visible without auth.
- Responsive panel smoke: mobile side panel fits a 390x844 viewport.
- Entry session continuity smoke: `/api/entry/turn` progresses `intent -> email -> password` using one request-body `session_id`
- Entry setup smoke: SaaS Agent launch returns no immediate form, and natural-language REST details progress to `connection_confirm`
- Conversational entry smoke: anonymous platform Q&A returns chips and artifacts; pre-auth setup draft survives register, invalid password retry, signup, SaaS Agent launch, and setup intro.
- In-container assistant harness: platform question, setup draft, and explicit auth routing assertions passed.
- LangGraph runtime tests: RouteDeck node/handler parity, edge/resolver parity, auth/SaaS Agent recovery navigation, public assistant streaming, and no fake token chunking regression passed in backend pytest.
- REST catalog tests: OpenAPI preview summarizes methods/tags/sample actions, and lightweight entity inference groups actions by tag/path with risk counts.
- QA service tests: UI scenario catalog includes connection/catalog/execution flows and evaluator gates cover SaaS Agent view, API status, catalog totals, and generated tool traces.
- Unified shell build validation: `/`, `/login`, `/register`, and `/agents/:SaaS AgentId` route through `OperatorGateway`.
- Bridged handoff smoke: anonymous setup draft -> register -> SaaS Agent launch -> `setup.open_chat` -> first SaaS Agent agent stream with `handoff_context`; agent session metadata persisted in Postgres.

## Known Flow Gaps

- Direct `/agents/:id` deep links can still bypass graph-owned REST setup until the user explicitly enters setup/auth.
- SaaS Agent REST execution is first-pass: read-safe generated tools can run, but approval resume controls for write/destructive/financial tools are still pending.
- Autonomy ladder is visible as an execution-policy surface, but it is advisory until REST execution approval gates are fully wired.
- Entity/action browsing is lightweight and OpenAPI-derived, not yet a full resource/workflow graph.
- Full browser QA for the responsive unified shell and entry canvas/artifact UX is still pending beyond smoke checks.
- Frontend artifact renderer tests are not yet automated.
