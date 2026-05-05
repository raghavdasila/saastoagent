# System Flow Index — SaaStoAgent v0.1

This file is the source of truth for the main product flows as implementation begins.

## Planned Primary Flows

1. Workspace setup and selection
2. REST connection onboarding and activation
3. Entity and action exploration
4. Retrieval-only tool-finder chat
5. Agentic REST execution
6. QA agent execution and review

## Implemented Flow — Slice 1

### Backend

1. `backend.main:app` starts and creates public tables on boot
2. Auth routes are exposed at `/api/auth/*`
3. `/api/me` returns the current authenticated user
4. `/api/workspaces` supports create, list, and get
5. Creating a workspace provisions a matching tenant schema via `backend.core.tenancy.create_tenant_schema`
6. `/api/workspaces/{workspace_id}/stats` returns placeholder Slice 1 stats

### Frontend

1. `frontend/src/main.tsx` boots React Query and auth context
2. `frontend/src/App.tsx` wires public auth routes and protected workspace routes
3. `frontend/src/pages/DashboardPage.tsx` lists and creates workspaces
4. `frontend/src/components/layout/WorkspaceLayout.tsx` applies the workspace shell
5. `frontend/src/pages/WorkspaceOverviewPage.tsx` presents the workspace-as-agent overview
6. `/w/:workspaceId/connections` and `/w/:workspaceId/chat` are Slice 1 placeholders for later slices

## Current Status

Slice 1 runnable shell is implemented. Later slices are still placeholders.

Update this file when concrete routes, services, SSE events, hooks, and page flows are added.