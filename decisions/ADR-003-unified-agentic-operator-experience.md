# ADR-003 — Unified Agentic Operator Experience

Date: 2026-05-09
Status: Accepted
Supersedes: parts of ADR-002

## Context

ADR-001 and ADR-002 corrected the product away from a generic SaaS dashboard and toward an agent-first workspace. That was the right direction, but the later conversational entry work exposed a deeper issue: entry, auth, setup, and workspace chat cannot feel like separate products or page swaps.

The user should experience SaaStoAgent as one continuous operator console from the first anonymous question through signup, workspace creation, API setup, and workspace chat. A separate outer entry shell, a post-auth visual reset, or a distinct "open chat" destination breaks the agentic model.

## Decision

Use one unified operator shell for `/`, `/login`, `/register`, and `/w/:workspaceId`.

The shell has:

- a persistent icon sidebar
- central chat as the primary control plane
- optional panels and canvas surfaces around chat
- one shared composer area that routes to the active runtime
- frontend state that owns cross-flow UI continuity

Entry/setup and workspace chat remain separate backend runtimes for this slice:

- entry/auth/setup uses `/api/entry/stream`
- workspace chat uses `/api/workspaces/{workspaceId}/agent/chat`
- the frontend bridges them inside `OperatorGateway`
- `operator_ready` changes mode and workspace context, not the page shell

ADR-002 remains historically valid for the agent-first correction gate, but its "ActivityBar + full-width Canvas" rule is no longer the canonical v0.1 layout. The current canonical layout is central chat first, with canvas/panels available only when useful.

## Consequences

- Conversation is the continuous product surface before and after auth.
- Login/signup are graph interactions inside the same shell, not separate app pages.
- Workspace handoff must preserve entry messages and setup context.
- Direct workspace links may open the same shell in operator mode.
- Future views should extend the operator console instead of adding nested route shells.
- The frontend may own layout continuity, but workflow decisions remain backend graph-owned.
