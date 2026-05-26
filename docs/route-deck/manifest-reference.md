# RouteDeck Manifest And Projection Reference

This reference describes the current SaaStoAgent RouteDeck integration. The
reusable framework contracts live in the sibling `../routedeck` project; the
SaaStoAgent product graph integration lives under `backend/services/app_graph/`.

## Core Objects

`RouteDeckRuntimeState`
: Current runtime object returned by snapshot/dispatch/stream. It contains
graph state, projection, location, status, diagnostics, and projection version.

`RouteDeckProjection`
: UI/agent-facing projection of current graph state. It includes current node,
legal operations, blocked operations, surfaces, navigation, and diagnostics.

`RouteDeckOperation`
: Typed capability that can be selected by UI or a product agent. It includes
operation id, label, description, category, invocation kind, input schema,
readiness metadata, safety/execution metadata, and target node.

`RouteDeckSurface`
: Projected UI surface. SaaStoAgent uses frame, active, and diagnostic roles,
with peer/detail/embedded surface kinds where applicable.

`RouteDeckDispatchInput`
: Client-to-runtime dispatch payload. The runtime validates operation id, args,
graph state, and projection version before commit.

`RouteDeckDispatchResult`
: Runtime dispatch result with the rebuilt runtime state, active surface,
messages, and optional location replacement.

`RouteDeckIntrospection`
: Read-only diagnostics/meta output. It may include blocked operations and
internal details that normal Corpus planning must not expose.

## SaaStoAgent Product Objects

`AppGraphState`
: Product graph state for the owner workbench. It tracks current node, active
SaaS Agent, active connection, pending operation/review state, active surface,
route params, navigation stacks, dirty surfaces, and related graph fields.

`CorpusPlanningContext`
: Product-facing planning context built from the RouteDeck projection for a
normal Corpus turn. It includes current state summary, active surfaces,
surface options, visible entities, and product legal operations.

`visible_entities`
: Product-surface-declared selectable records. For example, a SaaS Agent list
surface can expose rows with labels and a bound `saas_agent.open` operation
payload so Corpus can open what the user sees without asking for hidden ids.

`surface_options`
: Product-facing choices for valid peer/active surface switches. Corpus can
choose these as surface intents; runtime maps them to validated internal route
dispatch.

## Operation Readiness

Important operation fields:

- `id`
- `label`
- `description`
- `category`
- `input_schema`
- `invocation_kind`
- `can_dispatch_now`
- `required_args`
- `missing_args`
- `accepted_arg_keys`
- `safety_class`
- `execution_mode`
- `target_node`

Readiness rules:

- `can_dispatch_now=true` allows direct one-click dispatch only when the
  invocation kind is also appropriate for direct dispatch.
- `missing_args` means a generic button should not blindly dispatch.
- `invocation_kind=hidden` means runtime/diagnostic-only.
- `execution_mode=review` means side effects need a review/proposal path.
- `execution_mode=blocked` means the product should show recovery or ask for a
  prerequisite, not force dispatch.

## Internal Navigation Operations

The app graph still defines internal route operations:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

These belong to runtime/browser/history plumbing and diagnostics. They should be
projected as hidden operations and filtered out of:

- normal Corpus planning `legal_operations`
- product quick-action chips
- public deployed-chat vocabulary

The runtime can still dispatch them internally after validating the requested
node, surface, active agent, and pending review state.

## Normal Corpus Planning Context

Normal planning context includes:

- `current.node_id`
- `current.surface_id`
- active SaaS Agent summary
- active surface summary
- active surfaces
- surface options
- visible entities
- product legal operations

Normal planning context excludes:

- hidden route operations
- blocked operations
- raw endpoint paths
- trace ids
- approval ids
- credential values
- connection-level auth headers as visitor-fillable fields

Diagnostics/meta-introspection can expose richer internals; normal product chat
cannot.

## Validation Expectations

Backend tests should cover:

- projection retains hidden internal route operations for runtime clients
- normal planning context excludes hidden route operations
- normal planning context excludes blocked operations
- visible entity actions keep bound product args
- surface options normalize to validated route dispatch
- invalid surface injection is rejected
- review surfaces cannot be URL-injected without matching pending operation

Frontend tests should cover:

- product quick actions filter hidden/internal route operations
- clickable controls dispatch typed operations
- chat navigation updates RouteDeck state without remounting the shell
- pending approvals polling is gated to relevant UI/state
