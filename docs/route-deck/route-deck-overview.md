# RouteDeck Overview

RouteDeck is the sibling framework SaaStoAgent uses for graph-driven agentic navigation UX.
LangGraph remains the execution engine. RouteDeck defines what the product shell can show, submit, block, recover, inspect, and test.

The reusable framework lives in `../routedeck/`. SaaStoAgent keeps only product-specific adapters and catalogs under `backend/services/route_deck/`.

The first RouteDeck scope is the entry/auth/setup/workspace handoff flow. Later REST execution, approvals, QA, and learnings should use the same contract instead of adding unrelated UI conventions.

## Ownership

- Backend owns node ids, edge ids, action ids, form fields, recovery prompts, and sensitive-field policy.
- Frontend renders the manifest and runtime snapshot. It may rank and place actions, but it must not invent auth, setup, or execution actions.
- Stage handlers own dynamic business logic only: auth calls, workspace creation, setup planning, connection activation, and handoff.
- The RouteDeck debugger is diagnostic navigation UI. It should reveal control flow without changing runtime decisions and should stay separate from evidence/trace surfaces.

## Ecosystem Position

RouteDeck is internal-first and AG-UI-aligned in shape: manifest, runtime state, valid actions, human input, interrupts/recovery, tool/evidence surfaces, and streaming diagnostics. It is not currently a dependency on AG-UI or CopilotKit.

The debugger renders SVG node-link graphs from the current manifest and runtime snapshot: a focused current-node graph and a top-to-bottom full site graph grouped by lane. SaaStoAgent imports that debugger through the sibling local `@routedeck/react` package and renders it from a right-side RouteDeck map opened by the compact status strip.
