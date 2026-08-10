# Architecture Components

Component documents describe a subsystem's purpose, owner files, public
interfaces, dependent flows, tests, update triggers, invariants, dependencies,
and known risks.

Current component:

- `corpus-shared-infrastructure.md` - Corpus-owned durable job, lifecycle,
  encrypted credential, persistence, configuration, and dependency boundary.

- `corpus-routedeck-boundary.md` — ownership boundary between Corpus product
  behavior and RouteDeck interaction state.

- `standalone-agent-execution-runtime-reference.md` — capabilities, neutral
  future host seam, integration gates, and claim limits for the separately
  proven Agent Execution Runtime. Corpus does not currently depend on it.

- `corpus-feature-architecture.md` - MVC-style vertical feature slices,
  global/shared ownership, cross-feature contracts, and drift enforcement.

Use `component-template.md` when a new high-change or high-risk subsystem earns
its own contract document.
