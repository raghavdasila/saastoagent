# SaaStoAgent v0.1 Vision

## What This Is

SaaStoAgent v0.1 is a REST-only workspace agent product.

The product model is simple:

- One workspace owns one SaaS agent
- A workspace contains the connected REST sources, inferred entities, generated actions/tools, chat runtime, QA surface, and a lightweight feedback loop for error capture, tuning, and self-learning
- The agent is built by reusing proven code paths from the existing `saastoagent` and `foundation-agent` projects

## Scope

v0.1 includes:

1. Workspace-as-agent shell
2. REST onboarding and action catalog
3. Simplified entity explorer
4. REST tool-finder chat
5. Agentic REST execution
6. QA, error capture, tuning, and self-learning loop

## Non-Goals

The following are explicitly out of scope for v0.1:

- Database connectors
- GraphQL connectors
- MCP connectors
- Vector DB connectors
- The separate `AgentSystem` product model
- Full resource-graph canvas/debugger UX as a primary product surface

## Product Principles

1. Reuse proven code, not abstract ideas
2. Keep the visible product model simple
3. Prefer structural retrieval over fuzzy scoring where possible
4. Make entity/action understanding first-class, but keep the UX lighter than the old graph product
5. Keep QA as an operator-facing product capability, not an afterthought
6. Make failure capture, tuning, and learning simple enough to use continuously

## RouteDeck And Corpus Rule

RouteDeck is the reusable state management solution for agentic apps. It is not
just navigation, a debugger, or a UI helper. SaaStoAgent should import and use
RouteDeck the way applications use Redux, MobX, or React Query: as the shared
state layer that connects backend agent graph state to frontend React state.

The intended ownership is:

- LangGraph and backend services execute the agent flow and produce authoritative graph/runtime state.
- RouteDeck owns the generic agentic state contract: projections, operations,
  operation readiness, blocked state, surfaces, events, runtime snapshots,
  diagnostics, and React-facing store/hooks/debugger bindings.
- Corpus is the SaaStoAgent product/application layer that consumes RouteDeck.
  Corpus owns SaaStoAgent-specific conversation, setup behavior, SaaS Agent
  selection, recovery wording, public chat behavior, and product surface copy.

Do not move Corpus/SaaStoAgent product semantics into reusable RouteDeck
framework code. Do not bypass RouteDeck when exposing agentic graph state to the
frontend. Corpus should use RouteDeck on both backend and frontend as its
agentic application state spine.

## Continuous Improvement Loop

SaaStoAgent v0.1 must not stop at execution. It needs a simple closed loop for:

1. catching failed or weak agent outcomes
2. inspecting the trace and the reason for failure
3. tuning prompts, tool exposure, routing behavior, or approval behavior
4. persisting approved learnings so the next run is better

Self-learning in v0.1 means governed accumulation of validated learnings, not uncontrolled autonomous drift.

## Delivery Strategy

Build by vertical slices. Each slice must be usable end to end before moving on.

### Slice Order

1. Workspace-as-agent shell
2. REST onboarding and action catalog
3. Simplified entity explorer
4. REST tool-finder chat
5. Agentic REST execution
6. QA, tuning, and self-learning loop
7. REST-only hardening

## Implementation Strategy

Use a code-as-context approach:

- Copy and adapt the smallest working surfaces from `saastoagent`
- Use `foundation-agent` only where its chat/session shell is cleaner
- Keep the new project clean instead of inheriting every legacy surface

## Success Condition

At the end of v0.1, a user should be able to:

1. Create a workspace
2. Connect a REST API
3. Inspect entities and actions inferred from that API
4. Ask the agent which actions are relevant for a request
5. Let the agent execute a real REST workflow
6. Run a QA loop against that workspace agent
7. Catch failures, tune the agent, and persist validated learnings for future runs
