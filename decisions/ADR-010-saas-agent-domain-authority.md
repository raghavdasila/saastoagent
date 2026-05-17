# ADR-010: SaaS Agent Domain Authority

Date: 2026-05-13

## Status

Accepted

## Context

SaaStoAgent v0.1 originally used `Workspace` as the visible and technical
boundary, with the intent that a workspace could contain agent capability over
time. Recent implementation made the practical product contract clearer:
one operational SaaS surface should be one agent.

Medusa Storefront and Medusa Admin are a concrete example. They expose
different API surfaces, credentials, risk profiles, memories, QA evidence, and
execution policies. Treating them as separate SaaS Agents gives the runtime a
cleaner boundary than placing both under a workspace container.

## Decision

`SaaSAgent` replaces `Workspace` as the product and domain authority.

Each SaaS Agent owns:

- API connections and credentials.
- Generated actions and tools.
- Its own SaaS Agent RouteDeck runtime snapshot.
- Execution plans, approvals, traces, and result reviews.
- RAG sources, generated knowledge, and citations.
- Session memory and durable approved memory.
- Sandbox learning candidates and active learnings.
- QA scenarios, runs, and evidence.

There is no workspace or grouping parent in the foundation implementation.
Grouping can be introduced later as a separate non-authoritative concept if the
product needs it.

The application now has two RouteDeck layers:

- Entry RouteDeck: auth, account entry, SaaS Agent creation/selection, and
  handoff.
- SaaS Agent RouteDeck: selected-agent operations such as connection setup,
  schema preview, catalog activation, action planning, approval, execution,
  result review, memory, learning, and QA.

## Consequences

- Backend tables, models, schemas, API routes, service parameters, and tests
  should move from `workspace` naming to `saas_agent` naming.
- Frontend routes and stores should move from `/w/:workspaceId` and workspace
  state to `/a/:saasAgentId` and SaaS Agent state.
- Medusa Storefront Agent and Medusa Admin Agent are separate agents, not two
  connections inside a shared workspace.
- Per-slice implementation must test, repair, update context artifacts using
  the `work_prompt.md` pattern, and then continue to the next slice unless
  blocked.

## Non-Goals

- Hardened production migration is not required in the first pass.
- A workspace/grouping parent is not introduced in this foundation pass.
- Multi-agent orchestration is deferred until the single-agent authority model
  is working end to end.
