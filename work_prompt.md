# Work Prompt - SaaStoAgent v0.1

Use this prompt to start or resume work on SaaStoAgent v0.1.

## Session Start Prompt

```text
I'm working on the SaaStoAgent v0.1 project.

Please:
1. Read critical_prompt.md and context.md first
2. If resuming, inspect the latest checkpoint in context_checkpoints/
3. If needed, inspect the latest context_history entry for deeper background
4. Review instructions.md for the documentation workflow
5. Review architecture/code-map.md and any relevant architecture/components/ doc if source files are in scope
6. Review the active plan in plans/
7. Tell me what the current state is and what the next concrete step should be
```

## Session End Prompt

```text
We're wrapping up this session. Please:

1. Create a log entry in logs/
2. Create a checkpoint in context_checkpoints/
3. Archive the previous context.md into context_history/ if needed
4. Rewrite context.md as the concise live snapshot
5. List changed source files and their owning architecture/code-map.md subsystem rows
6. Update plans, knowledgebase, decisions, architecture, and test_index if this session changed them
7. For each changed source subsystem, update the related component doc/test_index entry or explicitly state that the documented contract is unchanged
8. Run python scripts/check_doc_coverage.py and capture notable warnings
9. Update SYSTEM_FLOW_INDEX.md only if the runtime or UX flows changed
```

## Feature Completion Prompt

```text
The feature is complete. Please:

1. Update docs/
2. Update architecture/
3. Update architecture/code-map.md and relevant architecture/components/ docs if source ownership, interfaces, tests, or update triggers changed
4. Update SYSTEM_FLOW_INDEX.md if flows changed
5. Update context.md
6. Add ADRs or test_index entries if needed
```
