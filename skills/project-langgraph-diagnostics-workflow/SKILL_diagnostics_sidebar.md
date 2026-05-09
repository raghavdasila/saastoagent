# SKILL: Diagnostics Sidebar And Runtime Replay

Project-agnostic guide for implementing or maintaining a diagnostics sidebar that reflects graph/runtime backend facts, supports persisted replay, and can export turn-level debugging artifacts.

Use this before adding runtime stages, changing graph topology, touching persisted diagnostics, editing Tree/Timeline/DAG views, adding YAML/JSON diagnostics export, or porting a diagnostics sidebar to another graph-based agent project.

## 1. Source Of Truth

Diagnostics must reflect backend runtime facts, not frontend guesses.

Canonical runtime data should include:

- one run record per turn/request;
- one stage record per executed graph stage or child stage;
- ordered output records for assistant/user-visible chunks;
- backend-owned graph manifest for the current graph version;
- stage dependency metadata for executed edges;
- run metadata containing the graph manifest used for replay;
- structured artifacts for context/tool/model diagnostics.

Legacy compatibility data may be displayed for old turns, but it must not define new graph architecture.

## 2. Runtime Flow

Target live flow:

```text
stream_start
turn_started(graph_manifest)
stage_started(parent_stage_id, depends_on)
artifact_recorded(...)
output_delta(...)
stage_completed(...)
turn_completed
stream_end
```

Target replay flow:

```text
GET /sessions/{session_id}/turns/{turn_id}/diagnostics
  -> run row
  -> stage rows
  -> output rows
  -> graph_manifest from run metadata or current fallback
  -> frontend coerceTurnSnapshot()
  -> DiagnosticsTurn.runtimeStages + graphManifest
  -> Tree / Timeline / DAG render backend facts
```

The diagnostics sidebar should be a renderer over this payload. It should not be a second runtime model.

## 3. Sidebar Views

Useful diagnostics views:

- summary chips: status, duration, freshness, selected path, model/tool counts;
- context data: structured context cards, readiness, selected next action/question, matching/search results;
- tree: hierarchical stage view using `parent_stage_id`;
- timeline: stage durations and parallelism;
- DAG: graph manifest edges plus executed dependency edges;
- event feed: compact recent events, with token-noise hidden by default;
- artifacts: prompt context, structured tool outputs, trace payloads;
- export action: YAML/JSON from canonical diagnostics detail payload.

Keep Tree, Timeline, and DAG based on the same runtime stage set.

## 4. Frontend State Pattern

Recommended state split:

- one public application store, for example Zustand;
- chat/session actions in `state/chat/*`;
- diagnostics actions/helpers in `state/diagnostics/*`;
- pure per-turn helpers for event projection and replay hydration;
- components receive shaped view models, not raw event streams where avoidable.

Avoid Redux/reducer detours unless the project already uses them consistently. Do not leave comments that describe a reducer architecture when the implementation is store/actions/helpers.

## 5. Event Projection

Live event projection should:

1. create a diagnostics turn on stream or turn start;
2. store `graph_manifest` from turn start;
3. upsert runtime stages on stage start/complete/fail;
4. preserve `parent_stage_id`, `depends_on`, lane, sequence, duration, output, and errors;
5. append structured artifacts;
6. append output chunks;
7. parse structured context/tool payloads into typed diagnostics cards;
8. archive the active turn on terminal stream/turn events.

Replay hydration should:

1. prefer canonical runtime stages and outputs;
2. use stored graph manifest;
3. recover dependencies from stage input metadata;
4. map artifacts into the same shape live events use;
5. fall back to legacy snapshots only when canonical rows are absent.

## 6. Graph Rendering Rules

Backend graph manifest owns current topology.

DAG edge priority:

1. `turn.graphManifest.edges`
2. `runtimeStage.dependsOn`
3. `runtimeStage.parentStageId`
4. legacy stage-name inference only for old turns

Do not add current architecture rules only in the frontend. If a new edge matters, add it to the backend graph spec and emit dependency metadata.

Tree rules:

- top-level runtime stages are trunk nodes;
- child stages render as children using `parent_stage_id`;
- legacy synthetic leaves should not duplicate runtime-stage turns;
- child stages should remain visible, not folded into parent labels.

Timeline rules:

- sort by sequence or timestamp;
- preserve parallelism visually;
- show duration for every completed/failed stage;
- keep compact typography.

Event feed rules:

- keep it bounded;
- hide `message_delta` token-noise by default;
- expose raw payloads only behind an explicit expansion/debug view.

## 7. Structured Context Cards

Structured context should be parsed from canonical artifact/trace payloads, not UI-only state.

Recommended cards:

- safety/guardrail triage;
- client/user signal;
- domain model or provider/model profile;
- readiness/scoring;
- selected next question/action;
- matching/search results;
- tool calls;
- prompt context preview.

The card parser should tolerate:

- field metadata wrappers such as `{ value, confidence, source }`;
- nested grouped fields;
- absent optional sections;
- old flat legacy payloads.

The navigator/agent may receive curated context, but raw unordered suggestions should remain diagnostic unless explicitly selected by deterministic readiness logic.

## 8. Export Workflow

Export from the canonical diagnostics detail endpoint.

Recommended export contents:

- run metadata;
- graph manifest;
- runtime stages;
- outputs;
- artifacts;
- structured context cards;
- event feed;
- raw payloads needed for reproduction;
- timestamp and app/runtime version if available.

Do not invent a separate backend export route unless the diagnostics detail endpoint cannot provide the canonical payload. Browser-side YAML/JSON serialization is enough for turn-local debugging artifacts in most projects.

## 9. Problems This Pattern Fixes

### Frontend-only graph inference

Fix by rendering backend manifests and stage dependency metadata.

Avoid encoding current graph topology in component-local stage-name maps.

### Runtime/replay mismatch

Fix by using the same `DiagnosticsTurn` shape for live projection and replay hydration.

Avoid relying on transient active-turn UI state for replay.

### Duplicate blocks

Fix by choosing canonical runtime stages when present and legacy snapshots only as fallback.

Avoid rendering runtime stages and old synthetic leaves for the same work.

### Hidden child work

Fix by requiring backend child stage rows for waits, tool runs, extractors, model prefaces, and fallback stages.

Avoid summarizing child work only inside parent output text.

### Event-feed noise

Fix by hiding token deltas by default and giving explicit raw-event expansion.

Avoid making debugging panels unreadable during streaming.

### Hardcoded labels and lanes

Fix by using manifest labels/lanes when present and generic fallback labels only for legacy data.

Avoid scattering display names across unrelated components.

## 10. Change Workflow

When adding a new runtime stage:

1. Confirm backend emits and persists the stage.
2. Confirm stage has `parent_stage_id` and `depends_on` when applicable.
3. Confirm protocol types include required fields.
4. Confirm live event projection upserts the stage.
5. Confirm replay hydration maps the persisted row.
6. Confirm Tree, Timeline, and DAG render it generically.
7. Add tests before visual polish.

When adding a new structured artifact:

1. Define backend artifact payload.
2. Add typed frontend diagnostics shape.
3. Parse both live event payload and replay payload.
4. Render a compact card.
5. Include artifact in YAML/JSON export.
6. Keep raw payload accessible for debugging.

When adding an export:

1. Use diagnostics detail payload.
2. Serialize in browser unless server-side export is required.
3. Include graph manifest and runtime rows.
4. Avoid exporting only view-model state.

## 11. Debugging Symptoms

Graph looks sequential:

- Check whether the turn has a backend graph manifest.
- Check `depends_on`.
- Check join edges in graph spec.
- Check whether the frontend fell into legacy fallback mode.

Stage disappears after reopening:

- Check diagnostics detail endpoint.
- Check persisted stage rows.
- Check replay hydration.
- Check component filters.

Duplicate nodes:

- Check whether runtime stages and legacy synthetic events are both rendering.
- Prefer runtime stages when present.

Context card is blank:

- Check artifact payload.
- Check trace payload builder.
- Check live parser.
- Check replay parser.
- Check field wrapper handling.

Export lacks useful facts:

- Confirm export uses diagnostics detail payload.
- Confirm graph manifest, stages, outputs, and artifacts are included.

## 12. Acceptance Checklist

Backend:

- graph topology tests pass;
- runtime streaming tests pass;
- diagnostics detail/replay tests pass;
- persistence tests pass when stage/output schemas changed.

Frontend:

- production build passes;
- live diagnostics and reopened replay show the same stage set;
- DAG edges match backend manifest and stage `depends_on`;
- child stages are visible;
- export parses as YAML/JSON and contains canonical runtime facts.

Manual scenarios:

- low-signal direct response;
- normal graph path;
- cached/enrichment path if present;
- safety/guardrail hijack;
- tool call;
- structured context update;
- session reopen and replay.

## 13. Porting Notes

When porting to another project:

- rename domain cards;
- keep runtime rows and graph manifest generic;
- keep event projection pure and testable;
- keep UI renderers generic;
- preserve export from canonical diagnostics detail;
- update references to the target project's protocol, routes, and store modules.

See `references/diagnostics-sidebar-contract.md` for a compact implementation checklist.
