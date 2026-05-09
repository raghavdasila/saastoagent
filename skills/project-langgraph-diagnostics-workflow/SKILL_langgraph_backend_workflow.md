# SKILL: LangGraph Backend Workflow

Project-agnostic guide for building, debugging, or porting a graph-based backend turn workflow with reliable diagnostics and replay.

Use this when a project has a LangGraph or graph-like backend runtime, server-sent streaming, staged execution, persisted run diagnostics, child-stage visibility, or a diagnostics sidebar that must reflect backend truth.

## 1. Core Rule

Backend runtime facts are the source of truth.

The UI can render graph facts, filter them, group them, and make them readable. It must not invent current graph topology from component-local stage-name strings.

If the graph view is wrong, fix the backend graph spec, emitted dependency metadata, persisted stage rows, or protocol types first. Do not patch current graph architecture into the frontend renderer.

## 2. Recommended File Roles

Adapt names to the target project, but keep the responsibilities separate:

- `routes` or API layer: request validation, auth/session ownership, SSE/stream response shell, diagnostics endpoints.
- `orchestrator` or turn shell: create run row, emit start manifest, delegate to graph executor, finalize stream. Keep it thin.
- `graph_spec`: typed stage IDs, lanes, graph nodes, graph edges, edge conditions, graph manifest.
- `graph_executor`: compiled LangGraph `StateGraph`, node mapping, conditional routing, graph joins, stream projection, checkpoint config.
- `graph_runtime`: mutable per-turn runtime state and dependency injection.
- `stage_*` modules: concrete stage behavior by lane or domain.
- `stage_io`: shared stage persistence, output streaming, stage start/complete/fail helpers.
- `runtime_store`: database writes for runs, stages, outputs, artifacts, and replay data.
- `protocol`: backend event dataclasses and frontend event types.
- `diagnostics_state`: live event projection plus replay hydration.

Avoid catch-all service files. Split by runtime responsibility, not by convenience.

## 3. Runtime Shape

Target request flow:

```text
POST /chat-or-turn
  routes
    -> turn shell
      -> create run row
      -> emit turn_started(graph_manifest)
      -> run graph executor
        -> stage_started(parent_stage_id, depends_on)
        -> stage_completed / stage_failed
        -> artifact_recorded
        -> output_delta
      -> finalize assistant/output message
      -> persist run metadata and graph manifest
      -> emit turn_completed / stream_end
```

Persist at least:

- one run row per turn/request;
- one stage row per executed graph stage or child stage;
- ordered output rows for user-visible text;
- graph manifest used for the run;
- stage input metadata carrying executed dependencies;
- artifacts for structured diagnostics payloads.

Checkpoint metadata can be useful for execution debugging, but do not claim durable product replay unless the graph state can fully rehydrate the turn without hidden mutable side state.

## 4. Graph Topology Contract

Keep graph topology in a backend spec module:

- typed stage identifiers;
- typed lane identifiers;
- typed edge types;
- typed edge conditions;
- graph node definitions;
- graph edge definitions;
- manifest builder.

The compiled graph must be generated from that spec. Do not duplicate edge literals in the executor.

Recommended edge types:

- `entry`
- `conditional`
- `parallel_branch`
- `join_input`
- `sequence`
- `terminal_path`
- `exit`

Recommended stage metadata:

- `stage_id`
- `parent_stage_id`
- `depends_on`
- `lane`
- `sequence`
- `input`
- `output`
- `status`
- `duration_ms`

The frontend should prefer:

1. backend graph manifest edges;
2. stage `depends_on`;
3. stage `parent_stage_id`;
4. legacy inference only for old persisted turns without backend facts.

## 5. Top-Level And Child Stages

Keep the graph readable by separating top-level control stages from child work.

Example top-level stages:

- `preflight`
- `safety_intervention`
- `assembly_gate`
- `direct_response`
- `context_assembly`
- `empathy_or_preface`
- `context_format`
- `navigator_or_agent`
- `finalize`

Example child stages:

- `preflight.intent_classification`
- `preflight.safety_gate`
- `context_assembly.phase1_wait`
- `context_assembly.enrichment_wait`
- `context_assembly.populate_client_signal`
- `context_assembly.populate_provider_model`
- `context_assembly.assessment_readiness`
- `context_assembly.search_and_rank`
- `empathy.first_token_wait`
- `empathy.streaming`
- `empathy.fallback`

Child stages should be real persisted stages, not strings embedded in a parent label. If the diagnostics sidebar should show it as work, the backend should emit it as work.

## 6. Context Assembly Pattern

Keep top-level graph control distinct from context assembly internals.

Recommended split:

- graph stage: `context_assembly`;
- internal assembler: queue/task/single-flight implementation if needed;
- pipeline config: declarative phases, dependencies, injection rules;
- trace payload builder: frontend-safe structured outputs;
- child stage emitter: converts executed tool/extractor runs into child runtime facts.

If the assembler uses asyncio, document it as an implementation detail behind `context_assembly`, not the top-level controller.

Business logic should not live in extractor prompts:

- `schemas/`: canonical structured data.
- `scoring/`: deterministic completeness/readiness scoring.
- `questions/`: deterministic candidate generation and ordering.
- `readiness`: convergence and selected next action/question.
- `extractors/`: LLM extraction only.
- `matching` or domain modules: deterministic ranking/search logic.

LLMs can produce phrasing and extracted facts. Deterministic modules decide priority, readiness, and control flow.

## 7. Prompt Boundary

Create one prompt formatter boundary between runtime context and the agent/navigator.

The formatter should pass:

- selected next question/action;
- readiness status;
- missing critical fields;
- relevant summaries;
- safety status;
- matching/search summary only after readiness gates pass;
- freshness/snapshot metadata when useful.

The formatter should not pass raw unordered suggestions as the primary control input. Raw suggestions belong in diagnostics unless a backward-compatibility fallback is required.

## 8. Problems This Pattern Fixes

### Hardcoded stage strings

Fix with typed stage IDs, typed lanes, helper functions, backend graph manifests, and tests that compare spec and executor.

Avoid inline stage strings in executor, frontend DAG logic, and persistence code except in legacy migration/fallback code.

### Duplicated graph edges

Fix by generating the compiled graph from the canonical graph edge list.

Avoid one edge list for diagnostics and a second manually written edge list for execution.

### God-function orchestrators

Fix by keeping the orchestrator as a shell and moving stage bodies into lane/domain modules.

Avoid adding branch behavior, prompt formatting, persistence details, and tool execution into one turn function.

### Frontend-owned graph architecture

Fix by streaming and persisting a backend graph manifest plus stage dependency metadata.

Avoid React-only rules like "if stage name is X, draw edge to Y" for current runtime architecture.

### Hidden internal work

Fix by emitting child stages for meaningful internal work: waits, extractors, tool runs, model prefaces, fallback paths.

Avoid burying important work only inside parent-stage output JSON.

### Replay mismatch

Fix by hydrating replay from persisted run/stage/output rows and the stored graph manifest.

Avoid relying on transient UI state, old snapshot shapes, or checkpoint metadata alone.

### LLM-owned business priority

Fix by moving scoring, readiness, and next-question/action priority into deterministic modules.

Avoid asking the LLM to choose priority when domain rules, safety gates, or business standards should own it.

### Eligibility leakage

Fix by exiting before stage start when a stage should not exist for a turn.

Avoid starting a stage and then suppressing its text; diagnostics will still show that the stage executed.

## 9. Change Workflow

For a new or changed graph stage:

1. Add typed IDs, nodes, labels, lanes, parents, and edges in the graph spec.
2. Add or update executor node mapping with typed IDs.
3. Put behavior in the appropriate stage module.
4. Emit stages through shared start/complete/fail helpers.
5. Set `parent_stage_id` for child work.
6. Set `depends_on` for executed dependency edges.
7. Persist useful diagnostics in stage output or artifacts.
8. Stream user-visible text through the shared output helper.
9. Mirror protocol changes across backend and frontend types.
10. Add topology/runtime tests before changing frontend visuals.

For a new context-assembly tool/extractor:

1. Add canonical schema if the output is durable business state.
2. Add deterministic scoring/readiness/question logic if it affects control.
3. Add extractor only for LLM extraction.
4. Register the pipeline step declaratively.
5. Add a child stage mapping for diagnostics.
6. Add trace payload projection for frontend-safe diagnostics.
7. Update prompt formatter only with selected/curated control input.

## 10. Debugging Playbook

Graph looks wrong:

1. Inspect live `turn_started.graph_manifest`.
2. Inspect persisted diagnostics `graph_manifest`.
3. Inspect stage `depends_on`.
4. Inspect graph spec edge list.
5. Inspect topology tests.

Live diagnostics differ from replay:

1. Inspect diagnostics detail endpoint payload.
2. Inspect persisted run metadata.
3. Inspect persisted stage rows.
4. Inspect persisted output rows.
5. Inspect frontend replay hydration.
6. Inspect live event projection helpers.

A child stage is missing:

1. Confirm the backend emits stage start/complete for it.
2. Confirm `parent_stage_id` is set.
3. Confirm it is persisted.
4. Confirm replay maps it into diagnostics state.
5. Confirm tree/timeline/DAG render child stages generically.

Agent asks the wrong next question/action:

1. Inspect deterministic readiness output.
2. Inspect candidate generation and priority.
3. Inspect screening/safety gates.
4. Inspect prompt formatter selected-control block.
5. Inspect prompt instructions.

Local tests differ from container runtime:

1. Check dependency versions.
2. Check checkpointer fallback.
3. Rebuild the running backend.
4. Confirm whether tests hit in-process code or `localhost`.

## 11. Validation Matrix

Backend focused:

```powershell
python -m pytest tests/test_graph_topology.py tests/test_turn_runtime.py -q
```

Backend broad:

```powershell
python -m pytest tests -q
```

Frontend:

```powershell
npm run build
```

Config parse:

```powershell
@'
import yaml
from pathlib import Path
payload = yaml.safe_load(Path("shared/ops_registry.yaml").read_text(encoding="utf-8"))
print("config yaml ok")
'@ | python -
```

Manual scenarios:

- low-signal direct response;
- normal issue-bearing turn;
- cached/enrichment context turn;
- safety/guardrail hijack;
- explicit tool call;
- matching/search readiness gate;
- diagnostics export;
- reopened-session replay.

## 12. Porting Notes

When moving this pattern to another project:

- rename stages to match the domain;
- preserve typed IDs and manifest-driven rendering;
- replace domain context modules with that project's schemas/scoring/readiness modules;
- keep graph topology backend-owned;
- keep replay backed by persisted runtime rows;
- keep diagnostics renderers generic;
- avoid importing the source project's product names or domain-specific fields unless they truly apply.

See `references/runtime-graph-contract.md` for a compact checklist of required runtime facts.
