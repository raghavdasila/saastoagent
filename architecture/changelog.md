# Architecture Changelog

## 2026-05-05

- Initialized architecture documentation scaffold for `saastoagent-v0.1`
- Adopted product boundary: REST-only workspace agent
- Chose simplified Entity Explorer over the full graph canvas as the v0.1 surface
- Implemented the Slice 1 runnable shell across FastAPI, React, and Docker Compose
- Normalized local runtime to frontend `3005`, backend `8085`, and local `frontend/` naming
- Recorded an architecture correction: re-center the current shell around an agentic workspace home before Slice 2

## 2026-05-09

- Recorded the unified operator shell as the canonical v0.1 experience in `ADR-003`.
- Recorded backend-owned persistent quick actions in `ADR-004`.
- Recorded the typed widget, sanitized markup, and optional canvas artifact contract in `ADR-005`.

## 2026-05-10

- Replaced the planned GraphUI naming with `RouteDeck` across backend, frontend, docs, and framework folders.
- Added the RouteDeck framework split: `routedeck_core` for Python contracts/validation and `@routedeck/react` for reusable frontend types/debugger widgets.
- Moved entry/auth/setup/workspace handoff visibility into a backend-owned RouteDeck manifest and runtime snapshot.
- Added action validation before stage execution so invalid selected actions recover with visible alternatives.
- Added the RouteDeck status strip plus side map with focused graph and scrollable full-site graph visualization.
- Recorded the RouteDeck framework contract in `ADR-007`.
