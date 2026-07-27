# Source Boundary Refactor Plan

Status: completed and locally validated on 2026-07-24

## Owner Instruction

Remove the hardcoded API and ToolRouter details from generic Sources,
including the API upload behavior in `features/sources/http.py`. ToolRouter
values must remain owned by ToolRouter rather than copied into Sources or the
application factory.

## Plan And Result

- [x] Make the Source data root explicit and keep `SourceSettings`
  connector-neutral.
- [x] Move API upload limit and multipart HTTP behavior into
  `connectors/api/`.
- [x] Introduce `ApiSourceEngine`; make `ApiSourceConnector` depend on the port
  rather than `ToolRouterAdapter`.
- [x] Isolate ToolRouter translation in one API/ToolRouter bridge and concrete
  registration in the host composition root.
- [x] Make `ToolRouterSettings` own all ToolRouter environment names, defaults,
  validation, embedding values, Ollama URL, models, and timeout.
- [x] Preserve the public HTTP paths and real YAML -> graph/index -> retrieval
  -> reviewed-evalset behavior.
- [x] Update the Structure explorer and architecture/test ownership docs.

## Acceptance Evidence

- Backend: 56 passed; `pip check` clean.
- Frontend: 19 passed; strict typecheck and production build passed.
- Notebook unit contract: 10 passed; proposed design remains 15 features,
  53 nodes, and 146 edges.
- Real local Ory YAML product path: 56 endpoints, 477 nodes, 876 edges,
  477 cards; `ASK_DISAMBIGUATE` / `low_score_margin`; evalset ready with 1
  accepted, 0 quarantined, and 2,936 offline tokens.
- Local runtime: backend `http://127.0.0.1:8099/readyz`; frontend
  `http://127.0.0.1:5199/`; Structure explorer
  `http://127.0.0.1:8771/#structure`.

