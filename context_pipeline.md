# Context Pipeline — SaaStoAgent v0.1

This project uses a structured context pipeline for continuity, planning, and clean handoffs.

## Goals

1. Session continuity
2. Clean handoffs between sessions
3. Verified planning before implementation
4. Auditable progress history
5. Reusable workflows captured as skills only when they are truly repeatable

## Layers

### Vision

- `critical_prompt.md` — product scope and north star

### State

- `context.md` — live current state
- `context_history/` — archived full snapshots of prior `context.md`
- `context_checkpoints/` — end-of-session handoff snapshots
- `structure.md` — project tree snapshot

### Process

- `instructions.md` — documentation workflow
- `work_prompt.md` — session start/end templates
- `context_pipeline.md` — this file

### Planning

- `plans/` — feature and architecture plans

### Knowledge

- `knowledgebase/` — verified research and patterns
- `skills/` — reusable workflows and build patterns only

### History and Decisions

- `logs/` — session activity history
- `decisions/` — ADRs
- `errors/` — hard debugging notes

### Documentation and Validation

- `docs/` — end-user docs
- `test_index/` — test documentation
- `architecture/` — architecture state and evolution
- `audits/` — audit reports

## Session Lifecycle

### Session Start

Read, in order:

1. `critical_prompt.md`
2. `context.md`
3. Latest file in `context_checkpoints/` if resuming
4. Latest file in `context_history/` only if more background is needed
5. Relevant file in `plans/`
6. Relevant skills in `skills/` if a reusable workflow applies

### Planning Phase

1. Verify uncertain technical details
2. Record proven findings in `knowledgebase/`
3. Create or refine a plan in `plans/`
4. Create an ADR in `decisions/` when the choice is significant

### Implementation Phase

1. Implement according to the plan
2. Keep `context.md` current
3. Add logs, ADRs, KB notes, or test docs when appropriate

### Session End

1. Create a log entry in `logs/`
2. Create a checkpoint in `context_checkpoints/`
3. Archive the previous live snapshot into `context_history/`
4. Rewrite `context.md` as the concise live snapshot

## Working Rule

Keep this project clean. Reuse the proven pipeline structure, but do not import old history, old logs, or old runtime-specific decisions unless they are intentionally adopted into the new project.