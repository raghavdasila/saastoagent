# ADR-002 — Agent-First Interface Pattern

Date: 2026-05-06
Status: Accepted

## Context

After the Correction Gate pass (ADR-001 outcome), the frontend was rewritten to be genuinely agent-first. This decision records the specific architectural choices made and establishes them as the interface contract for future slices.

## Decision

The workspace interface is built around three principles:

1. **Conversation is the control plane.** The primary surface inside a workspace is a talk-first shell (`AgentChatStub`). Users direct agent behavior through conversation, not through dashboard links or menu navigation.

2. **ActivityBar + full-width Canvas.** Navigation is a compact vertical icon bar (ActivityBar). Each capability opens a full-width canvas view rather than a side-panel or nested page. This keeps the agent surface dominant and avoids a generic SaaS page hierarchy.

3. **Capabilities are revealed progressively.** Unimplemented future-slice views render a `LockedCanvasView` placeholder. Only `connect` and `chat` are active in Slice 1. Further capabilities unlock as slices are completed.

### Concrete interface decisions

- No sidebar. `Sidebar.tsx` is deleted.
- Root (`/`) is an Agent Desk, not a workspace list page.
- The workspace page (`/w/:id`) renders `<AgentCanvas>` directly, not a layout with nested routes.
- `AgentChatStub` seeds an initial assistant message and offers starter prompts.
- `ConnectSetupView` is the single onboarding surface and is navigable from the chat shell via "Set up a connection".

## Consequences

- All future-slice canvas views must follow the ActivityBar + full-width canvas pattern.
- Chat must remain the entry point; capability views are secondary surfaces reachable from the chat.
- When the local scripted shell (`shellAgent.ts`) is replaced with a real LLM backend, the component interface (`AgentChatStub` → `shellAgent`) must remain stable from the canvas's perspective.
- State for the shell thread (messages, draft) lives in `workspaceStore.ts`, keyed by workspace ID, to support multi-workspace navigation without losing thread context.
