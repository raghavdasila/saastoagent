# Porting Map

Use this when exporting the LangGraph backend workflow and diagnostics sidebar pattern to another project.

## Replace Product-Specific Terms

Replace source-project names with target-project concepts:

- care navigator -> target assistant/agent role;
- client signal -> target user/customer/task signal;
- provider genome -> target provider/vendor/resource/capability model;
- assessment readiness -> target readiness/convergence/gating result;
- fit result -> target matching/ranking/search result;
- safety hijack -> target guardrail/escalation/intervention path;
- empathy -> target preface/acknowledgement/parallel response lane if applicable.

Do not port source-domain field names unless the target project shares those standards.

## Keep These Architecture Invariants

- Backend graph manifest owns topology.
- Executor compiles from the same graph spec used for diagnostics.
- Orchestrator/route shell stays thin.
- Stage behavior lives in stage modules.
- Child stages are first-class persisted runtime facts.
- Replay comes from persisted runtime rows.
- Frontend diagnostics render backend facts.
- Deterministic control logic lives outside LLM prompts.

## Adapt These Modules

Source pattern:

- `graph_spec`
- `graph_executor`
- `graph_runtime`
- `stage_io`
- `stage_*`
- `runtime_store`
- `protocol`
- `diagnostics_state`
- `diagnostics_components`
- `context/schemas`
- `context/scoring`
- `context/questions`
- `context/readiness`
- `context/extractors`

Target project should create equivalent modules using its naming conventions.

## Minimum Port Sequence

1. Define typed stage IDs, lanes, edges, and manifest.
2. Compile the graph from the manifest/spec edge list.
3. Add run/stage/output persistence.
4. Emit graph manifest and stage lifecycle events.
5. Build a diagnostics detail endpoint from persisted rows.
6. Implement live frontend projection.
7. Implement replay hydration.
8. Render Tree, Timeline, and DAG from backend facts.
9. Add export from diagnostics detail payload.
10. Move business scoring/readiness out of LLM prompts.

## Questions To Answer In The Target Project

- What is the stable unit of execution: turn, request, job, workflow?
- What are the top-level graph stages?
- Which internal steps deserve child stages?
- What outputs are user-visible?
- What artifacts are useful for replay and debugging?
- What state must be deterministic rather than LLM-authored?
- What existing frontend state mechanism should own diagnostics?
- What legacy replay data needs fallback support?

## Acceptance Criteria

The port is healthy when:

- graph topology tests prove spec/executor alignment;
- live diagnostics and replay show the same stages;
- DAG edges come from backend facts;
- child stages are visible;
- export includes graph manifest, stages, outputs, and artifacts;
- prompt/control logic uses deterministic selected inputs;
- no frontend-only current topology rules are required.
