# SaaStoAgent v0.1

REST-only workspace agent built by copying and adapting proven pieces from `saastoagent` and `foundation-agent`.

## Current State

- Context pipeline scaffold is in place.
- Slice 1 runnable shell is now scaffolded.
- The implementation plan lives in `plans/saastoagent_v0_1_workspace_agent_plan.md`.

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

## Run Slice 1

From this directory:

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:3005`
- Backend API: `http://localhost:8085/api/health`

## Context Pipeline

This project follows the same context-pipeline pattern used in `saastoagent`, but starts with a clean history and a v0.1-specific scope.

See `context_pipeline.md` and `instructions.md` for workflow rules.