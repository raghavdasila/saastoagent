# Context Checkpoint - 25 May 2026 08:01 AM IST

## Current State

This checkpoint supersedes `context_checkpoint_24-05-2026-10-32AM.md`.

The project moved from RouteDeck/Corpus boundary cleanup into deployed-agent
API orchestration, execution-frame state replacement, RouteDeck v2 navigation,
Learning review surfaces, and another boundary-hardening pass.

The worktree is not clean. Earlier SaaStoAgent work was committed in:

- `beb8646 rotuer changes (Execution Frame)`
- `c6cc00d wiki added for llm+gnn checkout flow half complete`

One unrelated research commit also exists after the prior closeout:

- `e7d38f8 toolrouter llm+gnn model working`

Treat `e7d38f8` as outside the SaaStoAgent runtime closeout scope.

## Main Runtime Changes

- API orchestration now sits above `rest_operator.py`.
- Router execution facts are consumed by SaaS agent orchestration instead of directly asking buyers for internal ids.
- Missing inputs are classified as internal vs public.
- Internal dependencies can resolve through generated OpenAPI actions.
- Write dependencies without approved policy create `domain_policy_gap` learning candidates.
- Approved policy hints can allow orchestration across visitor sessions for the same SaaS agent/action chain.
- Execution-frame state moved toward `execution_frame_v1.variables`.
- Pending choices and resource ids are stored as private variables with metadata.
- Public chat avoids exposing cart ids, endpoint paths, operation ids, trace ids, and internal slot names.

## RouteDeck And Corpus Changes

- RouteDeck v2 navigation state is present in core/react contracts.
- The React store supports back, forward, cancel, open-node, and switch-surface.
- Learning now has peer surfaces and child/detail nodes:
  - `learning.policy_candidate`
  - `learning.execution_trace`
  - `learning.active_policy`
- Learning approve/reject dispatch through AppGraph operations.
- Instructions save is graph-owned through `instructions.save`.
- Public raw `/api/routedeck/*` product routes were removed.
- Product UI copy now says workflow/surface instead of RouteDeck node.
- RouteDeck debugger no longer labels navgraph edges with action ids.
- `../routedeck/docs/using-routedeck.md` documents human, agent, and developer usage boundaries.

## Validation

Latest current-worktree validation:

- `python -m pytest backend/tests -q` from `saastoagent-v0.1`: `171 passed`
- `npm run type-check` from `saastoagent-v0.1/frontend`: passed
- `npm test` from `agent-lab-powered-projects/routedeck/react`: `13 passed`
- `python -m pytest tests -q` from `agent-lab-powered-projects/routedeck`: `17 passed`
- `git diff --check`: passed

Not validated after latest changes:

- `npm run e2e:medusa:docker`
- full browser checkout flow

## How Totality Was Determined

Do not infer this session only from chat memory. Use this sequence:

1. Read `context.md` and this checkpoint.
2. Use `f995a6c routedeck corpus boundary separation` as the previous SaaStoAgent closeout baseline.
3. Inspect committed SaaStoAgent changes with:
   `git diff --stat f995a6c..HEAD -- agent-lab-powered-projects/saastoagent-v0.1 agent-lab-powered-projects/routedeck`.
4. Inspect current uncommitted changes with:
   `git diff --stat -- agent-lab-powered-projects/saastoagent-v0.1 agent-lab-powered-projects/routedeck`.
5. Inspect `git status --short` before editing.
6. Treat `e7d38f8` as research/toolrouter training work, not SaaStoAgent product runtime work.

## Known Issues

- Full checkout is not done.
- Product list -> selection -> size -> cart is improved but still needs full browser rerun and checkout continuation.
- Multi-step checkout/payment/shipping orchestration is still a later phase.
- Browser screenshots showed the policy-needed cart state but not completed checkout.
- Some RouteDeck v2 and state-variable work is currently uncommitted.

## Next Step

Run the Medusa browser E2E against the current worktree:

```powershell
cd agent-lab-powered-projects/saastoagent-v0.1/frontend
npm run e2e:medusa:docker
```

Then continue checkout orchestration generically:

```text
product/variant resolution
  -> cart create or reuse
  -> add line item
  -> shipping method selection
  -> payment session/provider selection
  -> order completion
```

Keep Medusa as an acceptance fixture only.
