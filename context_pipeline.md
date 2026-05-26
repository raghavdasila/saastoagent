# Context Pipeline - SaaStoAgent v0.1

This project uses a structured context pipeline for continuity, planning, and
clean handoffs.

## Goals

1. Session continuity
2. Clean handoffs between sessions
3. Verified planning before implementation
4. Auditable progress history
5. Reusable workflows captured as skills only when they are truly repeatable
6. Code-referenced architecture coverage for source-heavy work

## Layers

### Vision

- `critical_prompt.md` - product scope and north star

### State

- `context.md` - live current state
- `context_history/` - archived full snapshots of prior `context.md`
- `context_checkpoints/` - end-of-session handoff snapshots
- `structure.md` - project tree snapshot

### Process

- `instructions.md` - documentation workflow
- `work_prompt.md` - session start/end templates
- `context_pipeline.md` - this file

### Planning

- `plans/` - feature and architecture plans

### Knowledge

- `knowledgebase/` - verified research and patterns
- `skills/` - reusable workflows and build patterns only

### History and Decisions

- `logs/` - session activity history
- `decisions/` - ADRs
- `errors/` - hard debugging notes

### Documentation and Validation

- `docs/` - end-user docs
- `test_index/` - test documentation
- `architecture/` - architecture state, code ownership, and evolution
- `architecture/code-map.md` - subsystem-to-code/test/doc ownership map
- `architecture/components/` - focused component docs for active/high-risk areas
- `audits/` - audit reports

## Session Lifecycle

### Session Start

Read, in order:

1. `critical_prompt.md`
2. `context.md`
3. Latest file in `context_checkpoints/` if resuming
4. Latest file in `context_history/` only if more background is needed
5. `architecture/code-map.md` when source files, architecture, or tests are in scope
6. Relevant component doc in `architecture/components/`
7. Relevant file in `plans/`
8. Relevant skills in `skills/` if a reusable workflow applies

### Planning Phase

1. Verify uncertain technical details
2. Record proven findings in `knowledgebase/`
3. Create or refine a plan in `plans/`
4. Create an ADR in `decisions/` when the choice is significant

### Implementation Phase

1. Implement according to the plan
2. Track changed source files against `architecture/code-map.md`
3. Keep `context.md` current
4. Add logs, ADRs, KB notes, architecture docs, or test docs when appropriate

### Session End

1. Create a log entry in `logs/`
2. Create a checkpoint in `context_checkpoints/`
3. Archive the previous live snapshot into `context_history/`
4. Rewrite `context.md` as the concise live snapshot
5. Name changed source files and their owning `architecture/code-map.md` rows
6. Update related component docs/test docs or explicitly state they are unchanged
7. Run `python scripts/check_doc_coverage.py` and include notable warnings in the closeout

### Source Coverage Rule

`context.md` stays concise. It links to the current architecture and validation
anchors; it does not duplicate the code map. Source ownership lives in
`architecture/code-map.md`, detailed contracts live in `architecture/components/`,
and validation coverage lives in `test_index/`.

## Working Rule

Keep this project clean. Reuse the proven pipeline structure, but do not import
old history, old logs, or old runtime-specific decisions unless they are
intentionally adopted into the new project.
