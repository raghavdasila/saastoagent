# ToolRouter browser evidence

Date: 2026-07-24

## Boundary

- Runtime: local Windows workstation only.
- Notebook: `http://127.0.0.1:8771/#structure`.
- Product: `http://127.0.0.1:5199/sources`.
- API input: the real Ory Kratos v26.2.0 OpenAPI collection from the local
  ToolRouter checkout.
- The Sources surface is experimental debug evidence. Reviewed evalset
  candidates are not human gold.

## Video

`logs/evidence/20260724-toolrouter-sources-walkthrough.mp4`

- Duration: 35 seconds.
- Encoding: H.264, 1920x1080, 10 fps.
- SHA-256:
  `2571A830A7804CABF47E7DE378E2C9C5542870B35FA2D649C8B534DBE0D14040`.
- Construction: five live browser captures collected during the verified run
  and sequenced into one evidence walkthrough. The sequence shows the corrected
  Structure explorer, persisted API source/graph, entered retrieval query,
  retrieval decision/ranking, and completed reviewed evalset.

## Observed results

- The full proposed structure remains in the explorer.
- Implemented files are added beside the proposal and marked green; planned
  files remain amber; folders containing both are blue/mixed.
- Source: `Ory Identities API`, state `ready`.
- Graph: 56 endpoints, 477 nodes, 876 edges, 477 cards.
- Retrieval query: `create a new identity`.
- Decision: `ASK_DISAMBIGUATE`, reason `low_score_margin`.
- Top result: `api:createRecoveryLinkForIdentity` at `0.4280`.
- Evalset `api-debug-v1`: ready, 1 accepted of 1 completed, 0 quarantined,
  2,936 offline tokens, Gemma generator and independent Qwen reviewer.

## Validation commands

```powershell
python -m unittest tests.test_feature_behavior_notebook -v
python scripts/validate_design_notebook.py
python scripts/check_doc_coverage.py
ffprobe -v error -show_entries format=duration,size `
  -show_entries stream=width,height,r_frame_rate,codec_name `
  -of json logs/evidence/20260724-toolrouter-sources-walkthrough.mp4
```
