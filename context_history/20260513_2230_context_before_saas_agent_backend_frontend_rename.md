# SaaStoAgent v0.1 Context

Last Updated: May 13, 2026 21:58
Project: SaaStoAgent v0.1
Status: Slice 0 of the SaaS Agent foundation reset is complete; Slice 1 backend rename is starting. The accepted product contract is now `SaaSAgent` as the domain authority. Existing runtime code still contains workspace naming until Slice 1 and Slice 2 rename the backend and frontend surfaces.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Live State

- SaaStoAgent frontend: `http://localhost:3007`
- SaaStoAgent backend health: `http://localhost:8085/api/health`
- RouteDeck framework project: `../routedeck/`
- SaaStoAgent RouteDeck product adapter/catalog: `backend/services/route_deck/`
- Active plan: `plans/saastoagent_v0_1_saas_agent_foundation_plan.md`
- Superseded plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`

## Product Contract

- `SaaSAgent` replaces `Workspace` as the product and domain authority.
- No workspace/grouping parent exists in this foundation pass.
- Medusa Storefront and Medusa Admin are separate SaaS Agents.
- Every SaaS Agent owns its own RouteDeck runtime snapshot, API connections, generated actions/tools, execution traces, RAG corpus, memory, sandbox learnings, QA evidence, and channels.
- The app has two RouteDeck layers:
  - Entry RouteDeck: public entry, auth, SaaS Agent creation/selection, and handoff.
  - SaaS Agent RouteDeck: selected-agent connection setup, schema preview, catalog activation, action planning, approval, execution, result review, memory, learning, and QA.

## Current Implemented Runtime

- `/`, `/login`, `/register`, and `/w/:workspaceId` currently mount `OperatorGateway`.
- Entry/auth/workspace/setup handoff currently executes through `backend/services/entry_runtime/graph_executor.py`.
- Runtime topology remains `turn_start -> route_action -> group boundary -> concrete stage -> finalize_turn -> END`.
- RouteDeck validates submitted actions and provides visible navigation/debug snapshots.
- REST/OpenAPI activation, generated Actions/Entities canvases, first-pass read-safe generated REST tool execution, and advisory approval-required copy are implemented against the current workspace-shaped code.

## Active Implementation Direction

1. Slice 1: rename backend domain, schemas, ownership fields, and routes from Workspace to SaaSAgent.
2. Slice 2: rename frontend route/store/type/shell language from workspace to SaaS Agent.
3. Slice 3: implement SaaS Agent creation with name + editable slug and Medusa Storefront/Admin split.
4. Slice 4+: add per-SaaS-Agent RouteDeck runtime states, execution surface, RAG generation, memory, sandbox learning, and QA/observability.

## Slice Operating Rule

Each slice must be implemented, tested, repaired if broken, then documented before continuing to the next slice. The mini closeout follows `work_prompt.md` style without stopping the session:

- log in `logs/`
- checkpoint in `context_checkpoints/`
- archive `context.md` to `context_history/` when materially changed
- rewrite `context.md`
- update active plan
- update `SYSTEM_FLOW_INDEX.md` when flows changed
- update or add `test_index/`
- add ADR/docs/architecture only when needed

## Known Gaps

- Workspace naming still exists in code until Slice 1 and Slice 2.
- SaaS Agent RouteDeck runtime does not exist yet.
- Approval/resume controls for write/destructive/financial generated REST actions are still advisory copy only.
- RAG generation from OpenAPI/actions/traces is not wired.
- Durable memory and sandbox learning are not yet integrated into execution refinement.
- Browser smokes remain temporary rather than repo-native.

## Verification

- Slice 0 contract file presence check: passed.
- `python -m backend.services.route_deck.validate`: passed.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Active plan: `plans/saastoagent_v0_1_saas_agent_foundation_plan.md`
- Superseded plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- Domain ADR: `decisions/ADR-010-saas-agent-domain-authority.md`
- RouteDeck ADRs: `decisions/ADR-007-routedeck-framework-contract.md`, `decisions/ADR-008-live-entry-streaming-contract.md`, `decisions/ADR-009-langgraph-owned-entry-runtime.md`
- Latest context archive: `context_history/20260513_2158_context_before_saas_agent_domain_authority.md`
