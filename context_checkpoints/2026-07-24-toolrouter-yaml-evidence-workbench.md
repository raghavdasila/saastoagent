# Checkpoint: ToolRouter YAML Evidence Workbench

Date: 2026-07-24

## Completed

- The Sources debug surface accepts the real Ory Kratos OpenAPI YAML.
- The rendered pipeline now states and completes all four ToolRouter stages.
- Real graph/index, GRAG retrieval, and independently reviewed evalset paths
  were exercised from the authenticated owner UI.
- Responsive browser evidence and source-focused automated coverage were
  refreshed.

## Verified Result

`api.yaml` -> 56 endpoints -> 477 nodes / 876 edges / 477 cards ->
`create a new identity` -> `ASK_DISAMBIGUATE` (`low_score_margin`) ->
`api-debug-v1` ready with 1/1 accepted, 0 quarantined, and 2,936 offline tokens.

## Resume Boundary

The ToolRouter pipeline is proven only as the authenticated experimental
Sources debug surface. Agent Designer, Sandbox, public Web, Operations, and
deployment remain deferred. Keep API as a connector under Sources and consume
the existing connector-neutral Source exports when those features are added.
