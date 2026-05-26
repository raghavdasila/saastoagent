# SaaStoAgent Docs

This directory contains operator, developer, and validation guides for the
current SaaStoAgent v0.1 runtime.

Start with the root `README.md` for setup and with `context.md` for the current
handoff state. Use this directory for deeper guides.

## Guides

- [RouteDeck Overview](route-deck/route-deck-overview.md) - concepts, mental
  model, RouteDeck/Corpus boundary, navigation lanes, and anti-patterns
- [RouteDeck Authoring Guide](route-deck/authoring-guide.md) - how to add or
  modify app-graph nodes, surfaces, and operations safely
- [RouteDeck Manifest Reference](route-deck/manifest-reference.md) - current
  object model and validation expectations for RouteDeck-projected state
- [RouteDeck Debugging Guide](route-deck/debugging-guide.md) - how to inspect
  graph state, legal operations, surfaces, and diagnostics
- [Medusa API Agent Test Guide](medusa-api-agent-test-guide.md) - local Medusa
  fixture setup and end-to-end validation path
- [Horizontal E2E Guide](horizontal-e2e.md) - browser harness expectations for
  the owner and deployed-agent flows

## Architecture Anchors

- `../architecture/route-deck-corpus-vision.md`
- `../decisions/ADR-013-routedeck-corpus-boundary.md`
- `../SYSTEM_FLOW_INDEX.md`
- `../../routedeck/docs/using-routedeck.md`
- `../../routedeck/docs/agentic-ui-state-runtime.md`

## Documentation Rules

- Keep setup ports and commands synchronized with `docker-compose.yml` and
  `frontend/package.json`.
- Keep RouteDeck product docs aligned with `backend/services/app_graph/` and the
  `/api/corpus/*` boundary.
- Do not document Medusa as product behavior. It is an acceptance fixture only.
- Do not commit local account credentials, publishable keys, API keys, trace
  IDs, approval IDs, or fixture secrets.
- If docs mention a behavior as current, run at least the lightweight checks in
  the root README before closing the change.
