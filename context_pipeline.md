# Corpus Context Pipeline

This repository uses a structured context pipeline for continuity, planning,
source traceability, validation, and compact handoffs.

## Goals

1. clean session restarts without transcript archaeology;
2. verified planning before implementation;
3. auditable progress and validation evidence;
4. subsystem-level source, architecture, and test ownership;
5. reusable findings and workflows stored only in their proper owners.

## Ownership Layers

| Layer | Owners |
| --- | --- |
| Vision | `critical_prompt.md` |
| Live state | `context.md`, `structure.md` |
| State history | `context_history/`, `context_checkpoints/` |
| Process | `AGENTIC_CODING_GUIDE.md`, `instructions.md`, `work_prompt.md`, `context_pipeline.md` |
| Architecture | `architecture/code-map.md`, `architecture/components/`, `architecture/diagrams/` |
| Product behavior | `docs/` |
| Runtime and UX flow index | `SYSTEM_FLOW_INDEX.md` |
| Validation meaning | `test_index/` |
| Decisions and history | `decisions/`, `logs/`, `audits/`, `errors/` |
| Planning and knowledge | `plans/`, `knowledgebase/`, `skills/` |
| Historical application evidence | ignored `benchmark/` |

## Session Lifecycle

### Start

Read `critical_prompt.md`, `context.md`, the latest checkpoint,
`instructions.md`, `context_pipeline.md`, the code map, relevant component
documents, and active plans—in that order.

### Plan

Verify uncertain technical details from live source. Identify subsystem owners,
real validation, and affected documentation owners. Record a plan only while it
is active; record a reusable finding only after it is verified.

### Implement

Track changed source files against the code map. Keep contracts, tests, and
documentation aligned with actual behavior. Do not widen scope into unrelated
owners.

### Complete A Feature

Prove the real product path, update affected product/architecture/test owners,
record durable decisions when warranted, and refresh the concise live context.

### Close A Session

Create a log and checkpoint, archive materially changed prior context, reconcile
changed source files to their code-map rows, run applicable executable gates
and `python scripts/check_doc_coverage.py`, then rewrite `context.md` as the
compact restart snapshot.

## Working Rule

Each fact has one primary owner. Link to it instead of duplicating detailed
contracts. `context.md` is not architecture; chat history is not project memory;
the benchmark is not the new runtime.
