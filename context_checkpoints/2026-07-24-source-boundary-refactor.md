# Checkpoint: Source Boundary Refactor

Date: 2026-07-24

## Completed

- Generic `SourceSettings` now requires only the Source persistence root.
- API owns its upload limit and `/api/sources/api` multipart route.
- `ApiSourceConnector` depends on `ApiSourceEngine`; one explicit
  `connectors/api/toolrouter.py` bridge translates ToolRouter contracts.
- ToolRouter owns all embedding, Ollama, generator/reviewer, and timeout
  settings/environment names.
- Concrete registration moved to `app/source_composition.py`.
- The Structure explorer preserves the proposal and shows every new implemented
  boundary with file-level explanations.

## Verified Result

56 backend and 19 frontend tests passed; typecheck/build and dependency checks
passed. The real Ory YAML product path produced 56 endpoints, 477 nodes, 876
edges, 477 cards, `ASK_DISAMBIGUATE`, and a ready 1/1 reviewed evalset with
2,936 offline tokens and zero quarantined candidates.

## Resume Boundary

Backend and frontend are running locally at ports 8099 and 5199. The Structure
notebook is running at port 8771. Agent Designer remains the next product
contract discussion; do not move connector or ToolRouter settings back into
generic Sources while wiring it.

