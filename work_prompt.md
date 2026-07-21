# Work Prompt

## Start

Read `critical_prompt.md`, `context.md`, the latest checkpoint,
`instructions.md`, `context_pipeline.md`, `architecture/code-map.md`, the
relevant component document, and any active plan.

## Before Source Changes

- Identify the owning code-map row.
- Name the affected product and RouteDeck contracts.
- Name the real validation path.
- Confirm that no new code imports from `benchmark/`.

## Feature Completion

- Validate the requested runtime and user-visible behavior end to end.
- Update the owning product, architecture, decision, and test-index documents.
- Record exact commands, URLs, outcomes, and remaining gaps.

## Session Close

- Create a concise checkpoint and log when explicitly closing a session.
- Refresh `context.md` with only restart-relevant state.
- Keep the benchmark unchanged unless the user explicitly requests benchmark work.
