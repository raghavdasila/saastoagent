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

Corpus is the SaaStoAgent application definition. It imports RouteDeck and
defines how the product behaves: domain state, user-facing flows, interaction
nodes, operations, guards, handlers, context, and surfaces. This product
definition is the single source of truth for the user-facing application
contract.

RouteDeck implements that definition as a full-stack agentic application
framework. It validates and compiles the app over LangGraph, owns generic
runtime mechanics, interaction and state management, review staging,
projection, navigation, typed events, SSE transport, diagnostics, and the React
store/surface host. The application specification exports the versioned
frontend contract, and RouteDeck coordinates atomic dispatch/idempotency with
durable state/event/outbox semantics. LangGraph remains the execution substrate for nodes,
branching, checkpoints, retries, tools, and streaming.

The intended ownership is:

- Corpus owns SaaStoAgent-specific declarations, conversation behavior, setup
  behavior, SaaS Agent selection, domain handlers, prompts, recovery wording,
  public chat behavior, product surface definitions/components, and product copy.
- RouteDeck owns the shared application compiler/runtime and full typed event
  protocol. Assistant, runtime, tool, surface, and diagnostic events share one
  envelope and ordering model while retaining separate semantic channels and
  visibility rules.
- LangGraph owns execution truth. Corpus must not grow a parallel state-machine,
  event loop, projection builder, or SSE formatter beside RouteDeck.

Do not move Corpus/SaaStoAgent product semantics into reusable RouteDeck
framework code. Do not bypass RouteDeck when exposing agentic graph state to the
frontend. Corpus should use RouteDeck on both backend and frontend as its
agentic application spine and should remain light enough to serve as a product
example, not as the place where missing framework mechanics accumulate.

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
