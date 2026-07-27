# ToolRouter YAML Evidence Workbench

Date: 2026-07-24

## Requirement

The authenticated Sources evidence site must accept an API collection YAML,
build the ToolRouter graph/index, run GRAG queries, and generate an independently
reviewed evalset. API remains a connector under Sources; the pipeline stages do
not become product nodes.

## Implemented Surface Change

- Added an explicit four-stage evidence rail to `SourceDebugSurface`:
  API collection, graph/index, GRAG retrieval, and reviewed evalset.
- Each stage derives its waiting, active, or complete state from the existing
  real Source, retrieval, evalset, and busy states.
- Added responsive four-, two-, and one-column rail layouts.
- Extended the existing component contract to prove YAML multipart upload and
  every pipeline transition.

## Live Product Evidence

- URL: `http://127.0.0.1:5199/sources?resume_handle=resume_coqSGYmZ4TJlAWLn03eG_T4t`
- Owner path: create local owner -> Home -> Open Sources debug.
- Input: `D:\Dev\AI Projects\openapi-toolrouter-benchmark\artifacts\targets\ory_kratos\raw_openapi\api.yaml`.
- Build: 56 endpoints, 477 graph nodes, 876 graph edges, 477 cards.
- Query: `create a new identity`.
- Decision: `ASK_DISAMBIGUATE`, reason `low_score_margin`.
- Top result: `api:createRecoveryLinkForIdentity`, score 0.4280.
- Evalset: `api-debug-v1`, 1 accepted / 1 completed, 0 quarantined.
- Models: `gemma4:latest` generator and `qwen2.5-coder:7b` reviewer.
- Offline tokens: 2,936.
- Browser warnings/errors: none.
- Responsive proof: 1440x900 and 390x844; mobile document width 390/390.

## Evidence Images

- `C:\Users\ragha\.codex\visualizations\2026\07\22\019f895d-bb32-7f31-94ab-df128085c19c\toolrouter-yaml-pipeline-1440.png`
- `C:\Users\ragha\.codex\visualizations\2026\07\22\019f895d-bb32-7f31-94ab-df128085c19c\toolrouter-yaml-pipeline-mobile.png`

## Runtime

- Frontend remained on the local Vite server at `http://127.0.0.1:5199/`.
- Backend ran locally with Uvicorn on `http://127.0.0.1:8099/`.
- The evidence run used `.runtime/evidence-routedeck-3.sqlite` so a stale prior
  browser session could not be mistaken for successful pipeline execution.
- No fallback, fixture, alternate parser, cached product result, or mock model
  was used in the rendered product path.
