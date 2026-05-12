# SaaStoAgent v0.1 Context

Last Updated: May 12, 2026
Project: SaaStoAgent v0.1
Status: Unified operator workbench, conversational entry, anonymous workspace chat, backend-owned persistent actions, RouteDeck sibling framework consumption, clean default UI, and RouteDeck debugger are implemented. Active next work is generated REST/OpenAPI upload, inspection, generated tool binding, and learning loop integration.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

---

## Live State

- SaaStoAgent frontend: `http://localhost:3007`.
- SaaStoAgent backend health: `http://localhost:8085/api/health`.
- Standalone RouteDeck example frontend: `http://127.0.0.1:5190`.
- Standalone RouteDeck example backend: `http://127.0.0.1:8096`.
- RouteDeck framework project: `../routedeck/`.
- SaaStoAgent product adapter/catalog: `backend/services/route_deck/`.
- REST/OpenAPI setup remains the active integration path; DB connectors remain out of immediate scope.

## Current Product Shape

- `/`, `/login`, `/register`, and `/w/:workspaceId` mount the unified `OperatorGateway` workbench.
- Anonymous users can ask platform questions, draft setup, sign in, create an account, or chat on direct workspace routes.
- Auth/login/signup remain deterministic graph stages for sensitive work.
- Workspace creation and REST setup remain graph-owned after auth.
- Workspace operator chat remains bridged through `/api/workspaces/{workspaceId}/agent/chat`.
- The workbench zones are capability rail, operator status strip, RouteDeck status strip, central intent spine, next action dock, context lens, evidence drawer, optional canvas, and shared composer.
- Product/operator naming remains `SaaStoAgent` / `Corpus`.

## RouteDeck State

- RouteDeck is now a sibling agentic navigation UX framework under `../routedeck/`.
- RouteDeck owns reusable navigation contracts and debugging UI:
  - `routedeck_core`
  - `@routedeck/react`
  - framework docs and boundary note
  - minimal FastAPI/React Docker example
  - core contract tests
- SaaStoAgent owns product behavior:
  - node/action IDs
  - auth/workspace/setup graph behavior
  - REST setup fields and copy
  - recovery prompts and test paths
- Backend imports RouteDeck primitives from `routedeck_core`.
- Frontend imports reusable debugger UI from `@routedeck/react`.
- Docker uses named sibling build contexts for RouteDeck.
- Docker frontend uses `npm install --no-package-lock` because npm currently crashes on local `file:` dependency lock/symlink handling inside the container.

## Default UI State

- Default entry no longer shows onboarding/checklist content.
- Default entry no longer opens Platform Overview, Knowledge Sources, or Next Best Action before user interaction.
- Platform overview remains available when explicitly requested.
- Canvas collapse uses a narrow rail so the chat column regains width.
- Artifact cards use responsive sizing instead of horizontally squished card rows.
- RouteDeck map remains separate from evidence/trace UI and supports focus/full graph modes plus JSON export.

## Known Gaps

- Generated REST tools are persisted but not yet bound into workspace agent selection/execution.
- Direct `/w/:id` deep links can still bypass graph-owned REST setup until the user explicitly enters setup/auth.
- Autonomy ladder is visible but advisory until REST execution and approval gates are wired.
- Browser QA is still smoke-level; repo-native Playwright/component tests are needed.
- Backend pytest is not yet wired into a reliable local/container test image.
- Platform KB remains small and needs richer source management/citation UX.
- RouteDeck currently covers entry/auth/setup/workspace handoff; REST execution, approvals, QA, and learnings should adopt it next.

## Verification

- RouteDeck import check: passed.
- RouteDeck `python -m pytest tests`: passed.
- RouteDeck minimal example `npm run type-check`: passed.
- RouteDeck minimal example `npm run build`: passed.
- RouteDeck minimal example Docker build/up: passed.
- SaaStoAgent `python -m backend.services.route_deck.validate`: passed.
- SaaStoAgent `python -m compileall backend`: passed.
- SaaStoAgent frontend `npm run type-check`: passed.
- SaaStoAgent frontend `npm run build`: passed.
- SaaStoAgent `docker compose up -d --build backend frontend`: passed.
- Playwright against `http://localhost:3007`: clean default page, RouteDeck Full graph with 11 node groups, no console errors.
- Playwright against `http://127.0.0.1:5190`: styled RouteDeck minimal example rendered.

## Immediate Next Steps

1. Implement REST/OpenAPI upload and inspection for workspace setup.
2. Bind generated REST tools into workspace agent selection/execution.
3. Extend RouteDeck into REST execution, approval gates, QA, and learning candidates.
4. Add repo-native tests for RouteDeck sign in, signup, invalid action recovery, direct workspace auth actions, debugger rendering, and generated REST execution.
5. Add a backend test image or dependency path for reliable pytest execution.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Active plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- Latest log: `logs/20260512_1447_routedeck_sibling_framework_closeout.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_12-05-2026-2-47PM.md`
- Context archive: `context_history/20260512_1447_context_before_routedeck_sibling_closeout.md`
- RouteDeck ADR: `decisions/ADR-007-routedeck-framework-contract.md`
- RouteDeck test index: `test_index/route-deck-contract.md`
- RouteDeck product docs: `docs/route-deck/`
- RouteDeck framework docs: `../routedeck/docs/`
