# Context Archive - 2026-05-13 21:18

Previous: `20260512_1447_context_before_routedeck_sibling_closeout.md`
Next: `../context.md`

# SaaStoAgent v0.1 Context

Last Updated: May 13, 2026
Project: SaaStoAgent v0.1
Status: Unified operator shell, RouteDeck sibling framework, LangGraph-owned entry runtime, embedded UI-driven QA panel, live public entry streaming, stream-aware collapsible assistant sections, REST catalog inspection, lightweight entity/action canvases, and first-pass generated REST tool execution are implemented. Active next work is deeper workspace RouteDeck execution states, approval resume controls, and learning-loop persistence.
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
- Assistant responses with multiple markdown heading sections now render as collapsible sections during streaming and after completion; backend setup/entry prompts now explicitly prefer `##` markdown sections, bullets, and fenced JSON.
- Activated REST APIs now expose workspace catalog, Actions, Entities, and read-safe generated-tool execution through the operator chat path.
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
- QA drives the real UI through the composer, visible actions, workspace view switching, connection forms, generated catalog waits, operator chat, RouteDeck map, and graph controls rather than direct node jumps.
- Dev-only backend QA endpoints support scenario catalog, domain model, runtime reset, and deterministic evaluation.
- Current test coverage includes backend RouteDeck/runtime parity, auth/workspace recovery, public assistant streaming, REST catalog behavior, QA service scenarios for connection preview, catalog canvases, generated tool traces, approval-required write behavior, and a guard that backend QA scenario actions are implemented by the frontend runner.

## Known Gaps

- Generated REST tools are persisted, inspectable, and bound into a first-pass workspace chat execution path for matched read-safe API tasks.
- Direct `/w/:id` deep links can still bypass graph-owned REST setup until the user explicitly enters setup/auth.
- Autonomy ladder is visible but advisory until approval resume gates and learning review controls are fully wired.
- Browser/runtime QA is stronger than before; the embedded QA runner now executes connection/catalog/operator action names, but repo-native Playwright tests are still the next automation step.
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

1. Add workspace-mode RouteDeck snapshots for REST tool search, execution plans, approval required, executing, result review, and learning review.
2. Add approval resume controls for write/destructive/financial REST tools.
3. Persist governed learning candidates and feed approved learnings back into retrieval/execution hints.
4. Promote the current Playwright smoke harnesses into repo-native browser automation using the embedded QA panel semantics.

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
