# 2026-05-13 LangGraph + RouteDeck Runtime Audit

## Scope

Audit the current SaaStoAgent v0.1 entry/auth/setup/runtime against four questions:

1. Are ADRs aligned with the implementation?
2. Is RouteDeck the visible navigation contract?
3. Is execution actually graph-based rather than dispatch-based?
4. Where does hardcoding still remain, and is it acceptable?

## Current Assessment

### 1. ADR alignment

- `ADR-007` matches the current RouteDeck package split and explicitly keeps LangGraph support in the optional `routedeck_langgraph` adapter.
- `ADR-008` matches the current public entry streaming behavior: live model deltas emit through SSE and completed text is not replayed as fake token chunks.
- `ADR-009` now records the runtime boundary that the code already follows: LangGraph owns topology, RouteDeck owns visible navigation.

### 2. RouteDeck as visible navigation contract

Current code path:

- `backend/services/route_deck/catalog.py` is still the center of gravity for node ids, action ids, labels, descriptions, allowed actions, form fields, policies, and test paths.
- `backend/services/entry_runtime/stage_io.py` validates submitted `selected_action_id` before business handlers run.
- `backend/services/entry_runtime/route_conditions.py` plus `routedeck_langgraph.assert_route_transition(...)` prove that handler transitions stay on RouteDeck edges.
- `frontend/src/components/OperatorGateway.tsx` renders backend-owned action metadata and RouteDeck snapshots; it does not jump arbitrary graph nodes.

Verdict:

- The foundation is correct. RouteDeck is not decorative here; it is the visible navigation contract and an executable validation boundary.

### 3. Graph-based execution

Current code path:

- `backend/services/entry_runtime/graph_executor.py` builds the runtime through `routedeck_langgraph.build_route_deck_state_graph(...)`.
- The executable topology is `turn_start -> route_action -> group boundary -> concrete stage -> finalize_turn -> END`.
- Product nodes remain discrete executable LangGraph stages: `bootstrap`, `intent`, `display_name`, `email`, `password`, `workspace_select`, `workspace_job`, `workspace_confirm`, `setup_intro`, `connection_confirm`, `operator_ready`.

Verdict:

- This is now graph-based execution. It is no longer just "dispatch current node and stop."

### 4. Remaining hardcoding

Still centralized but product-specific:

- Stage handler copy in `stage_auth.py` and `stage_workspace.py`.
- Product grouping in `ENTRY_GRAPH_GROUPS`.
- Product condition registry in `route_conditions.py`.
- Public entry LLM/system prompts in `entry_assistant.py` and setup planner prompts in `setup_planner.py`.
- Frontend placement rules in `OperatorGateway.tsx` for where actions, drawers, and RouteDeck views appear.

Why this is acceptable:

- These are product-level semantics, not framework leakage.
- The hardcoding is now mostly centralized and tested, rather than duplicated across frontend controls and backend handlers.

What still needs tightening:

- Some RouteDeck edge resolvers are still shallow state checks rather than richer semantic predicates.
- Some static auth/setup copy could move into RouteDeck metadata if the same text is meant to be framework-visible and stable.
- QA coverage is still mostly smoke-level for browser/runtime interaction even though the embedded QA harness now exists.

## Recommendation

- Keep RouteDeck framework-neutral.
- Keep LangGraph as the primary executable runtime for SaaStoAgent.
- Keep product semantics in SaaStoAgent unless the same pattern is proven across another app.
- Treat the next extraction boundary as adapter quality, not product copy extraction.

That means:

- Strengthen `routedeck_langgraph` validation and graph-builder helpers.
- Extend RouteDeck plus LangGraph into REST execution, approvals, QA, and learnings.
- Do not move auth/workspace/setup copy or SaaStoAgent-specific business branching into RouteDeck core.
