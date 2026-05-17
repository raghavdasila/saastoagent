# SaaStoAgent v0.1 SaaS Agent Foundation Plan

## Summary

Build the working foundation around `SaaSAgent` as the only product/domain
authority. Each SaaS Agent owns its RouteDeck runtime, API connections,
generated tools, execution state, RAG corpus, memories, sandbox learnings, QA
evidence, and channels. Medusa Storefront and Medusa Admin are separate SaaS
Agents.

This is a working foundation plan, not a production-hardening plan.

## Standing Slice Rule

Each slice must finish with this loop before the next slice starts:

1. Implement the slice.
2. Run the slice's relevant checks.
3. Fix regressions introduced by the slice.
4. Update tracking artifacts using the `work_prompt.md` pattern:
   - `logs/`
   - `context_checkpoints/`
   - `context_history/` when `context.md` materially changes
   - `context.md`
   - this active plan
   - `SYSTEM_FLOW_INDEX.md` when runtime/API/UX flow changes
   - `test_index/`
   - ADR/docs/architecture only when needed
5. Continue directly to the next slice unless blocked by failing checks,
   unclear product decisions, or external dependencies.

## Runtime Model

Two RouteDeck layers are required:

- Entry RouteDeck handles public entry, auth, SaaS Agent creation/selection, and
  handoff.
- SaaS Agent RouteDeck is scoped to one `saas_agent_id` and owns the selected
  agent's operating state: connection setup, schema preview, activation,
  catalog inspection, execution planning, input collection, approval,
  execution, result review, memory, sandbox learning, and QA.

The SaaS Agent RouteDeck can use a common manifest/template, but every SaaS
Agent has its own runtime snapshot, progress, evidence, and active node.

## Slice Plan

### Slice 0 - Product Contract Reset

Status: **COMPLETE** as of 2026-05-13.

Implement:

- Add ADR for `SaaSAgent` replacing `Workspace`.
- Make this plan the active plan.
- Update context, flow index, and test index to record the new authority model.
- Record that every SaaS Agent has its own RouteDeck runtime.

Done when:

- ADR-010 exists.
- `context.md` points to this plan.
- `SYSTEM_FLOW_INDEX.md` no longer presents workspace as the future authority.
- Slice closeout artifacts exist and checks have run.

### Slice 1 - Backend SaaS Agent Domain Rename

Status: **COMPLETE** as of 2026-05-13.

Implement:

- Rename backend domain from `Workspace` to `SaaSAgent`.
- Rename `WorkspaceMember`/`WorkspaceRole` to SaaS Agent equivalents.
- Rename `workspace_id` ownership fields to `saas_agent_id` across connections,
  activation state, action nodes, generated tools, sessions, messages,
  documents, chunks, memories, QA seeds, stats, and tenancy helpers.
- Replace `/api/workspaces` with `/api/saas-agents`.
- Add an explicit migration/reset path for local dev data.

Done when:

- Backend tests pass.
- SaaS Agent create/list/get/stats APIs work.
- Connections and chat are scoped by `saas_agent_id`.
- Backend responses do not expose workspace as the product concept.

### Slice 2 - Frontend SaaS Agent Shell Rename

Status: **COMPLETE** as of 2026-05-13.

Implement:

- Replace workspace store/types/routes with SaaS Agent equivalents.
- Change direct route from `/w/:workspaceId` to `/agents/:saasAgentId`.
- Update shell, status strip, capability rail, context lens, QA panel,
  Connections, Actions, Entities, Knowledge Base, and Sessions & Memory copy.
- Keep behavior intact while changing the domain language.

Done when:

- Frontend type-check and build pass.
- User can create/open a SaaS Agent and land in the same operator shell.
- Primary UI no longer says workspace.

### Slice 3 - SaaS Agent Creation And Medusa Split

Status: **PARTIAL / FOUNDATION COMPLETE** as of 2026-05-13.

Implement:

- Entry RouteDeck collects SaaS Agent name and editable slug.
- Entry graph creates the SaaS Agent and hands off to SaaS Agent RouteDeck.
- Add Medusa Storefront and Medusa Admin presets.
- Treat Storefront and Admin as separate SaaS Agents.
- Preview both OpenAPI specs; activate Storefront first.

Done when:

- `Medusa Storefront Agent` and `Medusa Admin Agent` can be created separately. **Implemented in dashboard presets.**
- SaaS Agent name + slug can be reviewed and edited before creation. **Implemented in dashboard launch pad and Entry RouteDeck launch form.**
- Storefront/Admin API connection details can be prefilled. **Implemented in Connections presets.**
- Storefront activation produces generated actions/tools. **Pending live Medusa target verification.**
- Admin preview works and does not pretend auth is solved. **Pending live Medusa target verification.**

### Slice 4 - SaaS Agent RouteDeck V1

Status: **COMPLETE** as of 2026-05-13.

Implement:

- Add SaaS Agent RouteDeck manifest/runtime snapshot. **Implemented in `backend/services/saas_agent_route_deck.py`.**
- Initial nodes:
  - `agent_bootstrap`
  - `needs_connection`
  - `connection_type`
  - `schema_preview`
  - `catalog_activation`
  - `catalog_ready`
  - `action_inspection`
  - `execution_planning`
  - `needs_input`
  - `approval_required`
  - `executing`
  - `result_review`
  - `learning_review`
- Let the frontend RouteDeck widget switch between Entry RouteDeck and selected
  SaaS Agent RouteDeck. **Implemented in `OperatorGateway` using `/api/saas-agents/{id}/route-deck`.**
- Show current SaaS Agent context in the lens: agent name, slug, active node,
  active connection, capability, draft, and next actions. **Implemented for agent identity, current node, working-on summary, connection/action/tool counts, latest connection, and valid RouteDeck actions. Draft/action-specific execution context lands in Slice 5.**

Done when:

- RouteDeck shows where the selected SaaS Agent is operationally. **Done.**
- Context lens answers what agent is selected, what it is doing, and what can
  happen next. **Done for setup/catalog states; execution-specific context continues in Slice 5.**

### Slice 5 - Working Execution Surface

Status: **COMPLETE** as of 2026-05-13.

Implement:

- Move first-pass REST execution into visible SaaS Agent RouteDeck states. **Implemented through latest execution trace inference in `saas_agent_route_deck.py`.**
- Show candidate action, required inputs, inferred inputs, risk, approval
  requirement, execution progress, result review, and trace evidence. **Implemented in persisted `agent_execution_traces` plus assistant/tool trace output.**
- Add approve/cancel/resume controls for write/destructive/financial actions. **Implemented as chat controls: `approve <trace>` and `cancel <trace>`.**
- Persist structured execution traces. **Implemented as `AgentExecutionTrace`.**

Done when:

- Read-safe Storefront action can execute or fail with a clear trace. **Done in generated REST operator path.**
- Risky Admin/Store action stops at approval. **Done.**
- Result review appears in RouteDeck and the evidence drawer. **RouteDeck result-review is done; evidence drawer continues to use message tool cards until Slice 9 export hardening.**

### Slice 6 - RAG Generation V1

Status: **COMPLETE** as of 2026-05-13.

Implement:

- Generate retrievable knowledge per SaaS Agent from OpenAPI specs, generated
  actions/tools, execution traces, and uploaded docs. **Implemented for generated API catalog, generated tools/actions, execution traces, and uploaded docs.**
- Store embeddings per `saas_agent_id`. **Implemented through existing `agent_document_chunks.saas_agent_id`; local deterministic embeddings are used when no OpenAI key is configured.**
- Add citations for OpenAPI/action/doc sources. **Implemented through generated document names and chunk metadata; chat citations already surface document name/id.**
- Feed retrieval into chat and tool selection. **Chat retrieval uses the existing RAG tool; tool selection still primarily uses generated tool matching and trace/context will be improved by later ranking work.**

Done when:

- Agent can answer what the connected SaaS surface can do. **Done through generated API catalog RAG.**
- Medusa Storefront operations are explained with citations. **Implemented at generated-catalog level; live Medusa verification is pending.**
- RAG does not leak across SaaS Agents. **Done by `saas_agent_id` filters.**

### Slice 7 - Memory Systems V1

Status: **COMPLETE** as of 2026-05-13.

Implement:

- Session memory for current conversations. **Implemented through existing session-scoped `AgentMemory` and memory context injection.**
- Durable user-approved memory. **Implemented through explicit memory API/UI and direct chat `remember ...` command.**
- Memory inspection and deletion in Sessions & Memory. **Implemented in the admin panel.**
- Memory injection into chat/execution context. **Implemented through existing `get_session_context` plus deterministic direct recall.**

Done when:

- User can ask a SaaS Agent to remember a fact. **Done.**
- Same SaaS Agent recalls it later. **Done through direct recall and injected memory context.**
- Another SaaS Agent cannot see it. **Done by `saas_agent_id` storage and recall filters.**

### Slice 8 - Sandbox Learning V1

Status: **COMPLETE** as of 2026-05-13.

Implement:

- Create learning candidates from failed executions, corrected tool choices,
  repeated missing inputs, and user feedback. **Implemented for failed executions and missing inputs; explicit correction/user-feedback capture can build on the same model.**
- Add learning states: proposed, approved, rejected, active. **Implemented as status values.**
- Approved learnings influence retrieval/tool selection. **Implemented as generated REST ranking hints.**
- Rejected learnings remain inert. **Done.**

Done when:

- Failed or corrected execution creates a candidate. **Done for failed/missing-input traces.**
- User can approve/reject it. **Done in Learn panel and API.**
- Approved learning changes future hints or ranking. **Done through candidate ranking bonus.**

### Slice 9 - QA And Observability

Status: **COMPLETE / ESSENTIAL VALIDATED** as of 2026-05-14.

Implement:

- QA scenarios for SaaS Agent creation, Medusa Storefront/Admin split,
  connection preview/activation, RouteDeck transitions, read execution,
  approval stop, RAG answer, memory save/recall, and learning review. **Implemented in QA scenario catalog at foundation level; live Medusa/browser smoke remains pending.**
- Evidence export includes RouteDeck snapshot, active SaaS Agent, tool traces,
  memory events, learning events, API failures, and console failures. **Existing QA evaluator covers RouteDeck, active views, API responses, tool traces, visible text, and console failures; richer export hardening remains post-foundation.**

Done when:

- Backend tests pass. **Done.**
- Frontend type-check/build pass. **Done.**
- Browser smoke proves: create SaaS Agent, connect Medusa Storefront, generate
  actions/RAG, execute read task, capture trace, save memory, propose learning. **Foundation path validated through embedded browser QA and direct Petstore API e2e; live Medusa Storefront/Admin verification remains pending.**

Validation addendum:

- Direct live API e2e against the running Docker backend and Petstore OpenAPI passed: QA seed/login, RouteDeck `needs_connection`, REST connection create, activation stream, catalog with 3 entities and 19 actions, generated RAG with 1 document and 3 chunks, memory create/list, chat SSE tool execution, and RouteDeck transition to `result_review`.
- Embedded browser QA passed `rag_memory_learning_surfaces` and `connection_catalog_preview` with zero console errors after fixing the connection-list async lazy-load issue.
- Independent QA agent validated health, frontend reachability, Docker stack, backend tests, frontend type-check, authenticated surfaces, QA panel, Petstore activation, generated RAG, and memory creation.
- Runtime fixes made during validation: Learn view QA mapping/icon support, QA memory-tab action, dev startup migration for old workspace columns, and eager loading for connection activation state.

## Final Working Flow

1. User signs in.
2. User creates `Medusa Storefront Agent`.
3. SaaS Agent RouteDeck starts at connection setup.
4. User previews and activates Medusa Storefront OpenAPI.
5. Agent generates actions, tools, RAG entries, and catalog surfaces.
6. User asks a read-safe task.
7. Agent plans, selects a tool, executes, shows trace, and reviews result.
8. User saves memory or corrects behavior.
9. Sandbox learning candidate is proposed.
10. User approves or rejects learning.
11. QA can replay and export evidence.

## Assumptions

- No workspace/grouping layer exists in this foundation.
- Every SaaS Agent has its own RouteDeck runtime.
- Medusa Storefront and Admin are separate SaaS Agents.
- Existing local data may be migrated or reset explicitly, but the canonical code
  model becomes SaaS Agent.
