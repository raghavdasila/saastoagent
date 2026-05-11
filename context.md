# SaaStoAgent v0.1 Context

Last Updated: May 11, 2026
Project: SaaStoAgent v0.1
Status: Unified operator workbench, conversational entry, anonymous workspace chat, responsive context lens, evidence drawer, backend-owned persistent actions, RouteDeck graph-navigation/debugger framework, and post-RouteDeck UI cleanup are implemented. Product/operator naming remains `SaaStoAgent` / `Corpus`. Entry/setup remains graph-owned; workspace chat remains a bridged agent runtime. Active next work is generated REST/OpenAPI upload, inspection, and binding into workspace agent execution.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

---

## Live State

- Frontend Docker/browser URL: `http://localhost:3007`.
- Backend health URL: `http://localhost:8085/api/health`.
- Current local SaaStoAgent dev URL for this cleanup pass: `http://127.0.0.1:5177`.
- Current standalone RouteDeck example URLs: frontend `http://127.0.0.1:5190`, backend `http://127.0.0.1:8096`; now launched with `routedeck_framework/examples/minimal-fastapi-react/docker-compose.yml`.
- Database image: `pgvector/pgvector:pg17`.
- Docker frontend now runs build plus Vite preview to avoid dev-server HMR websocket and host `@fs` alias failures.
- Backend Docker image copies `routedeck_framework/`.
- REST/OpenAPI setup remains the active integration path; DB connectors remain out of immediate scope.

## Current Product Shape

- `/`, `/login`, `/register`, and `/w/:workspaceId` mount the unified `OperatorGateway` workbench.
- Anonymous users can ask platform questions, draft setup, sign in, create an account, or chat on direct workspace routes.
- Auth/login/signup remain deterministic graph stages for sensitive work.
- Workspace creation and REST setup remain graph-owned after auth.
- Workspace operator chat remains bridged through `/api/workspaces/{workspaceId}/agent/chat`.
- Entry messages and setup draft are preserved through auth, workspace creation, REST setup, and operator handoff.
- The workbench zones are capability rail, operator status strip, RouteDeck status strip, central intent spine, next action dock, context lens, evidence drawer, optional canvas, and shared composer.

## RouteDeck State

- RouteDeck replaced the earlier GraphUI naming everywhere.
- Product-specific RouteDeck catalog/adapters live under `backend/services/route_deck/`.
- Reusable framework code lives under `routedeck_framework/`:
  - `routedeck_core`: Python models, runtime helpers, and validation.
  - `react`: TypeScript contracts and `RouteDeckDebugger`.
  - `docs`: framework architecture, minimal example, and packaging roadmap.
  - `examples/minimal-fastapi-react`: minimal FastAPI/React reference.
- `backend/services/route_deck/catalog.py` is the source of truth for visible nodes, edges, actions, fields, sensitive policy, recovery prompts, and test paths.
- `graph_spec.py` delegates visible manifest data to RouteDeck while preserving executor compatibility.
- `ui_actions.py` adapts RouteDeck actions into existing response shapes.
- `stage_io.py` validates submitted `selected_action_id` before stage handlers run.
- Invalid actions recover with visible alternatives instead of dead-end copy.
- `EntryGraphTurnResponse.route_deck_snapshot` exposes current node, reachable nodes, valid/blocked actions, executed nodes, recovery prompts, and diagnostics.
- `python -m backend.services.route_deck.validate` validates the manifest contract.

## Frontend Runtime Shape

- `OperatorGateway.tsx` owns the unified shell and runtime bridge.
- `entryStore.ts` centralizes mode, workspace id, entry/agent sessions, graph state, messages, actions, artifacts, canvas state, RouteDeck snapshot, and selected debug node.
- `operatorExperience.ts` remains the registry-driven capability model.
- Persistent quick actions render through the next action dock and are not cleared during streaming.
- Contextual action cards render inline under assistant turns.
- Sidebar/capability actions dispatch backend action ids from persistent actions first, then contextual actions.
- Direct `/w/:workspaceId` can expose backend-provided auth actions and temporarily switch into entry/auth composer mode without leaving the unified layout.
- RouteDeck navigation is a standalone widget:
  - compact status strip in the workbench
  - side map overlay separate from evidence/trace UI
  - focus graph for current/incoming/outgoing nodes
  - full-site vertical lane graph on a manifest-sized scrollable canvas
  - allowed actions, blocked actions, recovery/input details, and JSON export
- The full-site graph widget is framework-oriented: reusable node sizing, idle/current/previous/next states, width-aware text truncation, and no app-specific fixed node count.
- Default entry UI is cleaner after RouteDeck integration:
  - backend no longer emits onboarding, platform overview, knowledge sources, follow-up chips, or canvas artifacts on the initial empty bootstrap turn.
  - platform overview stays inline when explicitly requested instead of opening as a default canvas-capable artifact.
  - next action dock stays hidden on the entry default until the user has interacted.
  - canvas collapse now switches the workbench to a narrow canvas rail so the chat column regains width.
  - platform overview cards use responsive auto-fit tracks to avoid horizontal squishing.

## Known Gaps

- Generated REST tools are persisted but not yet bound into workspace agent selection/execution.
- Direct `/w/:id` deep links can still bypass graph-owned REST setup until the user explicitly enters setup/auth.
- Autonomy ladder is visible but advisory until REST execution and approval gates are wired.
- Browser QA is still smoke-level; repo-native Playwright/component tests are needed.
- Backend pytest is not yet wired into a reliable local/container test image.
- Platform KB remains small and needs richer source management/citation UX.
- Anonymous workspace chat rate limiting is in-memory and process-local.
- RouteDeck currently covers entry/auth/setup/workspace handoff; REST execution, approvals, QA, and learnings should adopt it later.

## Verification

- `python -m backend.services.route_deck.validate`: passed.
- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Standalone RouteDeck example `npm run type-check`: passed.
- Standalone RouteDeck example `npm run build`: passed.
- Standalone RouteDeck example `docker compose up -d --build`: passed.
- RouteDeck example frontend now includes Tailwind/PostCSS config that scans `../../../react/src` so shared debugger utility classes render in the minimal app.
- Playwright screenshot smoke against `http://127.0.0.1:5177`:
  - confirmed default entry surface no longer shows onboarding checklist.
  - confirmed canvas opens and collapse expands the main chat column from about 746px to about 1048px at 1280px viewport.
- Docker rebuild and Playwright smoke against `http://127.0.0.1:3007`:
  - `docker compose up -d --build backend frontend`: passed.
  - confirmed default entry surface does not show Platform Overview, Knowledge Sources, onboarding/checklist, or Next Best Action.
- Playwright screenshot smoke against `http://127.0.0.1:5190`: confirmed standalone RouteDeck example renders against backend `8096`.
- `docker compose up -d --build frontend`: passed.
- Docker frontend logs show Vite preview serving on container port 3000.
- Docker backend logs show application startup complete and entry requests returning 200.
- Playwright against `http://localhost:3007`:
  - opened RouteDeck `Map`.
  - switched to `Full graph`.
  - confirmed vertical lane order: system, auth, workspace, terminal.
  - confirmed 11 SVG node groups and 24 SVG path elements.
  - confirmed drawer width 1152px and canvas width 1266px.
  - confirmed no same-row node overlap.
  - confirmed no title/badge overlap.
  - confirmed no browser console errors.

## Immediate Next Steps

1. Wire generated REST tools into workspace agent execution.
2. Add repo-native tests for RouteDeck sign in, signup, invalid action recovery, direct workspace auth actions, and debugger rendering.
3. Extend RouteDeck to generated REST execution, approvals, QA, and learnings.
4. Enforce or clearly redirect graph-owned setup from direct `/w/:id` deep links when no ready REST connection exists.
5. Add a backend test image or dependency path for reliable pytest execution.

## References

- Vision: `critical_prompt.md`
- Work prompt: `work_prompt.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- Active plan: `plans/saastoagent_v0_1_workspace_agent_plan.md`
- Latest log: `logs/20260510_1853_routedeck_contract_framework_and_debugger.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_10-05-2026-06-53PM.md`
- Context archive: `context_history/20260510_1853_context_before_routedeck_closeout.md`
- RouteDeck ADR: `decisions/ADR-007-routedeck-framework-contract.md`
- RouteDeck test index: `test_index/route-deck-contract.md`
- RouteDeck packaging error note: `errors/20260510_routedeck_framework_container_packaging.md`
- RouteDeck product docs: `docs/route-deck/`
- RouteDeck framework docs: `routedeck_framework/docs/`
