# Corpus And RouteDeck Boundary

## Responsibility

Corpus owns product meaning, its primary chat agent, agent configuration,
feature operations, providers, policies, surfaces, and owner-visible language.

RouteDeck owns the generic legal interaction topology and state mechanics used
by Corpus and deployed agents: active node, transitions, operation legality,
review/input/recovery state, projection, identifiers, and diagnostics.

## Core Runtime Rule

```text
Corpus feature definitions own product meaning
  -> RouteDeck owns legal interaction state
    -> the active node scopes the Corpus agent
      -> the frontend renders chat plus typed projected surfaces
```

## Invariants

- Corpus remains the primary chat interface across feature nodes.
- RouteDeck does not contain Corpus product literals or source-specific policy.
- Corpus does not reimplement a competing interaction-state store.
- Legal operations are agent/runtime context, not a raw button inventory.
- Product surfaces dispatch typed operations; they do not mutate graph state.
- Deployed agents are agents, not renamed agentic apps.
- Agent Configuration revisions pin all behaviorally relevant contracts.
- Benchmark code is not an implementation dependency.

## Current Status

This is an architecture contract only. There is no new runtime implementation.
