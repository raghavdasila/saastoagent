# Corpus Documentation Instructions

Use this workflow whenever source, runtime behavior, architecture, tests, or
project state changes.

## Default Documentation Flow

1. Follow the read order in `AGENTIC_CODING_GUIDE.md`.
2. Identify the `architecture/code-map.md` row for every changed source file.
3. Change source and documentation in the smallest coherent slice.
4. Run the relevant command from `test_index/README.md`.
5. Update a component document when its interface, ownership, invariant,
   dependency, risk, evidence, or update trigger changed.
6. Update `SYSTEM_FLOW_INDEX.md` only when runtime or UX flow changed.
7. Update `context.md` as a concise restart state, linking to detailed owners.

## Evidence And Authority

- Live source, executable tests, serialized assets, and current RouteDeck
  contracts are implementation truth.
- `benchmark/` is ignored, read-only historical evidence, not architecture.
- Keep unknowns explicit. Do not invent runtime contracts, dependency choices,
  or readiness claims.
- Never edit the benchmark as a side effect of new Corpus implementation.
- No silent mock, fixture, provider, model, cached, or heuristic fallback may
  make a missing dependency appear successful.

## Where Information Belongs

| Information | Owner |
| --- | --- |
| Product north star and non-negotiables | `critical_prompt.md` |
| Current restart state | `context.md` |
| Session evidence | `logs/`, `context_checkpoints/` |
| Archived restart snapshots | `context_history/` |
| Source ownership | `architecture/code-map.md` |
| Subsystem contracts | `architecture/components/` |
| Product and developer behavior | `docs/` |
| Test meaning and commands | `test_index/` |
| Durable architecture decisions | `decisions/` |
| Active implementation work | `plans/` |
| Verified reusable findings | `knowledgebase/` |
| Repeatable procedures | `skills/` |
| Reusable debugging failures | `errors/` |
| Read-only audit reports | `audits/` |

## Source Change Closeout Checklist

- Changed source files and their code-map rows are listed.
- Related component/architecture anchors are updated or explicitly unchanged.
- Related test anchors and validation meaning are updated or explicitly
  unchanged.
- Exact validation commands, outcomes, runtime location, and smoke-test URLs
  are recorded when a runtime exists.
- `context.md` points to current owners instead of duplicating their contracts.
- `python scripts/check_doc_coverage.py` has been run for an explicit closeout.

## Skill Rule

Create a repo-local skill only when the workflow is stable, repeatable, and has
clear invocation criteria, inputs, outputs, checks, and stop conditions. Never
store one-off fixes or session history as skills.
