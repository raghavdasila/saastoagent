# Log — 2026-05-06 07:35 — Slice 1 Agentic Reset + Dark Mode

## Summary

Completed the Correction Gate from the plan. The Slice 1 shell was transformed from a generic SaaS dashboard into a conversation-first agent control plane. Dark mode (black/clean, non-blue) was implemented and verified in the live Docker runtime.

---

## Work Done

### 1. Agentic UX Redesign

**Problem:** After Slice 1 was working, the product read like a conventional SaaS app with a dashboard, sidebar, and placeholder routes. ADR-001 called for a correction pass before Slice 2.

**Solution:** Full frontend refactor to an agent-first interface pattern.

Key changes:
- Deleted `Sidebar.tsx`, `ConnectionsPage.tsx`, `ChatPage.tsx`
- Replaced sidebar nav with compact vertical `ActivityBar`
- Root page rewritten as **Agent Desk**: auto-enters sole workspace, shows zero-workspace hero, "continue / create" flow
- Workspace surface rewritten as `ActivityBar + AgentCanvas` (full-width canvas, no sidebar)
- `AgentChatStub` added: talk-first local conversational shell with starter prompts, scripted agent replies, open-setup / reset-thread controls
- `shellAgent.ts` added: scripted assistant behavior backing the chat stub
- `ConnectSetupView` added: first capability setup surface accessible from chat and activity bar
- `LockedCanvasView` added: placeholder for future-slice views

### 2. Zustand State Foundation

Added proper client-state layer so the codebase is extensible for future slices:

- `stores/authStore.ts` — canonical auth state; `hydrateAuth`, `login`, `register`, `logout`
- `stores/workspaceStore.ts` — active view, workspace ID, per-workspace shell thread state (`ShellMessage`, `shellDraftByWorkspace`, `shellMessagesByWorkspace`)
- `stores/themeStore.ts` — theme mode persistence + DOM class management; localStorage key `sta_v01_theme`
- `context/AuthContext.tsx` — converted to thin Zustand wrapper (compatibility)
- `context/WorkspaceContext.tsx` — converted to router-to-Zustand sync wrapper (compatibility)

### 3. Dark Mode

Added black/clean dark mode (not blue-tinted):

- `tailwind.config.js` — `darkMode: 'class'`
- `index.css` — `.dark` variable overrides for full neutral black palette; `surface-card`, `surface-muted`, `surface-outline-button`, `surface-solid-button` utility classes
- `main.tsx` — `useThemeStore.getState().initializeTheme()` on boot
- `ThemeToggleButton.tsx` — reusable icon-only toggle component
- All visible surfaces patched (Header, LoginPage, RegisterPage, DashboardPage, AgentChatStub, ActivityBar, ConnectSetupView, WorkspaceCreateModal, LockedCanvasView, CapabilityReadinessRow)

### 4. Runtime Fixes

- Frontend dependencies (`zustand`, `lucide-react`) required an in-container install because Docker uses a named volume for `/app/node_modules`
  - Fix: `docker compose exec frontend npm install`
- Type-check and build both pass in the container
- Dark mode toggle verified live in Docker on `http://localhost:3005/login` after `docker compose restart frontend`

---

## Files Changed

### New
- `frontend/src/stores/authStore.ts`
- `frontend/src/stores/workspaceStore.ts`
- `frontend/src/stores/themeStore.ts`
- `frontend/src/components/theme/ThemeToggleButton.tsx`
- `frontend/src/components/workspace/ActivityBar.tsx`
- `frontend/src/components/workspace/AgentCanvas.tsx`
- `frontend/src/components/workspace/AgentChatStub.tsx`
- `frontend/src/components/workspace/shellAgent.ts`
- `frontend/src/components/workspace/ConnectSetupView.tsx`
- `frontend/src/components/workspace/LockedCanvasView.tsx`
- `frontend/src/components/workspace/WorkspaceCreateModal.tsx`
- `frontend/src/components/workspace/CapabilityReadinessRow.tsx`

### Modified
- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/index.css`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/context/WorkspaceContext.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/WorkspaceOverviewPage.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/package.json`

### Deleted
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/pages/ConnectionsPage.tsx`
- `frontend/src/pages/ChatPage.tsx`

---

## Validation

- `docker compose exec frontend npm run type-check` — pass
- `docker compose exec frontend npm run build` — pass (1817 modules)
- Live browser: login page loads on `:3005`, theme toggle visible and functional, dark mode applies correctly
- Dark mode state persists via localStorage (`sta_v01_theme`)

---

## Known Gaps (→ Next Session)

- `AgentChatStub` uses a scripted local shell — not wired to any real agent backend yet
- `ConnectSetupView` UI is present but submit actions are not wired to Slice 2 backend
- Many components still have hard-coded light-mode Tailwind classes (152 matches found); the shared `surface-*` helpers partially address this but full sweep is deferred
- True foundation-agent message/session persistence (server-side thread) not yet started

---

## Next Step

Begin **Slice 2 — REST onboarding and action catalog**:
- Wire `ConnectSetupView` to a real POST endpoint for adding an OpenAPI source
- Build backend route for connection registration and activation
- Add action-catalog inspection to the canvas
