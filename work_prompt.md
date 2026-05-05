# Work Prompt — SaaStoAgent v0.1

Use this prompt to start or resume work on SaaStoAgent v0.1.

## Session Start Prompt

```text
I'm working on the SaaStoAgent v0.1 project.

Please:
1. Read critical_prompt.md and context.md first
2. If resuming, inspect the latest checkpoint in context_checkpoints/
3. If needed, inspect the latest context_history entry for deeper background
4. Review instructions.md for the documentation workflow
5. Review the active plan in plans/
6. Tell me what the current state is and what the next concrete step should be
```

## Session End Prompt

```text
We're wrapping up this session. Please:

1. Create a log entry in logs/
2. Create a checkpoint in context_checkpoints/
3. Archive the previous context.md into context_history/ if needed
4. Rewrite context.md as the concise live snapshot
5. Update plans, knowledgebase, decisions, architecture, and test_index if this session changed them
6. Update SYSTEM_FLOW_INDEX.md if the runtime or UX flows changed
```

## Feature Completion Prompt

```text
The feature is complete. Please:

1. Update docs/
2. Update architecture/
3. Update SYSTEM_FLOW_INDEX.md if flows changed
4. Update context.md
5. Add ADRs or test_index entries if needed
```