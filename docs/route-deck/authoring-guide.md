# RouteDeck Authoring Guide

## Add A Node

1. Add a `RouteDeckNodeSpec` in `backend/services/route_deck/catalog.py`.
2. Add any new edges from or to the node.
3. Add the runtime handler to `entry_runtime/graph_executor.py` if it is executable.
4. Add expected input or at least one visible action.
5. Add a recovery prompt that tells the user how to continue from the node.

## Add An Action

1. Add a `RouteDeckActionSpec` in the action catalog.
2. Set `allowed_nodes` to the exact nodes that may accept the action.
3. Set `capability_id` when a stable frontend rail/workbench item should trigger this action.
4. Use `visibility="persistent"` only for actions that should survive contextual action clearing.
5. For forms, define `RouteDeckFieldSpec` entries in the action spec.
5. Use `sensitive=True` for fields containing credentials or passwords.

## Add A Form

Forms should be backend-authored. The frontend renders the fields from `EntryActionCard.fields`.

Never hardcode a frontend-only auth/setup form. If the backend cannot validate the submitted action from the current node, the runtime returns a RouteDeck recovery message and visible valid actions.

## Update Frontend Copy

Prefer RouteDeck node/action fields first:

- Composer placeholder: `node.prompt_placeholder`
- Debug/help text: `node.description`, `node.expected_input`, `node.recovery_prompt`
- Buttons/forms/chips: `RouteDeckActionSpec` converted to `EntryActionCard`

Capability labels can remain in `operatorExperience.ts` when they describe stable workbench areas rather than graph actions. Capability-to-action binding should use `RouteDeckActionSpec.capability_id`, not frontend copies of action ids.
