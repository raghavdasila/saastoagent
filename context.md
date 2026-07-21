# Corpus Current Context

Updated: 2026-07-21

## Repository Boundary

- Authoritative checkout: `D:\Dev\AI Projects\saastoagent-v0.1`.
- Public repository: `https://github.com/raghavdasila/saastoagent`.
- The local ignored `benchmark/saastoagent-v0.1/` is preserved legacy evidence;
  a separate copy remains in agent-core. It is not a new-runtime dependency.

## Current State

- The root contains a feature-free backend/frontend/contracts scaffold.
- The repository-local context architecture is operational and documented in
  `AGENTIC_CODING_GUIDE.md`.
- Source/doc/test ownership and update triggers are mapped in
  `architecture/code-map.md`.
- `docs/corpus-product-definition.md` owns the locked layout and fifteen
  proposed feature boundaries.
- `docs/corpus-routedeck-design-notebook.html` owns the mobile discussion
  artifact and proposed interactive Navgraph.
- `docs/corpus-behavior-reference.md` owns verified benchmark behavior.
- No new runtime, feature implementation, dependency manifest, or database
  exists.

## Locked Product Direction

- Corpus is a chat-first agentic app whose primary agent is node-scoped by
  RouteDeck.
- Corpus deploys agents; deployed agents use RouteDeck for interaction state.
- Sources are API, database, Agentic-GRAG knowledge, and Smithery MCP.
- Sandbox, Evaluation, Channels, Operations, and Learning are first-class owner
  journeys.
- Evaluation owns evalsets and deployment-readiness evidence.
- Memory, policy, revision lineage, model-role bindings, surfaces, access, and
  channel bindings belong to versioned agent configuration.

## Validation Baseline

- `python scripts/validate_design_notebook.py` passes: 15 features, 53 unique
  nodes, 146 edges, zero missing targets, and two syntax-valid inline scripts.
- `python -m unittest discover -v` passes 5 repository-tooling tests.
- These gates prove documentation structure only, not runtime readiness.

## Next Concrete Step

Refine the proposed Corpus Navgraph and Agent Configuration node by node. Then
perform a read-only comparison against the standalone RouteDeck Medusa example
before researching and proposing implementation dependencies.

## Runtime

There is no runnable new Corpus application. No runtime URL exists. The
benchmark remains independently runnable from its ignored local directory.
