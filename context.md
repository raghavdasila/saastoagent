# SaaStoAgent v0.1 Context

Last Updated: May 13, 2026
Project: SaaStoAgent v0.1
Status: Unified operator shell, RouteDeck sibling framework, LangGraph-owned entry runtime, embedded UI-driven QA panel, and live public entry streaming are implemented. Active next work is REST/OpenAPI upload, inspection, generated tool binding, execution approval surfaces, and learning-loop integration.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Live State

- SaaStoAgent frontend: `http://localhost:3007`
- SaaStoAgent backend health: `http://localhost:8085/api/health`
- Standalone RouteDeck example frontend: `http://127.0.0.1:5190`
- Standalone RouteDeck example backend: `http://127.0.0.1:8096`
- RouteDeck framework project: `../routedeck/`
- SaaStoAgent RouteDeck product adapter/catalog: `backend/services/route_deck/`
- REST/OpenAPI setup remains the active integration path; DB connectors remain out of immediate scope

## Current Product Shape

- `/`, `/login`, `/register`, and `/w/:workspaceId` mount the unified `OperatorGateway` workbench.
- Anonymous users can ask product questions, draft setup, sign in, create an account, or use backend-provided quick actions on direct workspace routes.
- Auth/login/signup remain deterministic executable LangGraph stages for sensitive work.
- Workspace creation and REST setup remain graph-owned after auth.
- Workspace operator chat remains bridged through `/api/workspaces/{workspaceId}/agent/chat`.
- The workbench zones are capability rail, operator status strip, RouteDeck nav/debug surface, central intent spine, action dock, context lens, evidence drawer, optional canvas, and shared composer.
- Product/operator naming remains `SaaStoAgent` / `Corpus`.

## Runtime State

- Entry/auth/setup/workspace handoff now executes through a central LangGraph topology built by `backend/services/entry_runtime/graph_executor.py`.
- The executable shape is `turn_start -> route_action -> group boundary -> concrete stage -> finalize_turn -> END`.
- RouteDeck remains the visible navigation contract and validates submitted actions before business logic.
- Runtime finalization asserts handler-produced transitions against RouteDeck edges.
- Public entry LLM text now streams live via SSE `message_delta`; completed text is no longer replayed as fake delayed chunks.
- Entry thinking stays inside the streaming assistant bubble.
- The action dock remains visible whenever backend/RouteDeck actions exist, even before a first user message.

## RouteDeck State

- RouteDeck is the sibling framework for agentic navigation UX under `../routedeck/`.
- RouteDeck owns reusable contracts and debugging UI:
  - `routedeck_core`
  - `routedeck_langgraph`
  - `@routedeck/react`
  - framework docs and examples
- SaaStoAgent owns product behavior:
  - node/action ids
  - auth/workspace/setup branching
  - REST setup fields and copy
  - recovery prompts and test paths
- Backend imports framework primitives from `routedeck_core` and `routedeck_langgraph`.
- Frontend imports reusable debugger UI from `@routedeck/react`.

## QA State

- An embedded UI-driven QA panel now exists in the unified shell.
- QA drives the real UI through the composer, visible actions, forms, RouteDeck map, and graph controls rather than direct node jumps.
- Dev-only backend QA endpoints support scenario catalog, domain model, runtime reset, and deterministic evaluation.
- Current test coverage includes backend RouteDeck/runtime parity, auth/workspace recovery, public assistant streaming, and QA service scenarios.

## Known Gaps

- Generated REST tools are persisted but not yet bound into workspace agent selection/execution.
- Direct `/w/:id` deep links can still bypass graph-owned REST setup until the user explicitly enters setup/auth.
- Autonomy ladder is visible but advisory until REST execution and approval gates are wired.
- Browser/runtime QA is stronger than before but still not a full repo-native automated browser suite.
- Some RouteDeck edge resolvers are still shallow state checks and should become richer semantic predicates as REST execution flows are added.
- Product copy in stage handlers is still centralized but not fully moved into RouteDeck metadata; keep only true contract-level copy in the framework boundary.

## Verification

- SaaStoAgent `python -m pytest backend/tests`: passed
- SaaStoAgent `python -m compileall backend`: passed
- SaaStoAgent `python -m backend.services.route_deck.validate`: passed
- SaaStoAgent frontend `npm run type-check`: passed
- SaaStoAgent frontend `npm run build`: passed
- RouteDeck `python -m pytest tests`: passed
- Previous Docker/browser smoke remains valid for the unified shell and RouteDeck map

## Immediate Next Steps

1. Implement REST/OpenAPI upload and inspection for workspace setup.
2. Bind generated REST tools into workspace agent selection/execution.
3. Extend RouteDeck plus LangGraph into REST execution, approval gates, QA results, and learning candidates.
4. Deepen QA from smoke coverage into repo-native browser automation using the embedded QA panel semantics.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Active plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- Latest audit: `audits/2026-05-13-langgraph-routedeck-runtime-audit.md`
- Latest log: `logs/20260513_1301_langgraph_routedeck_runtime_closeout.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_13-05-2026-1-01PM.md`
- Context archive: `context_history/20260513_1301_context_before_langgraph_routedeck_closeout.md`
- RouteDeck ADRs: `decisions/ADR-007-routedeck-framework-contract.md`, `decisions/ADR-008-live-entry-streaming-contract.md`, `decisions/ADR-009-langgraph-owned-entry-runtime.md`
