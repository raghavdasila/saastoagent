# RouteDeck Migration Notes

## Moved Into RouteDeck

- Reusable framework contracts moved into the sibling `../routedeck/routedeck_core` package.
- Reusable React debugger moved into the sibling `../routedeck/react` package.
- Node labels, descriptions, lanes, placeholders, expected inputs, and recovery prompts moved into `backend/services/route_deck/catalog.py`.
- Static action metadata moved into the central action catalog.
- Backend action and node ids are exposed through `backend/services/route_deck/ids.py`.
- Frontend entry rail actions bind through RouteDeck `capability_id` metadata instead of duplicated action ids.
- REST setup form field definitions moved into `REST_CONNECTION_FIELDS`.
- Sensitive field metadata is now explicit on field specs and validated against the masking policy.
- Manifest export now includes nodes, edges, actions, policies, and test paths.

## Still In Existing Runtime Files

- `entry_runtime/graph_spec.py` still provides the LangGraph enum compatibility layer and delegates manifest building to RouteDeck.
- `entry_runtime/graph_executor.py` now owns the product-specific LangGraph topology and consumes `routedeck_langgraph` for shared graph wiring.
- `entry_runtime/route_conditions.py` remains the product condition registry that maps RouteDeck edge condition ids onto executable SaaStoAgent checks.
- `entry_runtime/ui_actions.py` remains the adapter that creates `EntryActionCard` instances for the current API shape.
- `backend/services/route_deck/` remains SaaStoAgent-specific and imports framework-level models/helpers from `routedeck_core`.
- `stage_auth.py` and `stage_workspace.py` still own dynamic auth/workspace/setup behavior.
- `OperatorGateway.tsx` still owns streaming, workbench layout, and shell state.

## Follow-Up Refactors

- Move more static auth/setup messages from stage handlers into RouteDeck node or action copy when the copy is truly contract-level rather than domain-specific.
- Replace placeholder-style RouteDeck condition resolvers with richer product checks where edge semantics require more than `state.node == edge.to_stage`.
- Generate TypeScript manifest types or fixtures from the backend contract.
- Extend RouteDeck beyond entry/setup into REST execution, approval gates, QA, and learnings.
