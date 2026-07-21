# Shared Contracts

This directory will hold language-neutral schemas exchanged across the Corpus
backend, frontend, RouteDeck boundary, builders, deployed agents, and channels.
It contains no implementation yet.

The central aggregate is the versioned **Agent Configuration**:

```text
Agent Configuration
├── identity and instructions
├── RouteDeck Navgraph and node scopes
├── source bindings
├── operations and review policies
├── surfaces
├── model-role bindings
├── memory configuration
├── access and safety policy
├── channel bindings
└── revision lineage
```

Evaluation suites/results and channel contracts will reference an exact agent
configuration revision. They do not silently modify it.
