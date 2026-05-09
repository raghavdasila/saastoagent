# ADR-004 — Backend-Owned Persistent Actions

Date: 2026-05-09
Status: Accepted

## Context

The conversational entry graph originally emitted per-turn `available_actions`. That worked for local node actions such as launching a workspace or activating a connection, but it failed for global actions that should remain available across turns, especially Sign In and Create Account.

When the unified shell introduced direct workspace chat and optional panels, frontend-only starter prompts and contextual action clearing made important actions disappear. The product needs actions that are relevant to the current graph and actions that are globally available for the current auth/workspace state.

## Decision

Split backend actions into two contracts:

- `available_actions`: contextual actions for the current graph node
- `persistent_actions`: stable global actions for the current auth/workspace state

The backend owns both groups. The frontend renders and dispatches them, but does not invent auth/setup actions locally.

Persistent action examples:

- anonymous users get `entry.learn.platform`, `entry.learn.setup`, `intent.sign_in`, and `intent.register`
- deterministic auth nodes suppress conflicting auth actions while collecting display name, email, or password
- authenticated workspace users can receive setup-oriented persistent actions
- `Open Chat` is not a persistent quick action when the user is already in central chat

Direct routes that have not yet streamed an entry turn can fetch persistent actions through `/api/entry/persistent-actions`.

## Consequences

- Quick actions no longer disappear when contextual graph actions are cleared during streaming.
- Sidebar action dispatch resolves backend action ids from `persistent_actions` first, then `available_actions`.
- Login/signup remain available across anonymous entry and direct workspace chat without frontend hardcoding.
- Contextual forms and execution actions remain node-scoped, reducing accidental invalid action loops.
- Future action surfaces should preserve this separation instead of adding ad hoc frontend chips.
