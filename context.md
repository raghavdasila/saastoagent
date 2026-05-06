# SaaStoAgent v0.1 Context

Last Updated: May 6, 2026
Project: SaaStoAgent v0.1
Status: Slice 1 complete including Correction Gate. Product is now agent-first. Dark mode live. Ready for Slice 2.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

---

## Live State

- Slice 1 backend, frontend, and Docker Compose runtime are validated locally.
- Frontend at `http://localhost:3005` (Vite, Docker port-mapped from internal 3000).
- Backend health at `http://localhost:8085/api/health`. DB at `5435`.
- The Correction Gate (ADR-001) is complete — the product now reads as an agent-first interface, not a generic SaaS shell.
- Dark mode (black/clean, non-blue) is implemented, persisted, and verified in the live runtime.

## Current Product Shape

- Root `/` — Agent Desk: auto-enters sole workspace; shows workspace selector / zero-workspace hero otherwise
- Workspace `/w/:id` — `ActivityBar` (compact vertical) + full-width `AgentCanvas`
- Default canvas view: `AgentChatStub` — talk-first local shell with starter prompts and setup redirect
- Setup canvas view: `ConnectSetupView` — first REST connection setup UI (UI only, not wired to backend)
- No sidebar. No generic SaaS chrome.
- Theme: dark/light toggle with localStorage persistence (`sta_v01_theme`)

## State Architecture

- `authStore.ts` — canonical auth state (Zustand)
- `workspaceStore.ts` — active view, workspace ID, per-workspace shell thread messages
- `themeStore.ts` — theme mode + `.dark` class on `<html>`
- `AuthContext.tsx` / `WorkspaceContext.tsx` — thin Zustand wrapper shims kept for hook compatibility

## Current Focus

Begin Slice 2 — REST onboarding and action catalog:
1. Wire `ConnectSetupView` to a real `POST /api/workspaces/{id}/connections` endpoint
2. Build backend connection registration + activation
3. Add action-catalog inspection to the canvas

## Known Gaps

- `AgentChatStub` is local/scripted — not connected to a real agent/LLM backend
- ~152 hard-coded light-mode Tailwind classes remain; partially addressed by `surface-*` helpers
- No server-side session/thread persistence for agent chat

## Immediate Next Step

**Slice 2 — REST onboarding:** Create `POST /api/workspaces/{id}/connections` backend route, wire `ConnectSetupView` form submit, and return an activated connection with action count to the canvas.

## References

- Vision: `critical_prompt.md`
- Plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- ADR-001: `decisions/ADR-001-recenter-agentic-product-boundary.md`
- ADR-002: `decisions/ADR-002-agent-first-interface.md`
- Validation: `test_index/slice1-runtime-validation.md`
- Latest log: `logs/20260506_0735_slice1-agentic-reset-and-dark-mode.md`
- Pipeline: `context_pipeline.md`