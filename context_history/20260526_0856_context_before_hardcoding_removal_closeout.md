# SaaStoAgent v0.1 Context

Last Updated: May 25, 2026 08:01 IST
Project: SaaStoAgent v0.1
Status: Agent-owned API orchestration, RouteDeck v2 navigation, execution-frame variable state, Learning policy review surfaces, and boundary hardening are implemented in the current worktree. Backend/type/framework tests pass. Full browser Medusa checkout E2E remains pending.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Start Here

- Latest checkpoint: `context_checkpoints/context_checkpoint_25-05-2026-08-01AM.md`
- Previous context archived at:
  `context_history/20260525_0801_context_before_agent_orchestration_routedeck_v2_closeout.md`
- Closeout log:
  `logs/20260525_0801_agent_orchestration_routedeck_v2_closeout.md`
- Dev validation:
  `architecture/dev_validated_docs/2026-05-25_agent_orchestration_routedeck_v2_validation.md`
- Prior RouteDeck boundary checkpoint:
  `context_checkpoints/context_checkpoint_24-05-2026-10-32AM.md`
- RouteDeck human/agent/developer guide:
  `../routedeck/docs/using-routedeck.md`
- RouteDeck framework anchor:
  `../routedeck/docs/agentic-ui-state-runtime.md`
- Boundary ADR:
  `decisions/ADR-013-routedeck-corpus-boundary.md`
- State variable plan:
  `docs/superpowers/plans/2026-05-24-agent-state-variable-store.md`
- Medusa setup/test guide:
  `docs/medusa-api-agent-test-guide.md`
- RouteDeck test index:
  `test_index/route-deck-contract.md`

## Current Worktree Warning

The worktree is not clean. Do not assume all current changes are committed.

Use this sequence before continuing:

```powershell
git status --short
git diff --stat -- agent-lab-powered-projects/saastoagent-v0.1 agent-lab-powered-projects/routedeck
```

The previous SaaStoAgent closeout baseline is:

```text
f995a6c routedeck corpus boundary separation
```

SaaStoAgent commits after that baseline:

- `beb8646 rotuer changes (Execution Frame)`
- `c6cc00d wiki added for llm+gnn checkout flow half complete`

Separate research commit after that baseline:

- `e7d38f8 toolrouter llm+gnn model working`

Treat `e7d38f8` as outside this product runtime handoff.

## Current Architecture

```text
Deployed visitor chat
  -> SaaS agent orchestration layer
    -> generated OpenAPI action router/executor
      -> execution_frame_v1.variables
      -> internal dependency resolution
      -> policy learning when write automation is not approved
        -> public-safe response formatting

Corpus builder app
  -> CorpusGraphRuntime
    -> CorpusRouteDeckRuntime
      -> generic RouteDeck runtime/projection/dispatch contract
        -> RouteDeckStore / @routedeck/react
          -> AppGraphShell
            -> Corpus surfaces
            -> Learning review detail nodes
            -> owner diagnostics
```

Core rules:

- Product graph/runtime services own truth, guards, and commits.
- RouteDeck owns generic projection, navigation, surface, operation, dispatch,
  event, and diagnostics contracts.
- Corpus owns SaaStoAgent builder presentation and product copy.
- SaaSAgent/deployed chat owns visitor-safe domain behavior.
- OpenAPI-generated actions and target API execution remain SaaStoAgent domain
  services, not RouteDeck framework behavior.
- Medusa remains an acceptance fixture only.

## Implemented Since The Prior Closeout

### Agent-Owned API Orchestration

- Added orchestration above `rest_operator.py`.
- Router results are structured execution facts rather than public missing-slot prompts.
- Missing inputs are classified as internal vs public.
- Opaque ids such as cart/resource ids are internal in public chat.
- Internal dependencies can be resolved through generated OpenAPI actions.
- Write dependencies without approval produce `domain_policy_gap` learning candidates.
- Approved policy hints allow orchestration to continue for the same SaaS agent/action chain.

### Execution Frame Variable State

- Added `backend/services/agent/state_variables.py`.
- Canonical state is `execution_frame_v1.variables`.
- Variables carry name, value, visibility, value type, tags, aliases, resource metadata, origin, and choice metadata.
- Pending choices are represented as `choice.<input_name>` variables.
- Old dependency/pending-choice frame state is not imported as a compatibility path.

### RouteDeck v2 Navigation

- RouteDeck schemas now include hierarchy and navigation metadata.
- React RouteDeck store supports:
  - `route.back`
  - `route.forward`
  - `route.cancel`
  - `route.open_node`
  - `route.switch_surface`
- Learning has peer surfaces and child/detail nodes.
- Capability rail uses projected hierarchy instead of local hardcoding.
- RouteDeck debugger no longer renders action ids as navgraph edge labels.

### Learning And Policy Review

- Learning surfaces split policy gaps, failed executions, active policies, and rejected candidates.
- Policy candidates open detail nodes with owner evidence.
- Approve/reject now dispatch through AppGraph/RouteDeck operations.
- Failed executions remain separate from policy candidates.

### Instructions/System Prompt Surface

- Instructions are a graph-owned node/surface.
- `instructions.save` is an AppGraph operation.
- Corpus UI no longer directly mutates the instructions REST route.

### RouteDeck/Corpus Boundary Cleanup

- Removed public product `/api/routedeck/projection` and `/api/routedeck/stream`.
- Product UI no longer says "RouteDeck node".
- RouteDeck production source scan is clean for SaaStoAgent/Corpus/Medusa literals.
- Added `../routedeck/docs/using-routedeck.md`.

## Verification

Latest current-worktree verification:

- `python -m pytest backend/tests -q`
  - Result: `171 passed`
- `npm run type-check` from `frontend`
  - Result: passed
- `npm test` from `agent-lab-powered-projects/routedeck/react`
  - Result: `13 passed`
- `python -m pytest tests -q` from `agent-lab-powered-projects/routedeck`
  - Result: `17 passed`
- `git diff --check`
  - Result: passed

Boundary scans were clean for direct Corpus UI learning mutation, direct
instructions mutation, raw `/api/routedeck/*` route declarations, product
RouteDeck-node copy, and product literals in RouteDeck production source.

## Known Issues To Carry Forward

### Full Checkout Still Pending

Cart policy learning is improved, but full checkout is not complete.

Still needed:

- cart creation/reuse browser validation
- add-line-item validation after owner policy approval
- shipping method selection
- payment session/provider selection
- order completion
- public-safe transcript validation through the full flow

### Browser E2E Not Rerun After Latest Work

Run:

```powershell
cd agent-lab-powered-projects/saastoagent-v0.1/frontend
npm run e2e:medusa:docker
```

Do not claim product E2E is green until this passes on the current worktree.

### Checkout Must Stay Generic

Do not hardcode Medusa product, variant, cart, shipping, or payment behavior.
The flow must stay OpenAPI/action/schema driven.

### Worktree Is Broad

Some RouteDeck v2, state-variable, boundary, and docs changes are uncommitted.
Review before editing or committing.

## Next Concrete Step

Run the Medusa browser E2E against the current worktree. If it fails, fix only
generic orchestration/state/policy issues, not Medusa-specific shortcuts.

Then continue:

```text
product/variant resolution
  -> cart create or reuse
  -> add line item
  -> shipping method selection
  -> payment session/provider selection
  -> order completion
```

## Anti-Drift Reminder

- Public chat never exposes internal resource ids, operation ids, endpoint paths, trace ids, or raw tool labels.
- RouteDeck framework stays product-neutral.
- Corpus and SaaSAgent product services own product behavior.
- Graph/AppGraph operations own side effects from RouteDeck-backed UI.
- `execution_frame_v1.variables` is the current agent state shape.
- Medusa is an acceptance fixture, not a runtime dependency.
