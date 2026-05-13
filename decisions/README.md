# Decisions

Architectural Decision Records for SaaStoAgent v0.1.

## Format

`ADR-{number}-{short-name}.md`

## Use ADRs When

- Choosing between multiple valid approaches
- Establishing a durable project pattern
- Making a hard-to-reverse architectural decision

## ADR Index

- `ADR-001-recenter-agentic-product-boundary.md` - use the current Slice 1 shell as technical foundation, then reset the visible product surface before Slice 2
- `ADR-002-agent-first-interface.md` - establish conversation-first workspace interface and progressive capability reveal
- `ADR-003-unified-agentic-operator-experience.md` - unify anonymous entry, auth, setup, and workspace chat into one operator shell
- `ADR-004-backend-owned-persistent-actions.md` - separate contextual graph actions from backend-owned persistent quick actions
- `ADR-005-widget-canvas-artifact-contract.md` - define backend-emitted widgets, markup, and optional canvas artifacts
- `ADR-006-operator-workbench-extensibility-contract.md` - define the user-facing workbench zones, capability registry, evidence drawer, and autonomy ladder contract
- `ADR-007-routedeck-framework-contract.md` - define RouteDeck as the reusable sibling graph-navigation contract, package boundary, and debugger framework
- `ADR-008-live-entry-streaming-contract.md` - require live model/graph streaming for entry assistant text and prohibit fake delayed chunk replay
- `ADR-009-langgraph-owned-entry-runtime.md` - make LangGraph the executable topology while RouteDeck remains the visible navigation contract
