# Corpus Work Prompt

Use this workflow to start, complete a feature, or explicitly close a Corpus
development session.

## Session Start

1. Read `critical_prompt.md` and `context.md` first.
2. Read the latest dated checkpoint in `context_checkpoints/`.
3. Read `instructions.md` and `context_pipeline.md`.
4. Read `architecture/code-map.md` and relevant component documents when
   source, tests, contracts, or architecture are in scope.
5. Read any active plan in `plans/`.
6. State the repository boundary, current state, known risks, owning subsystem,
   and next concrete step before changing source.

## Before Source Or Asset Changes

- Identify the owning code-map row and likely changed files.
- Name affected product, RouteDeck, interface, component, decision, and test
  owners.
- Name the real validation path from `test_index/README.md`; if none exists,
  define it with the first implementation.
- Run an existing baseline gate when applicable.
- Confirm no new code, test, or build path imports from `benchmark/`.

## Feature Completion

- Validate requested runtime and user-visible behavior end to end through real
  integrations, persistence, state transitions, errors, and rendered outcomes.
- Update `docs/` if product or developer behavior changed.
- Update the code map and relevant component docs if ownership, interfaces,
  tests, dependencies, risks, invariants, or update triggers changed.
- Update `SYSTEM_FLOW_INDEX.md` only if runtime or UX flows changed.
- Update `test_index/` with exact commands and what they prove.
- Add or update an ADR only for a durable direction, boundary, compatibility,
  migration, or rejected-alternative decision.
- Refresh `context.md` as a concise restart state and list validation results.

## Explicit Session Close

1. Create a dated log in `logs/`.
2. Create a dated checkpoint in `context_checkpoints/`.
3. Archive the previous `context.md` in `context_history/` if its meaning
   changed.
4. Rewrite `context.md` as the concise live snapshot.
5. List changed source files and their `architecture/code-map.md` owner rows.
6. Update affected plans, knowledge, decisions, architecture, product docs, and
   test index; leave unrelated owners unchanged.
7. For each changed source subsystem, update its component/test anchors or
   explicitly record that their documented contracts are unchanged.
8. Run `python scripts/check_doc_coverage.py` and capture notable warnings.
9. Run all applicable executable gates from `test_index/README.md` and record
   exact results, smoke-test commands, runtime location, and URLs.
10. Keep the final handoff compact enough for a clean next-session restart.

The preserved benchmark remains unchanged unless the user explicitly requests
benchmark work.
