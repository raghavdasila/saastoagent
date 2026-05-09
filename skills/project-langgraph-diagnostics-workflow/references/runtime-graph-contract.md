# Runtime Graph Contract

Use this as the minimum contract for a backend-owned graph runtime that supports diagnostics, replay, and a generic DAG/sidebar renderer.

## Required Backend Facts

Each turn/request should produce:

- `run_id`
- `turn_id` or request id
- `session_id` when applicable
- `graph_version`
- `graph_manifest`
- `status`
- `started_at`
- `completed_at`
- `metadata`

Each executed stage should produce:

- `stage_id`
- `parent_stage_id`
- `sequence`
- `lane`
- `status`
- `started_at`
- `completed_at`
- `duration_ms`
- `input_payload`
- `output_payload`
- `error`

Each dependency edge should be recoverable from:

- graph manifest edges for architecture;
- `stage_started.depends_on` or stage input metadata for executed dependency facts.

Each user-visible output should produce:

- `stage_id`
- ordered sequence or timestamp;
- text chunk;
- lane/source when useful.

Each structured diagnostic artifact should produce:

- `stage_id`
- artifact type;
- name;
- payload;
- timestamp.

## Graph Manifest Shape

Recommended manifest:

```json
{
  "version": "whole_turn_v1",
  "nodes": [
    {
      "id": "context_assembly",
      "label": "Context Assembly",
      "lane": "assembly"
    },
    {
      "id": "context_assembly.populate_signal",
      "label": "Populate Signal",
      "lane": "assembly",
      "parent": "context_assembly"
    }
  ],
  "edges": [
    {
      "from": "assembly_gate",
      "to": "context_assembly",
      "type": "conditional",
      "condition": "assembly_required"
    },
    {
      "from": "context_assembly",
      "to": "context_format",
      "type": "join_input"
    }
  ]
}
```

## Stage Event Shape

Recommended live event:

```json
{
  "type": "stage_started",
  "turn_id": "turn-123",
  "run_id": "run-123",
  "stage_id": "context_assembly.populate_signal",
  "parent_stage_id": "context_assembly",
  "depends_on": ["context_assembly"],
  "sequence": 8,
  "lane": "assembly"
}
```

Recommended completion:

```json
{
  "type": "stage_completed",
  "turn_id": "turn-123",
  "run_id": "run-123",
  "stage_id": "context_assembly.populate_signal",
  "status": "ok",
  "duration_ms": 421,
  "lane": "assembly",
  "output": {
    "summary": "structured result summary"
  }
}
```

## Persistence Rules

- Persist every executed stage.
- Persist child stages as first-class rows.
- Persist graph manifest with the run, not only in code.
- Persist output chunks separately from stage output payloads.
- Persist structured artifacts separately enough that replay/export can recover them.
- Store executed dependencies in stage input metadata if the stage table has no dependency column.

## Renderer Rules

The diagnostics renderer should prefer:

1. persisted/current graph manifest;
2. executed `depends_on`;
3. parent-child stage relationships;
4. legacy stage-name inference only when no backend facts exist.

## Anti-Patterns

- graph topology hardcoded only in frontend components;
- two separate graph definitions, one for execution and one for diagnostics;
- child work represented only as text in parent output;
- replay based on transient active UI state;
- checkpoint metadata treated as product replay without full rehydration support;
- LLM extraction prompts deciding deterministic priority or readiness.
