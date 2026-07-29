# RouteDeck Feature And Node Design Guide For Corpus

Status: current Corpus design companion

Canonical framework guidance:
[RouteDeck Feature and Node Design Guide](../../../routedeck/docs/feature-and-node-design-guide.md).
Normative contracts:
[RouteDeck Reference](../../../routedeck/docs/route-deck-reference.md).

Use this guide only after a Corpus feature's behavior has been reviewed and
accepted. It helps translate accepted product behavior into a provisional
RouteDeck candidate without letting nodes or framework vocabulary drive the
earlier product design.

## The Mental Model

- A **Feature** is a product ownership boundary.
- A **Node** is a durable product location.
- An **Operation** is an action legal at that location.
- A **Provider** loads authoritative facts needed by an operation.
- A **Guard** deterministically decides whether the operation may proceed.
- A **Handler** performs the product-owned action.
- An **Outcome** reports what actually happened.
- A **Transition** maps that outcome to the next node.
- A **Surface** presents public state and dispatches declared affordances.
- An **AgentPolicy** gives the Corpus agent trusted, scoped guidance.

Corpus owns product meaning, prompts, models, business logic, data, UI, and
external effects. RouteDeck owns legal interaction state, supervised execution,
projection, navigation, review, recovery, and session mechanics.

## When A Behavior Needs A Node

Create a new node when at least one of these changes:

- the durable product location;
- the set of legal operations;
- route, deep-link, history, back, forward, or cancellation behavior;
- authoritative context or entity scope;
- the interaction needs its own durable history entry.

Do not create a node merely for loading, empty, success, expanded, or error UI.
Those are usually surface or status variations inside one node.

Ask:

> What can legally happen here, and what authoritative outcome moves the user
> somewhere else?

If the answer does not change, another node is probably unnecessary.

## Operation Flow

Agent tool calls and surface affordances use the same supervised operation
path. Neither may mutate canonical state directly.

```text
user or surface requests an operation
  -> RouteDeck validates the request and current node
  -> providers load authoritative facts
  -> guards evaluate those facts
  -> review is staged when required
  -> the product handler executes
  -> the handler reports a declared outcome
  -> RouteDeck commits state and follows the matching transition
```

Each operation declares typed inputs and meaningful outcomes such as:

```text
created
already_exists
needs_input
rejected
failed
```

At the current node, every operation/outcome pair maps to exactly one target.
The handler reports the outcome; it does not navigate by itself.

## Providers, Guards, Handlers, And Review

### Providers load facts

A provider loads current product facts or an allowed entity set, such as the
signed-in owner, a ready source revision, an accepted design, or an eligible
deployment version.

The model's memory and browser state are not authoritative product facts.

### Guards enforce permission

A guard is deterministic product code. It decides from the current request and
provider facts whether an operation may continue.

```text
Deploy requested
  -> provider loads the exact version and evaluation result
  -> guard checks that the same version is eligible
  -> pass: deployment handler may run
  -> fail: handler never runs
```

A policy cannot grant permission, and a prompt cannot bypass a guard.

### Handlers perform product work

The handler performs the action only after RouteDeck accepts the request and
passes its providers, guards, and review boundary. It returns a declared result
or fails visibly.

### Review requires a person

A guard answers, "May this operation proceed?"

Review answers, "This operation is permitted, but must a person approve it
before execution?"

Use review for consequential actions such as deployment, deletion, payment, or
another external write that requires explicit confirmation.

## Agent Prompt And Policy Scopes

Keep one stable Corpus prompt for product identity, voice, and universal rules.
Use `AgentPolicy` for guidance that applies only in a particular RouteDeck
scope.

RouteDeck resolves policies from:

- **Framework** - always-active RouteDeck execution and state rules;
- **Feature** - active anywhere inside that Corpus feature;
- **Node** - active at one product location;
- **Capability** - active with a capability declared at that node;
- **Surface** - active while that surface is active;
- **Operation** - active while that operation is currently legal.

On every model call, RouteDeck reloads the session, resolves the active node and
relevant policies, builds safe model context, and exposes only legal tools.

```text
stable Corpus prompt
  + currently relevant trusted policies
  + current public state and legal tools
  -> Corpus agent
```

When the node changes, the policies and tools refresh on the next model call.
Policies guide the model; operations, guards, review, validation, and private
handle resolution enforce behavior.

## Navigation Awareness

The Corpus agent normally needs its current location and legal ways forward,
not the complete Navgraph.

Express navigation through declared operations and transitions. Give navigation
operations clear titles and descriptions. Use suggested actions when an
important next step should be prominent.

Broad knowledge of Corpus features may live in the stable product prompt or a
product-owned read-only knowledge source. Knowing that a destination exists
does not make navigation to it legal.

## Surfaces And Suggested Actions

A surface presents projected public props. Its state-changing affordances
dispatch declared operations through RouteDeck.

A suggested action is an invitation to perform an operation. It does not grant
authority or create another execution path.

Avoid:

- letting a surface mutate canonical state directly;
- turning every legal operation into a button;
- using suggested actions instead of designing navigation;
- copying business logic into the frontend.

## Public And Private State

Only safe public values enter browser projection or model context.

Keep credentials, private form values, database identifiers, and private
bindings on the server. When the browser or model refers to an entity, use an
opaque handle whose session, node, operation, entity kind, allowlist, and
version are checked before resolution.

## Failure And Recovery

For an external write, distinguish:

- definitely not sent;
- possibly sent, with the outcome unknown;
- sent and answered.

An outcome-unknown write enters explicit recovery. Never silently retry it or
claim success. Recovery may refresh trusted facts, reconcile with the external
system, or ask the user to choose an explicit next action.

## Candidate Extraction Order

After the feature behavior is accepted:

1. Identify only durable locations that require nodes.
2. List the operations legal at each node.
3. Define typed inputs and meaningful outcomes.
4. Identify authoritative facts and declare providers.
5. Add deterministic guards and required review boundaries.
6. Map every operation outcome to exactly one target node.
7. Design surfaces and bind affordances to operations.
8. Add suggested actions only where they clarify the next step.
9. Add scoped policies where the Corpus agent needs guidance.
10. Define public/private state and explicit recovery.

Keep the result provisional until the RouteDeck candidate is separately
reviewed and approved.

## Review Checklist

- Does every node represent a meaningful durable location?
- Is every operation legal only where it should be?
- Do UI and agent actions use the same operation path?
- Do providers load current authoritative facts?
- Are permission decisions deterministic guards rather than prompts?
- Is review used for consequential actions that need human approval?
- Does every outcome have one exact transition target?
- Are surfaces limited to presentation and dispatch?
- Are policies guidance rather than security enforcement?
- Does the agent receive only current legal tools?
- Are private identifiers and values excluded from public/model context?
- Are uncertain writes handled without blind retries?

