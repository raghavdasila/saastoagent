# Corpus And RouteDeck Boundary

## Purpose

Corpus owns product meaning, its primary chat agent, agent configuration,
feature operations, providers, policies, surfaces, and owner-visible language.

RouteDeck owns generic legal interaction topology and state mechanics used by
Corpus and deployed agents: active node, transitions, operation legality,
review/input/recovery state, projection, identifiers, and diagnostics.

## Owner Files

- `backend/src/corpus/runtime/**` — future node-scoped Corpus agent execution
- `backend/src/corpus/routedeck/**` — future backend integration boundary
- `frontend/src/routedeck/**` — future state/projection bridge
- `frontend/src/surfaces/**` — future typed surface rendering boundary
- `contracts/**` — future language-neutral shared contracts

All listed implementation directories are currently empty scaffolds.

## Public Interfaces

No runtime interface exists yet. Future interfaces must make these boundaries
explicit:

- Corpus supplies product nodes, legal operations, providers, policies,
  surfaces, and versioned agent configuration.
- RouteDeck supplies validated interaction state, legal transitions,
  projections, review/input/recovery mechanics, and diagnostics.
- Surfaces emit typed operations; they do not mutate RouteDeck state directly.

## Core Runtime Rule

```text
Corpus feature definitions own product meaning
  -> RouteDeck owns legal interaction state
    -> the active node scopes the Corpus agent
      -> the frontend renders chat plus typed projected surfaces
```

## Dependent Flows

- Corpus Interaction in `SYSTEM_FLOW_INDEX.md`
- Agent Creation And Release in `SYSTEM_FLOW_INDEX.md`
- Deployed Agent Interaction in `SYSTEM_FLOW_INDEX.md`
- proposed RouteDeck Navgraph in `docs/corpus-routedeck-design-notebook.html`

## Dependencies And Known Risks

- The standalone RouteDeck repository and its Medusa example must be inspected
  against the approved Corpus contract before implementation dependencies are
  selected.
- RouteDeck is new and its documentation is still settling; do not infer an API
  from the preserved benchmark.
- The proposed 53-node Navgraph is not locked. Some status/error candidates may
  become surfaces rather than durable nodes.
- Memory detail and concrete agent-configuration schemas remain deferred.
- The ignored benchmark is evidence only and must never become an import,
  build, runtime, or test dependency of the new application.

## Tests And Evidence

- `python scripts/validate_design_notebook.py` proves the current proposed
  Navgraph counts, edge-target resolution, and inline JavaScript syntax.
- `python -m unittest discover -v` protects the repository-local validators.
- `test_index/README.md` owns command meaning.
- No RouteDeck integration or runtime test exists because no new runtime exists.

## Update Triggers

Update this document and `architecture/code-map.md` when changing:

- Corpus-versus-RouteDeck state, projection, or operation ownership;
- the node-scoping contract for the Corpus agent or deployed agents;
- public schemas, events, adapters, or package boundaries;
- RouteDeck dependencies or compatibility expectations;
- relevant validation commands, known risks, or deferred decisions.

## Invariants

- Corpus remains the primary chat interface across feature nodes.
- RouteDeck does not contain Corpus product literals or source-specific policy.
- Corpus does not reimplement a competing interaction-state store.
- Legal operations are agent/runtime context, not a raw button inventory.
- Product surfaces dispatch typed operations; they do not mutate graph state.
- Deployed agents are agents, not renamed agentic apps.
- Agent Configuration revisions pin all behaviorally relevant contracts.
- Failures remain failures; unavailable dependencies do not silently fall back.
- Benchmark code is not an implementation dependency.

## Current Status

This is an architecture contract only. There is no new runtime implementation.
