# SaaStoAgent v0.1 Workspace Agent Plan

## Summary

Build `saastoagent-v0.1` as a REST-only workspace agent product.

## Key Product Decisions

- 1 workspace = 1 SaaS agent
- REST only
- Entity + actions concept is included in v0.1
- QA, error capture, tuning, and governed self-learning are first-class in v0.1
- `AgentSystem` is not retained as a user-facing concept

## Slice Plan

### ✅ Slice 1 — Workspace-as-agent shell

Status: **COMPLETE** (as of 2026-05-06)

Done:

- A user can create/select a workspace
- The workspace lands on an agent-first canvas
- ActivityBar + AgentCanvas replaces sidebar/dashboard pattern
- `AgentChatStub` provides a talk-first local conversational shell
- Zustand state layer in place (authStore, workspaceStore, themeStore)
- Dark mode (black/clean) implemented and verified
- Auth, workspace, routing, Docker foundations all validated

### ✅ Correction Gate — Recenter The Shell Before Slice 2

Status: **COMPLETE** (as of 2026-05-06)

All criteria met:

- Root `/` is an Agent Desk, not a generic dashboard
- Workspace canvas is activity-bar + full-width canvas, not a sidebar app
- `AgentChatStub` is the primary entry surface — conversation-first
- `Sidebar.tsx`, `ConnectionsPage.tsx`, `ChatPage.tsx` deleted
- ADR-002 filed to record the agent-first interface decision

### ✅ Slice 2A — Agentic REST setup and action catalog foundation

Status: **IMPLEMENTED** (as of 2026-05-07)

Implemented:

- Entry graph continues from auth/workspace creation into REST setup
- Backend action components support structured REST setup forms
- `POST /api/workspaces/{id}/connections` registers REST/OpenAPI sources
- Activation parses OpenAPI specs and generates action nodes/tools
- Workspace stats count connections and tools
- REST catalog routes expose providers, connections, activation state, action nodes, and tools

Deferred from the original Slice 2 wording:

- Browser QA through a real OpenAPI setup path
- Action/tool inspection inside the canvas
- Generated REST tool binding into chat/runtime execution

### ✅ UX Baseline Gate - Operator workbench operating model

Status: **IMPLEMENTED** (as of 2026-05-09)

Implemented:

- `OperatorGateway` now presents a workbench instead of chat plus side panels.
- A registry-driven capability model defines state, empty state, failure state, evidence surface, and action linkage for entry/workspace capabilities.
- The workbench has a status strip, capability rail, next action dock, context lens, evidence drawer, and advisory autonomy ladder.
- Frontend action placement remains backend-action driven; auth/setup/execution command validity stays backend-owned.
- ADR-006 records the extensibility contract for future capabilities.

Done when:

- First-run users can see the current stage, readiness, and next step without opening multiple panels.
- Power users can expand evidence and see runtime ids, graph state, readiness, future artifact surfaces, and execution policy controls.
- Future slices can add entities, actions, QA, and learnings through the capability registry rather than one-off shell changes.

### ✅ RouteDeck Contract Gate - Graph-owned navigation and debugger

Status: **IMPLEMENTED** (as of 2026-05-10)

Implemented:

- Entry/auth/setup/workspace handoff now has a backend-owned RouteDeck manifest and runtime snapshot.
- RouteDeck action ids, node ids, field specs, sensitive policy, recovery prompts, and test paths live in a central catalog.
- Existing entry response shapes are preserved through adapters while richer RouteDeck metadata is emitted.
- Stage input validates submitted `selected_action_id` values before handlers run.
- Invalid selected actions recover with visible alternatives instead of falling into dead-end copy.
- Reusable framework code lives under `routedeck_framework/` with Python core contracts, React types/debugger, docs, packaging notes, and a minimal FastAPI/React example.
- The standalone RouteDeck nav widget shows a compact status strip and a side map with focused graph, full-site graph, allowed actions, blocked actions, and JSON export.
- The full-site graph uses a vertical lane layout on a manifest-sized scrollable canvas so the widget can ship with RouteDeck rather than only fit this app.
- `ADR-007` records RouteDeck as the reusable framework contract.

Done when:

- Sign in, signup, setup, direct workspace, and invalid action recovery can be diagnosed from RouteDeck state.
- Docker/browser QA can open the RouteDeck map from the product shell without Vite alias/HMR failures.
- Future REST execution, approvals, QA, and learnings can adopt RouteDeck instead of inventing separate frontend/backend action contracts.

### 🔲 Slice 2B — REST tool inspection and chat binding  ← ACTIVE NEXT

Status note (2026-05-10):

- Unified shell, conversational entry, persistent quick actions, anonymous direct workspace chat, setup handoff, and RouteDeck graph-navigation/debugging are now in place.
- The next slice should start from generated REST tool inspection/binding rather than more entry/auth shell work.
- Direct `/w/:id` now supports anonymous chat and backend-provided auth quick actions, but still needs graph-owned setup redirection when no ready REST connection exists.

Done when:

- A generated REST action/tool can be inspected from the workspace
- Operator chat can find relevant generated REST tools for a request
- The setup path is enforced or clearly redirected for `/w/:id` deep links with no ready connection

### Slice 3 — Simplified entity explorer

Infer entities from REST response structures and expose a lightweight entity detail and action-path experience.

Done when:

- A user can browse entities and inspect their actions
- One action-path detail flow exists without requiring a full graph canvas

### Slice 4 — REST tool-finder chat

Add retrieval-only chat for action, entity, and action-path discovery.

### Slice 5 — Agentic REST execution

Turn workspace chat into a full REST task runner.

### Slice 6 — QA, tuning, and self-learning loop

Add an operator-facing QA loop for the workspace agent that makes it easy to catch failures, inspect traces, tune behavior, and persist validated learnings.

### Slice 7 — REST-only hardening

Remove remaining non-REST assumptions and stabilize follow-up handling.

## Exact Copy Order

### Slice 1 backend foundation

Copy from `saastoagent` first:

- `backend/core/models/public.py`
- `backend/core/schemas/workspace.py`
- `backend/core/schemas/__init__.py`
- `backend/core/tenancy.py`
- `backend/services/support/stats.py`
- `backend/routes/workspaces.py`

### Slice 1 frontend shell

Copy and adapt in this order:

- `frontend/src/lib/api.ts`
- `frontend/src/lib/storage.ts`
- `frontend/src/types/domain.ts`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/context/WorkspaceContext.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/WorkspaceLayout.tsx`
- `frontend/src/pages/WorkspaceOverviewPage.tsx`
- `frontend/src/App.tsx`

Adaptation rule: remove systems-first UX and make the workspace the agent home.

### Slice 2 backend REST catalog

Copy and adapt:

- `backend/providers/__init__.py`
- `backend/providers/base.py`
- `backend/providers/rest/parser.py`
- `backend/providers/rest/adapter.py`
- `backend/routes/connections.py`
- `backend/services/discovery/activation.py`
- `backend/services/discovery/engine.py`
- `backend/services/discovery/embeddings.py`
- `backend/services/tools/generator.py`
- `backend/routes/tools.py`

### Slice 2 frontend REST catalog

Copy and adapt in the user path order:

- `frontend/src/pages/ConnectionsPage.tsx`
- `frontend/src/components/ConnectionCard.tsx`
- `frontend/src/components/NewConnectionFlow.tsx`
- `frontend/src/pages/ConnectionDetailPage.tsx`
- `frontend/src/components/StatusBadge.tsx`
- `frontend/src/components/EmptyState.tsx`
- `frontend/src/components/ActionNodeCard.tsx`
- `frontend/src/pages/ActionNodeDetailPage.tsx`

Adaptation rule: keep only REST provider surfaces from the beginning.

## Source References for Later Slices

### Slice 3

- `saastoagent/backend/services/graph/discovery/rest_adapter.py`
- `saastoagent/backend/services/graph/inference/shape_matcher.py`
- `saastoagent/backend/services/graph/inference/set_algebra.py`
- `saastoagent/backend/services/graph/inference/resource_inferrer.py`
- `saastoagent/backend/services/graph/inference/resource_builder.py`
- `saastoagent/backend/services/graph/action_path.py`
- `saastoagent/frontend-v3/src/pages/ResourceNodeDetailPage.tsx`
- `saastoagent/frontend-v3/src/pages/ActionPathDetailPage.tsx`

### Slice 4

- `foundation-agent/frontend/src/pages/ChatPage.tsx`
- `foundation-agent/frontend/src/hooks/useSSEChat.ts`
- `foundation-agent/backend/routes/chat.py`
- `foundation-agent/backend/routes/sessions.py`
- `foundation-agent/backend/services/chat_service.py`
- `saastoagent/backend/routes/search.py`
- `saastoagent/backend/services/tools/search.py`

### Slice 5

- `saastoagent/backend/services/orchestration/chat.py`
- `saastoagent/backend/services/orchestration/agent_loop.py`
- `saastoagent/backend/services/orchestration/pipeline.py`
- `saastoagent/backend/services/tools/binder.py`
- `saastoagent/backend/services/execution/executor.py`

### Slice 6

- `saastoagent/backend/routes/qa.py`
- `saastoagent/backend/testing/qa_config.py`
- `saastoagent/backend/testing/query_tester.py`
- `saastoagent/frontend-v3/src/components/qa/QAAgentPanel.tsx`
- `saastoagent/frontend-v3/src/hooks/useQAAgent.ts`
- `saastoagent/frontend-v3/src/pages/QAPage.tsx`

## Verification

1. Slice 1: workspace is the only visible agent boundary
2. Slice 2: one REST connection activates and exposes action nodes and tools
3. Slice 3: entity detail and action-path detail work without graph-canvas dependency
4. Slice 4: retrieval chat returns actions plus entity-aware context
5. Slice 5: runtime streams retrieval, selection, execution, and synthesis
6. Slice 6: QA catches failures, supports tuning, and persists validated learnings and results
7. Slice 7: only REST remains visible anywhere in the product
