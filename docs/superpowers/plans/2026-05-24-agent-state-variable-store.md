# Agent State Variable Store Replacement Plan

Status: implemented on May 24, 2026.

## Goal

Replace scattered execution-frame state with a generic agent-controlled
variable store under `execution_frame_v1.variables`.

The replacement is not a backwards-compatibility migration. Old dependency and
pending-choice frame structures are removed from production read/write paths.

## Canonical State

The canonical state shape is:

```json
{
  "kind": "result_context",
  "variables": {
    "resource./api/accounts.id": {
      "name": "resource./api/accounts.id",
      "value": "acct_1",
      "visibility": "private",
      "value_type": "string",
      "tags": ["resource_id", "internal_dependency"],
      "aliases": ["id", "account_id"],
      "resource": {
        "collection_path": "/api/accounts",
        "resource_id": "acct_1"
      },
      "origin": {
        "method": "POST",
        "path": "/api/accounts",
        "tool_name": "postAccounts",
        "field_path": "account.id"
      }
    }
  },
  "active_resource_ref": "resource./api/accounts.id"
}
```

Choice state is represented as `choice.<input_name>` variables. Public prompts
show labels only; private values remain hidden in variable metadata.

## Replacement Decisions

- New writes go to `frame["variables"]`.
- Missing-input resolution reads variables directly.
- Opaque path ids are resolved from resource variables by action path.
- Scalar fields such as `region_id` are stored as resource variables with
  origin metadata.
- Pending choices are stored as choice variables.
- `active_resource` remains only as the current workflow routing pointer for
  this slice; it is written by current code and is not an import path for old
  dependency state.
- No old-frame import is provided.
- No production fallback reads old dependency or pending-choice structures.

## Removed

- Dependency-result scalar persistence helpers.
- Pending internal choice helpers.
- Frame-field helper that read dependency field bags.
- Old-session normalization/import logic.
- Tests that asserted old dependency frames keep working.

## Verification

Required checks:

```powershell
python -m pytest backend/tests -q
cd frontend
npm run type-check
npm run e2e:medusa:docker
```

Required scans:

```powershell
git grep -n "normalize_frame_variables\|legacy_internal_dependencies\|pending_internal_choices\|internal_dependencies\|resolve_dependency_id_from_frame" -- backend/services/agent backend/tests
git grep -n -I -E "Medusa|medusa|T-Shirt|tshirt|prod_|variant_01|cart_01|/store/carts|postcarts|pp_system_default|payment-collections|payment-providers|shipping-options|shipping-methods" -- backend/services backend/routes frontend/src
```

Expected:

- The first scan has no matches except unrelated RouteDeck historical tests
  outside agent frame state.
- The hardcoding scan has no production matches.
- Public chat never exposes internal resource ids.
- DB session frame state shows private ids and scalar fields in
  `execution_frame_v1.variables`.
