# Diagnostics Sidebar Contract

Use this as the minimum implementation checklist for a diagnostics sidebar that supports live runtime inspection, persisted replay, and exportable debugging artifacts.

## Required Inputs

Live stream events:

- stream start/end;
- turn start/end;
- graph manifest on turn start;
- stage start/complete/fail;
- output chunks;
- artifacts;
- tool/model lifecycle events when they are not already represented as stages.

Replay endpoint:

- run metadata;
- graph manifest;
- runtime stages;
- outputs;
- artifacts;
- legacy snapshot only as fallback.

## Required Frontend Shapes

`DiagnosticsTurn` should carry:

- `turnId`
- `sessionId`
- `status`
- `startedAt`
- `endedAt`
- `graphManifest`
- `runtimeStages`
- `outputs`
- `artifacts`
- `structuredContext`
- `eventFeed`

`DiagnosticsRuntimeStage` should carry:

- `stageId`
- `parentStageId`
- `dependsOn`
- `sequence`
- `status`
- `lane`
- `startedAt`
- `endedAt`
- `durationMs`
- `input`
- `output`
- `error`

## Live Projection Checklist

- Create active turn from stream/turn start.
- Store graph manifest.
- Upsert stage start by `stage_id` plus sequence or unique stage-run id.
- Merge stage completion/failure into existing stage.
- Append output chunks.
- Append artifacts.
- Parse structured context artifacts into cards.
- Bound event feed length.
- Archive active turn on terminal event.

## Replay Hydration Checklist

- Prefer canonical runtime stages when present.
- Rebuild stage dependencies from persisted metadata.
- Restore graph manifest from run metadata.
- Rebuild output feed from output rows.
- Restore artifacts and structured context cards.
- Fall back to legacy snapshots only when canonical runtime data is absent.

## View Checklist

Summary:

- status;
- duration;
- run path;
- graph version;
- output count;
- stage count.

Tree:

- parent/child hierarchy;
- child stages remain visible;
- legacy synthetic blocks do not duplicate runtime stages.

Timeline:

- duration for each stage;
- compact bars;
- visible parallelism;
- failed stages clearly marked.

DAG:

- manifest edges first;
- executed dependencies second;
- parent-child edges for nesting;
- legacy inference only as fallback.

Context:

- structured cards from artifacts;
- readiness/score cards when available;
- selected next action/question when available;
- raw payload expandable.

Export:

- YAML or JSON;
- source is diagnostics detail payload;
- includes graph manifest, stages, outputs, artifacts, and structured cards.

## UX Defaults

- Compact typography.
- Timing visible for stages.
- Raw events collapsed.
- Token/message deltas hidden by default.
- Obvious collapse/expand control.
- No duplicate diagnostics surfaces unless there are distinct workflows.

## Test Checklist

Backend:

- stage persistence;
- diagnostics detail payload;
- replay endpoint;
- graph manifest included;
- dependency metadata included.

Frontend:

- production build;
- live projection;
- replay hydration;
- DAG edge rendering;
- export parseability.

Manual:

- normal turn;
- skipped/direct response;
- safety/guardrail path;
- tool/model path;
- context assembly path;
- reopen session;
- export artifact.
