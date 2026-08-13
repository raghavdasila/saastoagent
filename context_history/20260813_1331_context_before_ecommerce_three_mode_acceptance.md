# Corpus context before ecommerce three-mode acceptance

Archived from `context.md` before the 2026-08-13 QA/review closeout.

At this boundary, all six final-integration feature phases were accepted through
isolated evidence, but the separately authorized complete surface-only,
ordinary-chat-only, and hybrid ecommerce journeys had not yet been recorded in
the current context. The context still cited the August 9 launch baseline:

- surface `20260809T153004Z-7cd51d776b` at 24/24;
- chat `20260809T165131Z-63d1c6220b` at 24/24; and
- hybrid `20260809T210136Z-853c33486c` at 25/25.

The active instruction was to run one current complete journey in each mode
only after the isolated phases, return any failure to its owning feature, and
avoid using a full journey as an integration debugger. The user-owned Behavior
Notes remained untouched, RouteDeck changes were separately reported, and no
Git operation had been made for the final ecommerce integration slice.

This archive is intentionally concise. The full phase history, failed-goal
record, exact prior campaigns, and process constraints remain in
`docs/corpus-agent-design/final-integration-tasks-and-process.md`; the exact old
accepted baseline remains in
`context_checkpoints/2026-08-10-horizontal-evidence-closeout.md`.
