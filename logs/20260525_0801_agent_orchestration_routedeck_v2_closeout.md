# 2026-05-25 08:01 IST - Agent Orchestration, RouteDeck v2, And Boundary Closeout

## Scope

This closeout covers the work after the previous live SaaStoAgent closeout at
`f995a6c routedeck corpus boundary separation`.

Totality was determined from:

- the last live `context.md` snapshot and `work_prompt.md`
- commits after `f995a6c`
- current uncommitted `git diff --stat`
- current tests and type-check output
- current RouteDeck and SaaStoAgent docs, ADRs, and test indexes

One later commit, `e7d38f8 toolrouter llm+gnn model working`, is outside the
SaaStoAgent runtime closeout scope. It belongs to the research/toolrouter
training line, not this product runtime handoff.

## Committed SaaStoAgent Work Since Prior Closeout

### `beb8646 rotuer changes (Execution Frame)`

- Added execution-frame context handling.
- Added public deployed-chat JSON collapsible rendering.
- Added a Medusa API agent test guide.
- Added execution-frame tests and REST catalog tests.
- Began making result context available for follow-up turns.

### `c6cc00d wiki added for llm+gnn checkout flow half complete`

- Added browser screenshots for product query and cart policy-gap flow.
- Added API orchestration layer and domain policy-gap behavior.
- Added timing instrumentation and message timing UI.
- Added learning-policy evidence surfaces.
- Added owner/admin instructions API.
- Added Medusa/browser validation notes.
- Added tests for API orchestration, timing, and REST catalog behavior.

## Current Uncommitted SaaStoAgent And RouteDeck Work

### Agent-owned API orchestration and policy learning

- Public chat no longer treats internal resource ids as buyer-facing fields.
- Missing inputs are classified as internal or public based on schema/path/parameter context.
- Internal dependencies are resolved through generated OpenAPI actions when possible.
- Domain policy gaps produce learning candidates for owner approval.
- Approved domain policies allow orchestration to continue across sessions for the same SaaS agent/action chain.
- Public responses avoid internal endpoint paths, operation ids, trace ids, and cart ids.

### Agent state variable store

- Added `backend/services/agent/state_variables.py`.
- Replaced scattered frame-state reads with `execution_frame_v1.variables`.
- Stores variables with name, value, visibility, type, tags, aliases, resource metadata, origin, and choice metadata.
- Pending choices are represented as `choice.<input_name>` variables.
- No production import path exists for old dependency-frame state.
- Added `backend/tests/test_state_variables.py`.

### RouteDeck v2 navigation runtime

- Added hierarchy/navigation metadata to RouteDeck models.
- Added client-store navigation state with back, forward, cancel, open-node, and switch-surface operations.
- Added React store navigation support and tests.
- Added child/detail nodes and peer surfaces for Learning review.
- Capability rail now shows descendants without flattening every child node globally.
- Same-node surface switches no longer require the old continue prompt.

### Learning review and policy surfaces

- Learning peer surfaces now separate policy gaps, failed executions, active policies, and rejected candidates.
- Policy candidate, execution trace, and active policy review are detail nodes.
- Learning approve/reject now dispatch through AppGraph/RouteDeck operations instead of direct REST mutations.
- Owner-facing policy evidence shows action chain, risk, dependency, session/trace context, and allowed paths.

### Instructions/system prompt surface

- Instructions are now a graph-owned surface.
- Added `instructions.save` as an AppGraph operation.
- The frontend dispatches `instructions.save`; it no longer directly mutates `/saas-agents/{id}/instructions`.
- The instructions node has dirty policy metadata for future cancel/back handling.

### RouteDeck/Corpus boundary cleanup

- Removed raw public `/api/routedeck/projection` and `/api/routedeck/stream` routes from SaaStoAgent.
- Product UI no longer exposes "RouteDeck node" wording.
- RouteDeck debugger no longer labels navgraph edges with action ids.
- Added `../routedeck/docs/using-routedeck.md` as a practical guide for humans, agents, and developers.
- Linked the guide from RouteDeck runtime and boundary docs.

## Verification Run This Session

Validated from the current worktree:

```powershell
python -m pytest backend/tests -q
```

Result: `171 passed`.

```powershell
npm run type-check
```

Result: passed from `frontend`.

```powershell
npm test
```

Result: `13 passed` from `agent-lab-powered-projects/routedeck/react`.

```powershell
python -m pytest tests -q
```

Result: `17 passed` from `agent-lab-powered-projects/routedeck`.

```powershell
git diff --check
```

Result: passed.

Focused boundary greps were also clean for:

- direct learning approve/reject REST mutation from Corpus UI
- direct instructions save REST mutation from Corpus UI
- public `/api/routedeck/*` routes
- product-visible RouteDeck node copy
- product literals in RouteDeck production source

## Known Gaps

- Full Medusa checkout is not complete. The current state improves policy-gated cart orchestration but checkout still needs additional generated-action chaining and browser validation.
- Browser/Medusa E2E was not rerun after the latest RouteDeck v2 and boundary cleanup.
- Payment/shipping/checkout continuation still needs more generic orchestration beyond the first internal dependency step.
- Some work is uncommitted at closeout time; the next session must inspect `git status` before assuming a clean tree.
- `e7d38f8` is a separate research/training commit and should not be treated as SaaStoAgent runtime validation.

## Restart Point

Start the next session from:

- `context.md`
- `context_checkpoints/context_checkpoint_25-05-2026-08-01AM.md`
- `docs/superpowers/plans/2026-05-24-agent-state-variable-store.md`
- `../routedeck/docs/using-routedeck.md`
- `docs/medusa-api-agent-test-guide.md`

Recommended next step:

1. Review `git status` and separate committed vs uncommitted work.
2. Run `npm run e2e:medusa:docker`.
3. Continue generic checkout orchestration from cart -> shipping -> payment -> order completion without Medusa-specific runtime logic.
