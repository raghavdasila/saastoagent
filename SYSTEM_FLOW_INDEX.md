# System Flow Index — SaaStoAgent v0.1

This file is the source of truth for the main product flows as implementation begins.

## Planned Primary Flows

1. Workspace setup and selection
2. REST connection onboarding and activation  ← **Slice 2 active**
3. Entity and action exploration
4. Retrieval-only tool-finder chat
5. Agentic REST execution
6. QA agent execution and review

---

## Implemented Flows — Slice 1 (including Correction Gate)

### Backend

1. `backend.main:app` starts and creates public tables on boot
2. Auth routes at `/api/auth/*` (register, login, logout)
3. `/api/me` returns the authenticated user
4. `/api/workspaces` supports create, list, and get
5. Creating a workspace provisions a matching tenant schema via `backend.core.tenancy.create_tenant_schema`
6. `/api/workspaces/{workspace_id}/stats` returns placeholder Slice 1 stats

### Frontend — Auth Flow

1. `frontend/src/main.tsx` boots React Query, auth context, and initializes theme (`useThemeStore.getState().initializeTheme()`)
2. `frontend/src/App.tsx` routes: public `/login`, `/register`; protected `/*`
3. `ProtectedRoute` hydrates auth from Zustand store and redirects unauthenticated users
4. `PublicRoute` redirects already-authenticated users away from auth pages
5. `LoginPage` / `RegisterPage` render with `ThemeToggleButton` in the top-right

### Frontend — Agent Desk (Root)

1. `DashboardPage` loads at `/`
2. If exactly one workspace exists → auto-navigates to `/w/:id`
3. If zero workspaces → renders zero-workspace hero with "Create your first agent" CTA
4. If multiple workspaces → renders workspace selector with "Continue" for primary and list for others
5. `WorkspaceCreateModal` handles workspace creation inline

### Frontend — Workspace / Agent Canvas

1. `WorkspaceRouteRedirect` maps `/w/:id` to the workspace overview
2. `WorkspaceOverviewPage` fetches workspace + stats then renders `<AgentCanvas workspace={workspace} stats={stats} />`
3. `AgentCanvas` reads `activeView` from `workspaceStore`
4. Default view (`chat`): renders `AgentChatStub`
5. `connect` view: renders `ConnectSetupView`
6. All other views: renders `LockedCanvasView` with slice-unlock messaging
7. `ActivityBar` shows capability icons; clicking sets `activeView` in `workspaceStore`

### Frontend — Agent Chat Shell (Local)

1. `AgentChatStub` mounts and seeds an initial assistant message via `buildInitialAgentMessage(workspace)` from `shellAgent.ts`
2. User selects a starter prompt or types a message
3. `sendMessage()` appends user message to `workspaceStore.shellMessagesByWorkspace` and calls `buildShellAgentReply()`
4. `buildShellAgentReply()` returns a scripted response (not LLM-backed yet)
5. Reply is appended after a short delay to simulate streaming
6. "Set up a connection" in replies → sets `activeView` to `connect`

### Frontend — Theme

1. On app boot: `initializeTheme()` reads `sta_v01_theme` from localStorage, sets `.dark` on `<html>` if dark
2. `ThemeToggleButton` calls `toggleTheme()` → flips `.dark` class and persists to localStorage
3. All surfaces use `surface-card`, `surface-muted`, `surface-outline-button`, `surface-solid-button` CSS helpers and Tailwind dark variants

---

## Current Status

Slice 1 + Correction Gate complete. Slice 2 (REST onboarding) is next.

Update this file when concrete routes, services, SSE events, hooks, and page flows are added for Slice 2.