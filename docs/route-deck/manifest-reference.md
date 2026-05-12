# RouteDeck Manifest Reference

Framework source package: `../routedeck/routedeck_core`.

SaaStoAgent adapter/catalog package: `backend/services/route_deck`.

## Objects

`RouteDeckManifest`
: Versioned graph contract with `nodes`, `edges`, `actions`, `policies`, and `test_paths`.

`RouteDeckNodeSpec`
: User-visible node metadata: `id`, `label`, `lane`, `description`, `prompt_placeholder`, `allowed_actions`, `expected_input`, and `recovery_prompt`.

`RouteDeckEdgeSpec`
: Transition metadata: `from`, `to`, `type`, `condition`, optional `action_id`, and user-visible `explanation`.

`RouteDeckActionSpec`
: Action contract: `id`, optional `capability_id`, `label`, `kind`, `category`, `placement`, `fields`, `payload`, `allowed_nodes`, `visibility`, and recovery/sensitive metadata. `capability_id` lets frontend workbench areas bind to backend-authored actions without duplicating action ids.

`RouteDeckFieldSpec`
: Structured input field: `key`, `label`, `field_type`, `required`, `options`, `validation_hint`, and `sensitive`.

`RouteDeckSensitivePolicy`
: Shared masking policy. Current masked payload keys are `credential_value`, `password`, `token`, and `api_key`.

`RouteDeckRuntimeSnapshot`
: Runtime debug state with `current_node`, `reachable_nodes`, `valid_actions`, `blocked_actions`, `executed_nodes`, `progress`, `recovery_prompts`, and `diagnostics`.

## Validation Rules

Run:

```powershell
python -m backend.services.route_deck.validate
```

The validator checks that edges reference real nodes, actions reference real nodes, node action lists reference real actions, every non-terminal node has an input or visible action path, and sensitive form fields are covered by the masking policy.
