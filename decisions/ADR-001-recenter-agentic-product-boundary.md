# ADR-001 — Recenter The Product Boundary On An Agentic Workspace Home

Date: 2026-05-05
Status: Accepted

## Context

Slice 1 now runs locally and proves the auth, workspace, routing, and Docker foundation. However, the visible product still reads like a conventional SaaS app shell: login, dashboard, workspace shell, and placeholder routes layered in a generic application pattern.

That is not the intended v0.1 direction. The product was meant to feel agentic from the start, with the workspace acting as an operator-facing agent home. If Slice 2 and later capabilities are added onto the current shell without correction, the repo will deepen the wrong product model.

## Decision

Before broad Slice 2 work, recenter the visible product boundary around an agentic workspace home.

This means:

- the first post-login surface must orient around the agent and its current capability state
- workspace navigation must read as agent operation, not generic SaaS navigation
- workspace home must foreground capabilities such as connections, actions, execution, QA, and learnings
- placeholder copy and labels must avoid reinforcing a generic SaaS shell

## Consequences

- The current Slice 1 implementation remains valuable as technical foundation.
- Slice 2 is gated by a short product-surface correction pass.
- Future slices should extend an agent control plane, not a generic dashboard shell.
- The repo should treat current dashboard/workspace shell code as provisional until the agentic reset is complete.
