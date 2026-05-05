# Instructions — SaaStoAgent v0.1

## Documentation Workflow

This project uses the same documentation discipline as `saastoagent`, but starts from a clean state.

## Core Files

### `critical_prompt.md`

- Purpose: product vision and scope boundary
- Update when the product direction changes

### `context.md`

- Purpose: concise live project snapshot
- Update after major work steps and at session close
- Keep short; archive older full state into `context_history/`

### `plans/`

- Purpose: feature plans and implementation roadmaps
- Create or update during planning, not after implementation is already drifting

### `logs/`

- Purpose: what happened in each work step
- File format: `YYYYMMDD_HHMM_description.md`

### `decisions/`

- Purpose: document meaningful architectural decisions
- File format: `ADR-{number}-{short-name}.md`

### `errors/`

- Purpose: preserve non-trivial debugging outcomes
- Use when a bug took meaningful effort or could recur

### `knowledgebase/`

- Purpose: verified research and patterns
- Every factual claim should have either citation or code/log proof

### `skills/`

- Purpose: reusable workflows, build patterns, or architecture recipes
- Do not create skills for one-off incidents

### `architecture/`

- Purpose: current architecture and architecture evolution
- Update with the implementation, not after it

### `SYSTEM_FLOW_INDEX.md`

- Purpose: source of truth for the main product flows
- Keep aligned with actual routes, services, hooks, and page flows once code exists

## Session Pattern

### Start

1. Read `critical_prompt.md`
2. Read `context.md`
3. Load the latest checkpoint if resuming
4. Load the active plan in `plans/`

### During Work

1. Plan first when requirements are still moving
2. Add verified findings to `knowledgebase/`
3. Keep `context.md` current

### End

1. Add log entry
2. Add checkpoint
3. Archive previous context if needed
4. Rewrite `context.md`

## Working Rule for This Repo

This project is being built incrementally from existing working sources. Favor explicit source references in plans so copied code remains traceable.