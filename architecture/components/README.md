# Architecture Components

This folder contains focused component docs for high-change or high-risk
SaaStoAgent areas. It is indexed by `../code-map.md`, which is the canonical
subsystem-to-code map.

Use component docs to answer:

- what the component owns
- which files are authoritative
- which interfaces and flows depend on it
- which tests protect it
- when the doc must be updated

## Component Index

| Component | Purpose | Primary code owners | Tests and evidence |
| --- | --- | --- | --- |
| `routedeck-corpus-boundary.md` | RouteDeck projection, Corpus planning, graph validation, diagnostics, and owner chat/action runtime. | `backend/routes/corpus_graph.py`, `backend/services/app_graph/*.py`, `backend/services/route_deck/*.py`, `frontend/src/components/appGraph/*` | `backend/tests/test_app_graph_contract.py`, `backend/tests/test_corpus_graph_contract.py`, `backend/tests/test_corpus_routedeck_runtime.py`, `backend/tests/test_corpus_routedeck_state.py`, `backend/tests/test_corpus_turn_planning.py`, `test_index/route-deck-contract.md` |
| `owner-workbench-shell.md` | Stable owner shell, auth/SaaS Agent context, product surfaces, and route mount behavior. | `frontend/src/App.tsx`, `frontend/src/components/layout/*`, `frontend/src/context/*`, `frontend/src/components/saasAgent/*` | `test_index/route-deck-contract.md`, `test_index/saas-agent-foundation-contract.md`, frontend E2E scripts |
| `deployed-agent-orchestration.md` | Public deployed SaaS Agent chat, generated API execution, execution-frame variables, and public-safe response shaping. | `backend/routes/deployed_agents.py`, `backend/services/deployed_agents.py`, `backend/services/agent/api_orchestration.py`, `frontend/src/pages/DeployedAgentChatPage.tsx` | `backend/tests/test_api_orchestration.py`, `backend/tests/test_execution_frames.py`, `backend/tests/test_state_variables.py`, `test_index/deployed-agent-orchestration-contract.md` |
| `openapi-provider-discovery.md` | OpenAPI ingestion, provider parsing, discovery activation, and generated action/entity catalog. | `backend/providers/rest/*`, `backend/services/discovery/*`, `backend/services/catalog.py`, `backend/services/tools/generator.py` | `backend/tests/test_rest_catalog.py`, `test_index/saas-agent-foundation-contract.md`, `docs/medusa-api-agent-test-guide.md` |
| `frontend-routedeck-store-bridge.md` | Frontend bridge from RouteDeck/Corpus state to React surfaces, typed dispatch, diagnostics, and local UI stores. | `frontend/src/components/appGraph/*`, `frontend/src/lib/api.ts`, `frontend/src/stores/*`, `frontend/src/types/*` | `test_index/route-deck-contract.md`, `npm run type-check`, frontend E2E scripts |

## Update Rule

If source changes match a subsystem in `../code-map.md`, update the relevant
component doc or explicitly record in closeout that the component contract is
unchanged. Do not expand this folder with one-off session history; use
`logs/`, `context_checkpoints/`, and `dev_validated_docs/` for session evidence.
