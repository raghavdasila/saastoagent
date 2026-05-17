# 2026-05-13 22:30 - SaaS Agent Backend/Frontend Rename

## Scope

- Completed Slice 1 backend rename from Workspace to SaaS Agent.
- Completed Slice 2 frontend shell/store/type/route rename from Workspace to SaaS Agent.
- Preserved the existing operator behavior while changing the product authority.

## Changed

- Backend domain classes/schemas/routes now use `SaaSAgent`, `SaaSAgentMember`, `SaaSAgentRole`, and `saas_agent_id`.
- Backend route prefixes are now `/api/saas-agents`.
- Entry RouteDeck node IDs are now `saas_agent_select`, `saas_agent_job`, and `saas_agent_confirm`.
- RouteDeck framework lane contract now accepts `saas_agent`.
- Frontend route is now `/agents/:saasAgentId`.
- Frontend store/type/component paths now use SaaS Agent naming.
- QA action names and evidence gates now use SaaS Agent naming.

## Verification

- `python -m backend.services.route_deck.validate` passed.
- `python -m pytest backend/tests/test_route_deck_contract.py backend/tests/test_entry_assistant.py backend/tests/test_rest_catalog.py backend/tests/test_qa_service.py` passed with 28 tests.
- `npm run build` in `frontend/` passed.
- Source scan over `backend` and `frontend/src` found no remaining `workspace`, `Workspace`, `/workspaces`, or `/w/` hits outside generated caches.

## Blockers / Notes

- Full `from backend.main import app` import is blocked by missing `fitz`/PyMuPDF in the local environment after reaching the existing RAG import.
- Slice 3 should add editable slug UX and Medusa Storefront/Admin presets.
