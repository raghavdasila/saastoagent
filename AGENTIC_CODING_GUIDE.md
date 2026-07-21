# Corpus Agentic Coding Guide

This repository uses the
[Context Architecture Bundle](https://github.com/saastoagent/context_architecture_bundle)
as its durable project-memory and documentation-ownership model. The initial
setup was reconciled against upstream commit
`e68dc62fe2083193bf2111b95c670cdd815d0f72` on 2026-07-21.

The upstream
[Agentic Coding Guide](https://github.com/saastoagent/context_architecture_bundle/blob/master/AGENTIC_CODING_GUIDE.md)
explains the model. This file defines its Corpus-specific operating sequence.

## Start Or Resume Work

Read, in order:

1. `critical_prompt.md`
2. `context.md`
3. the latest dated file in `context_checkpoints/`
4. `instructions.md`
5. `context_pipeline.md`
6. `architecture/code-map.md`
7. the relevant document in `architecture/components/`
8. any active plan in `plans/`

Use live source, executable tests, and current RouteDeck contracts as
implementation truth. The ignored `benchmark/` tree is evidence only.

## Before A Source Or Asset Change

1. Identify the owning row in `architecture/code-map.md`.
2. Identify the affected component, product, decision, and validation owners.
3. State the smallest coherent implementation slice.
4. Run the applicable command from `test_index/README.md` before and after the
   change when a baseline exists.
5. Do not create imports or runtime dependencies on `benchmark/`.

## Feature Completion

1. Prove the requested runtime and user-visible behavior through the real path.
2. Update product docs only if product behavior changed.
3. Update the code-map row and component doc if ownership, interfaces,
   invariants, tests, dependencies, risks, or update triggers changed.
4. Update `SYSTEM_FLOW_INDEX.md` only if a runtime or UX flow changed.
5. Update `test_index/` with exact executable commands and their meaning.
6. Add or update an ADR only for a durable direction, boundary, compatibility,
   migration, or rejected-alternative decision.
7. Refresh `context.md` as a concise restart snapshot.

## End A Session

Follow `work_prompt.md`. In particular:

1. create a dated log and checkpoint;
2. archive the prior `context.md` when its meaning changed;
3. reconcile each changed source file to a code-map row;
4. record updated or explicitly unchanged architecture and test anchors;
5. run `python scripts/check_doc_coverage.py` and applicable executable gates;
6. leave `context.md` short enough to start the next session without transcript
   archaeology.

## Information Ownership

Each fact has one owner, defined in `context_pipeline.md`. Link to that owner
instead of duplicating detailed contracts. Keep unknowns explicit; do not turn
assumptions into runtime claims.
