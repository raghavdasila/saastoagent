# ADR-009 - LangGraph-Owned Entry Runtime

Date: 2026-05-13
Status: Accepted

## Context

The entry/auth/setup runtime initially behaved like a dispatch wrapper: resolve the current node, run one handler, then end. RouteDeck made the user-facing navigation contract visible, but the executable topology still lived partly in product handler conventions and partly in validation helpers.

That split made it too easy to drift back into hardcoded frontend or handler-local navigation: visible actions could disappear, typed auth/setup nodes could lose recovery controls, and RouteDeck edges could describe navigation that the runtime did not prove executable.

## Decision

SaaStoAgent entry/auth/setup now uses a central LangGraph topology for executable control flow, with RouteDeck as the visible navigation contract.

- LangGraph owns the execution topology: `turn_start -> route_action -> group boundary -> concrete stage -> finalize_turn`.
- RouteDeck owns the manifest: visible nodes, edges, actions, fields, sensitive policy, recovery prompts, test paths, and runtime snapshots.
- `routedeck_langgraph` is the optional adapter boundary for manifest/handler/condition parity, transition assertions, and common graph wiring.
- SaaStoAgent product logic stays in `backend/services/entry_runtime/` and `backend/services/route_deck/`; reusable graph/framework logic belongs in sibling RouteDeck.
- Submitted `selected_action_id` values are validated against the RouteDeck node before business handlers run.
- Handler-produced `next_node`/`node` transitions are checked against RouteDeck edges during finalization.
- Frontend navigation controls render backend/RouteDeck actions and submit action ids. The UI must not jump arbitrary graph nodes or invent auth/setup operations locally.

## Consequences

- RouteDeck and LangGraph must be tested together: every manifest node needs a handler, every condition needs a resolver, and every executable transition must be a RouteDeck edge.
- Display grouping is allowed for debugging/readability, but concrete runtime nodes remain executable LangGraph stages.
- Product code may contain deterministic copy and domain handlers, but navigation ownership should stay centralized in RouteDeck plus LangGraph wiring rather than scattered hardcoded control flow.
- Future REST execution, approval, QA, and learning flows should follow the same pattern before adding new frontend action conventions.
