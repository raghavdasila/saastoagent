# SaaStoAgent v0.1 Context

Last Updated: May 17, 2026 12:14
Project: SaaStoAgent v0.1
Status: Architecture under dispute. The graph-first/agent-first reset has useful backend pieces, but the current UX contract is not aligned with the defining vision. Do not continue incremental UI patching before reading the latest checkpoint and resetting the agent-turn contract.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Start Here

- Latest checkpoint: `context_checkpoints/context_checkpoint_17-05-2026-12-14PM.md`
- Previous context archived at: `context_history/20260517_1214_context_before_agent_ux_architecture_reframe.md`
- Closeout log: `logs/20260517_1214_agent_ux_architecture_reframe_closeout.md`

## Current Problem

The current implementation is technically graph-based but architecturally wrong for the product vision. It behaves like an action router UI with chat decoration.

Concrete mismatch:

- Chat is not the true central agent runtime.
- RouteDeck action eligibility is leaking into visible UI.
- `available_actions` / `persistent_actions` are treated as render-now controls.
- Forms can appear because an action is eligible, not because the user or agent initiated a form lifecycle.
- `home` still behaves like a state-machine foyer/page instead of the opening context inside the agent conversation.
- The no-model/default turn path behaves like a menu repeater rather than an agent.
- Existing tests validate graph plumbing, not the intended agentic UX contract.

## Correct Direction

The next session should reset the contract around agent turns:

- `/turn` is the primary agent runtime.
- The graph owns truth, state, eligibility, and recovery.
- RouteDeck bridges graph state to frontend transformation and diagnostics.
- RouteDeck does not own LLM calls, model keys, or product copy.
- Eligible capabilities are internal, not automatically rendered.
- Visible proposals are agent-authored.
- Forms/work surfaces open only after the user accepts or initiates a proposal.
- Diagnostics can expose graph/RouteDeck internals; product UX cannot.

## Target Response Shape

```ts
type AgentTurnResponse = {
  state: GraphState
  context_lens: ContextLens
  message: AssistantMessage
  capabilities: Capability[]      // possible internally, not auto-rendered
  proposals: Proposal[]           // visible, agent-authored next steps
  active_surface?: Surface        // opened only after initiation/acceptance
  evidence: Evidence[]
  diagnostics: Diagnostics        // hidden unless developer opens it
}
```

## Current Implemented Pieces To Reuse Carefully

- Unified app graph package: `backend/services/app_graph/`
- App graph routes: `backend/routes/app_graph.py`
- RouteDeck manifest/validation pieces in `backend/services/app_graph/manifest.py`
- App-owned router seam: `backend/services/app_graph/router.py`
- Current frontend shell: `frontend/src/components/appGraph/AppGraphShell.tsx`
- Active plan: `plans/saastoagent_v0_1_graph_first_reset_plan.md`
- Current guardrail tests: `backend/tests/test_app_graph_contract.py`

Reuse these only after the agent-turn contract is reset. Do not treat the current frontend behavior as the desired architecture.

## Product Contract

- `SaaSAgent` is the product and domain authority.
- No workspace/grouping parent exists.
- Medusa Storefront and Medusa Admin should be separate SaaS Agents.
- Every SaaS Agent owns its API connections, generated actions/tools, execution traces, RAG corpus, memory, sandbox learnings, QA evidence, and channels.
- One unified backend app graph should own navigation and capability eligibility across entry, SaaS Agent setup, execution, knowledge, memory, learning, QA, and recovery.

## Next Concrete Step

Create a decision-complete ADR/plan for the `AgentTurnResponse` contract. Then refactor backend and frontend around:

1. `capabilities` as internal allowed moves.
2. `proposals` as visible agent-authored next steps.
3. `active_surface` as an initiated/opened surface only.
4. `/action` as accepted proposal/form submission only.
5. tests that prove forms do not render until user acceptance and chat remains conversational.

## Verification From Previous Implementation

The previous implementation passed technical checks, but those checks are insufficient for the vision:

- `$env:PYTHONPATH='.'; pytest backend/tests -q`: 44 passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Browser smoke passed for technical rendering but did not catch the architecture mismatch.

Treat those results as plumbing confidence, not product acceptance.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_17-05-2026-12-14PM.md`
- Active reset plan: `plans/saastoagent_v0_1_graph_first_reset_plan.md`
- Full app graph ADR: `decisions/ADR-011-full-application-graph-ownership.md`
