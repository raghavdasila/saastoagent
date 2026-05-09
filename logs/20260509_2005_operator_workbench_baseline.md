# Log - 2026-05-09 8:05 PM - Operator Workbench Baseline

## Accomplished

- Implemented the ADR-006 operator workbench model.
- Added a registry-driven capability model for entry and workspace capabilities.
- Reworked the visible shell around stable zones:
  - capability rail
  - operator status strip
  - central intent spine
  - next action dock
  - context lens
  - evidence drawer
  - optional canvas
- Added an advisory autonomy ladder for future REST execution policy.
- Retained backend-owned action dispatch: the frontend ranks/places actions but does not invent auth/setup/execution commands.
- Stored entry graph `run_id`, `graph_version`, and `graph_manifest` in frontend state for evidence/status surfaces.
- Added artifact renderer support for readiness summaries, tool candidates, execution plans, approval requests, trace summaries, and learning candidates.
- Added ADR-006, updated the flow index, updated the roadmap plan, and added test-index coverage notes.
- Follow-up: changed the visible operator title to `Corpus`.
- Follow-up: removed awkward title-cased workspace naming from generic talk-to-my-SaaS phrasing; those prompts now normalize to `SaaS Operations Workspace`.
- Follow-up: clamped the central chat viewport height so the workbench does not force unnecessary full-page scrolling.

## Files Changed

- `backend/core/schemas/entry.py`
- `frontend/src/components/OperatorGateway.tsx`
- `frontend/src/components/entry/EntryArtifactRenderer.tsx`
- `frontend/src/components/operator/OperatorWorkbench.tsx`
- `frontend/src/components/agent/AgentChat.tsx`
- `frontend/src/components/auth/AuthAgentDesk.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/components/workspace/ActivityBar.tsx`
- `frontend/src/components/workspace/WorkspaceLaunchPad.tsx`
- `frontend/src/lib/entryGraph.ts`
- `frontend/src/lib/operatorExperience.ts`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/stores/entryStore.ts`
- `frontend/src/types/entry.ts`
- `decisions/ADR-006-operator-workbench-extensibility-contract.md`
- `decisions/README.md`
- `SYSTEM_FLOW_INDEX.md`
- `plans/saastoagent_v0_1_workspace_agent_plan.md`
- `test_index/operator-workbench-baseline.md`
- `test_index/README.md`
- `context.md`

## Decisions

- The shell should read as an operator workbench, not chat plus side panels.
- Every future visible capability must define state, primary action/empty state, locked/failure state, evidence surface, and test scenarios.
- The evidence drawer is collapsed by default so first-run UX stays clean.
- The autonomy ladder is visible now but advisory until backend REST execution and approval gates are implemented.

## Validation

- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Repo-wide source search for rejected title/copy patterns and old startup placeholders: no matches in source outside excluded build/cache folders.

## Remaining Work

- Browser QA the visible stack after restarting backend/frontend.
- Add repo-native frontend/browser tests for capability rail state, action dock selection, context lens behavior, evidence drawer, and mobile drawer behavior.
- Continue next slice: generated REST tool inspection and chat binding.
