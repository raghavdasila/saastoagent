# Shared Contracts

This directory will hold language-neutral schemas exchanged across the Corpus
backend, frontend, RouteDeck boundary, builders, deployed agents, and channels.

`corpus-agent-design-routedeck-manifest.json` is an implementation-owned bridge
from product-semantic Design Studio names to compiled RouteDeck identifiers.
RouteDeck IDs stay here rather than becoming Studio fields. The manifest does
not prescribe handlers, files, transports, storage, or other implementation
choices; `scripts/check_agent_design_parity.py` uses it only to inspect product
shape and boundary parity.

`dependency-provenance/` contains machine-readable records for approved,
exactly pinned product dependencies. These manifests record source, license,
version, wheel hash, local reference evidence, and whether any source snapshot
was imported. The development source checkout manifest additionally owns the
exact RouteDeck and standalone runtime Git repositories and commits consumed by
the Docker build; the bootstrap reads that manifest without selecting a
floating branch.

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
