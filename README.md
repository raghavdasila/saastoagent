# SaaStoAgent v0.1

REST-only workspace agent built by copying and adapting proven pieces from `saastoagent` and `foundation-agent`.

## Current State

- Context pipeline scaffold is in place.
- The implementation plan lives in `plans/saastoagent_v0_1_workspace_agent_plan.md`.
- Code has not been copied yet; this folder currently hosts project context, planning, and documentation scaffolding.

## Product Boundary

- 1 workspace = 1 SaaS agent
- REST only
- Entity + actions explorer included in v0.1
- Tool-finder chat, agentic execution, and QA agent are planned slices
- No separate `AgentSystem` product model in v0.1

## Start Here

1. Read `critical_prompt.md`
2. Read `context.md`
3. Review `plans/saastoagent_v0_1_workspace_agent_plan.md`
4. Use `work_prompt.md` for session start and closeout

## Context Pipeline

This project follows the same context-pipeline pattern used in `saastoagent`, but starts with a clean history and a v0.1-specific scope.

See `context_pipeline.md` and `instructions.md` for workflow rules.