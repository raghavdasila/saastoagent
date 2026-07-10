# RouteDeck v0 compatibility snapshot

This directory is an explicit, pinned compatibility dependency for
SaaStoAgent v0.1. It is not a fallback implementation and is never selected at
runtime based on an error.

- Source repository: the standalone `routedeck` history
- Source commit: `4b4acff9ff21b674f9d2ab354d8419eba999bad2`
- Source commit date: 2026-07-09T13:25:47+05:30
- Source paths: `routedeck_core`, `routedeck_langgraph`, and `react`
- Extraction date: 2026-07-15 (Asia/Calcutta)

This is the last RouteDeck implementation revision preceding the 2026-07-10
Corpus consumer refactor; the intervening RouteDeck commits were documentation
only. Later RouteDeck work established a clean-break canonical architecture and
removed the v0 runtime/projection API that Corpus currently consumes. Vendoring
this exact snapshot makes SaaStoAgent v0.1 reproducible and independent while
keeping that legacy contract quarantined. Migrating Corpus to canonical
RouteDeck is a separate product refactor and must replace this dependency
deliberately; it must not be attempted through an automatic fallback or a mixed
pair of contracts.
