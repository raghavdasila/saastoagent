# SaaStoAgent v0.1 Context

Last Updated: May 13, 2026 21:18
Project: SaaStoAgent v0.1
Status: Unified operator shell, RouteDeck sibling framework, LangGraph-owned entry runtime, live entry streaming, stream-aware collapsible assistant sections, REST/OpenAPI connection activation, Actions/Entities catalog canvases, first-pass generated REST tool execution, and embedded UI-driven QA are implemented. Workspace creation is now corrected to workspace naming/configuration, not a "SaaS job" prompt.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Live State

- SaaStoAgent frontend: `http://localhost:3007`
- SaaStoAgent backend health: `http://localhost:8085/api/health`
- RouteDeck framework project: `../routedeck/`
- SaaStoAgent RouteDeck product adapter/catalog: `backend/services/route_deck/`
- REST/OpenAPI setup is the active integration path; DB connectors remain out of scope for the current pass.

## Current Product Flow

1. User signs in or creates an account.
2. User creates/selects a workspace by name.
3. User configures API schema connections from the workspace.
4. Connection setup previews a reachable OpenAPI schema, creates the connection, activates the catalog, and generates REST actions/tools.
5. Actions and Entities canvases expose generated REST action and inferred API group surfaces.
6. Operator chat can match generated REST tools, execute read-safe calls when required inputs are available, and stop writes behind approval-required copy.
7. QA panel can drive entry/auth/setup/recovery/connection/catalog/operator scenarios through the visible UI.

## Runtime Shape

- `/`, `/login`, `/register`, and `/w/:workspaceId` mount `OperatorGateway`.
- Entry/auth/workspace/setup handoff executes through `backend/services/entry_runtime/graph_executor.py`.
- Runtime topology remains `turn_start -> route_action -> group boundary -> concrete stage -> finalize_turn -> END`.
- RouteDeck validates submitted actions and provides visible navigation/debug snapshots.
- `workspace_job` remains a legacy internal node id for compatibility, but user-facing copy and tests now treat it as workspace setup/name collection.
- Assistant responses with two or more parsed sections render as collapsible `details`; during streaming, the newest section stays open and previous completed sections collapse.
- Backend entry/setup prompts now prefer explicit Markdown `##` sections, bullets, and fenced JSON.

## QA And Tests

- Embedded QA supports: `open_workspace_view`, `fill_connection_form`, `click_button`, `wait_for_catalog`, `collect_workspace_catalog`, `send_operator_chat`, and `ensure_petstore_connection`.
- QA evidence captures workspace view, catalog totals, Actions/Entities visible text, tool call cards, API status hints, and assistant DOM messages.
- QA panel stays mounted while it hosts the workspace surface under test.
- Regression tests now fail if backend QA scenarios reference unsupported frontend QA actions.
- RouteDeck contract tests now fail if workspace creation copy reintroduces "SaaS job", "operator should own", or "workspace job".

## Verification This Session

- `python -m pytest backend/tests`: passed, 28 tests.
- `python -m compileall backend`: passed.
- `python -m backend.services.route_deck.validate`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed, with existing Vite chunk-size warning.
- Docker backend/frontend rebuilt and healthy.
- Browser smoke verified streaming collapsible behavior, entry auth recovery, positive workspace/API activation, setup back/cancel/edit recovery, Actions/Entities surfaces, read-safe generated tool trace, write approval-required behavior, embedded QA scenarios, and corrected workspace-name flow.

## Known Gaps

- Approval/resume controls for write/destructive/financial generated REST actions are still advisory copy only.
- Workspace-mode RouteDeck snapshots do not yet model REST tool search, execution plans, approval required, executing, result review, or learning review.
- Learning-loop persistence is not yet wired into retrieval/execution refinement.
- The Playwright smokes are still temporary harnesses; promote them into repo-native browser tests.
- `workspace_job` should be renamed internally in a later compatibility/refactor pass if it remains confusing, but it is no longer visible as product copy.

## Immediate Next Steps

1. Add workspace-mode RouteDeck snapshots for generated REST tool search, execution plans, approval required, executing, result review, and learning review.
2. Add approval resume controls and state for write/destructive/financial REST tools.
3. Persist governed learning candidates and feed approved learnings into tool retrieval/execution hints.
4. Promote the temporary Playwright smoke coverage into repo-native browser automation.
5. Consider an internal `workspace_job` -> `workspace_setup` node-id migration once compatibility cost is acceptable.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Active plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- Latest audit: `audits/2026-05-13-langgraph-routedeck-runtime-audit.md`
- Latest log: `logs/20260513_2118_flow_qa_workspace_contract_closeout.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_13-05-2026-9-18PM.md`
- Latest context archive: `context_history/20260513_2118_context_before_flow_qa_workspace_contract_closeout.md`
- RouteDeck ADRs: `decisions/ADR-007-routedeck-framework-contract.md`, `decisions/ADR-008-live-entry-streaming-contract.md`, `decisions/ADR-009-langgraph-owned-entry-runtime.md`
