# 2026-05-13 21:18 - Flow QA And Workspace Contract Closeout

## Summary

Completed the SaaStoAgent v0.1 implementation pass for stream-aware collapsible assistant responses, embedded UI-driven QA coverage, REST/OpenAPI catalog/operator flow validation, and workspace creation contract correction.

## Accomplished

- Made assistant markdown sections render as collapsible `details` during streaming and after completion.
- Changed streaming section behavior so the newest section stays open and previous completed sections collapse; completed messages keep the first section open.
- Added frontend test hooks for collapsible section counts, summaries, streaming state, and active streaming section state.
- Updated backend entry/setup prompts to prefer explicit Markdown `##` sections, bullets, and fenced JSON blocks.
- Expanded frontend QA runner support for workspace views, connection forms, button actions, catalog waits, catalog collection, Petstore seeding, and operator chat.
- Extended QA evidence to include workspace view, catalog totals, visible canvas text, tool call cards, API status evidence, and assistant DOM messages.
- Kept the QA panel mounted while it drives hosted workspace views so new QA scenarios can finish and report.
- Added backend scenario/evaluator coverage for connection preview/activation, Actions/Entities, read-safe generated tool execution, and write approval-required behavior.
- Added a regression guard that fails if backend QA scenarios reference unsupported frontend QA action names.
- Implemented REST catalog inspection and operator-chat generated tool binding from the earlier implementation slice, including Petstore OpenAPI activation and read-safe `findpetsbystatus` execution.
- Corrected the workspace creation product contract: user-facing flow now asks for a workspace name/configuration, not a "SaaS job" or "operator should own" prompt.
- Added RouteDeck regression coverage to prevent reintroducing `SaaS job`, `operator should own`, or `workspace job` in manifest copy.

## Files And Areas Changed

- Backend entry/runtime: `backend/services/entry_runtime/entry_assistant.py`, `setup_planner.py`, `stage_workspace.py`, `graph_spec.py`.
- Backend RouteDeck/QA: `backend/services/route_deck/catalog.py`, `backend/services/qa/domain.py`, `backend/services/qa/service.py`.
- Backend REST/operator: `backend/routes/connections.py`, `backend/services/catalog.py`, `backend/services/agent/rest_operator.py`, `backend/services/agent/chat_service.py`, connection schemas.
- Frontend chat/rendering: `frontend/src/components/agent/CollapsibleMarkdown.tsx`, `MessageBubble.tsx`, `ToolCard.tsx`, `ChatInput.tsx`.
- Frontend workspace/operator: `OperatorGateway.tsx`, `ConnectSetupView.tsx`, `ActionsCanvas.tsx`, `EntitiesCanvas.tsx`, `WorkspaceLaunchPad.tsx`, `DashboardPage.tsx`, `operatorExperience.ts`, workspace/domain/qa types.
- Tests: `backend/tests/test_entry_assistant.py`, `backend/tests/test_qa_service.py`, `backend/tests/test_rest_catalog.py`, `backend/tests/test_route_deck_contract.py`.
- Docs/context: `context.md`, `SYSTEM_FLOW_INDEX.md`, `knowledgebase/patterns/agentic-workbench-ux-research.md`, test-index closeout docs.

## Decisions

- Keep the internal `workspace_job` node id temporarily for compatibility, but treat it as workspace naming/setup in every visible surface.
- Do not add a new ADR for the copy/flow correction; the existing RouteDeck/LangGraph ADRs still cover the architectural contract.
- Treat repo-native Playwright automation as the next QA hardening task; current browser validation used temporary Playwright harnesses.

## Issues Encountered

- The embedded QA runner originally unmounted itself when it opened workspace views. Fixed by hosting the driven workspace surface under the QA panel.
- Read-safe operator chat initially matched an unrelated generated tool because tokenization did not split OpenAPI camelCase/path names or infer enum-like status values. Fixed for the Petstore read-safe path.
- Workspace creation had drifted into a "SaaS job" concept. Fixed copy/runtime/docs/tests to align with the original product flow.

## Verification

- `python -m pytest backend/tests`: passed, 28 tests.
- `python -m compileall backend`: passed.
- `python -m backend.services.route_deck.validate`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed with the existing Vite chunk-size warning.
- `docker compose up -d --build backend frontend`: completed; backend and frontend healthy.
- Browser smoke confirmed:
  - stream-aware collapsible section behavior
  - entry/auth back/cancel/invalid email recovery
  - signup -> workspace name -> workspace confirm
  - Petstore setup -> Connection Confirm -> activation with 19 tools
  - setup Back/Cancel/Edit Details recovery
  - Actions and Entities catalog surfaces
  - read-safe generated tool trace for `findpetsbystatus(status: available)`
  - write approval-required response without silent execution
  - embedded QA pass for old and new scenarios

## Next Steps

1. Add workspace-mode RouteDeck snapshots for generated REST tool search, execution plan, approval required, executing, result review, and learning review.
2. Add approval resume controls and persistence for write/destructive/financial generated REST tools.
3. Persist governed learning candidates and feed approved learnings back into tool retrieval/execution hints.
4. Promote temporary Playwright smoke scripts into repo-native browser tests.
5. Rename internal `workspace_job` to `workspace_setup` in a compatibility-safe refactor if the id continues to cause confusion.
