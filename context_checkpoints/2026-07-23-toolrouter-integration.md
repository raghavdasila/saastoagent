# ToolRouter Integration Checkpoint

Date: 2026-07-23

## Restart State

Corpus now has eight live RouteDeck nodes: seven Workspace nodes and one
owner-only `sources.home` debug node. API is a connector beneath generic
Sources. Upload, normalized parsing, resource-first graph/index construction,
GRAG retrieval, and real Gemma/Qwen evalset generation/review are implemented
behind neutral Source contracts.

The earlier behavior-notebook slice is committed as `2e2a3d9`. The
ToolRouter/Sources implementation is present but not committed, alongside
pre-existing concurrent auth/UI work. Do not stage broadly.

## Read First

- `docs/toolrouter-integration-requirements.md`
- `plans/2026-07-23-toolrouter-integration.md`
- `architecture/components/toolrouter-source-integration.md`
- `decisions/ADR-003-vendored-toolrouter-adapter.md`
- `backend/src/corpus/integrations/toolrouter/SOURCE.md`
- `logs/20260723_toolrouter_integration.md`

## Critical Boundaries

- Generic Sources files may not import ToolRouter. Only
  `features/sources/connectors/api/` performs translation.
- No feature may import `integrations/toolrouter/engine` directly.
- Source identity/revision paths are server-generated compact opaque values;
  user labels never become directories.
- Missing parser, MiniLM, Ollama, model digest, graph/index, or evalset artifact
  must fail visibly. Do not add fallbacks.
- Generated/reviewed candidates are not human gold; semantic GRAG is
  experimental.
- The sibling ToolRouter checkout is provenance/reference only at runtime.

## Fresh Evidence

- Backend: 52 passed.
- Frontend: 19 passed; strict typecheck/build passed.
- Python dependencies: no broken requirements.
- Repository unittest: 12 passed.
- Ory upload: 56 endpoints, 316 schemas, two security schemes, 477 nodes, 876
  edges, 477 cards.
- Retrieval: `ASK_DISAMBIGUATE`, `low_score_margin`, top
  `api:createRecoveryLinkForIdentity` at 0.4280; passed again after page reload.
- Real evalset: 1/1 completed and accepted, zero quarantined, 2,936 offline
  tokens, exact Gemma/Qwen digests retained.
- Desktop/390x844 browser checks passed; no warning/error logs; backend ready.

## Run

```powershell
ollama pull gemma4:latest
ollama pull qwen2.5-coder:7b
.\scripts\init-local.ps1
.\scripts\run-backend.ps1
.\scripts\run-frontend.ps1
```

Smoke URLs:

- `http://127.0.0.1:8099/readyz`
- `http://127.0.0.1:5199/`
- authenticated Sources through Home -> Open Sources debug

## Next Concrete Step

Reconcile Agent Designer behavior and its agent-configuration contract. Keep
planner/executor selection open until that discussion. Consume Sources through
the neutral public feature contracts; do not wire Agent Designer directly to
the API connector or ToolRouter engine.

