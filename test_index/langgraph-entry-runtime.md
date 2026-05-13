# LangGraph Entry Runtime Validation

Date: 2026-05-13

## Scope

Validation for the LangGraph-owned entry/auth/setup runtime, RouteDeck-to-runtime parity, live entry streaming, and UI-driven QA coverage.

## What To Validate

- Entry/auth/setup/workspace handoff executes through a central LangGraph topology rather than a dispatch-only wrapper.
- Every RouteDeck manifest node has an executable stage handler.
- Every RouteDeck edge condition has an executable resolver.
- Runtime finalization rejects handler transitions that are not executable RouteDeck edges.
- `selected_action_id` is validated before business logic.
- Typed non-LLM nodes keep `nav.back` and `nav.cancel` available.
- Invalid input recovery keeps recovery navigation visible.
- Public entry text streams through live `message_delta` events rather than delayed post-hoc chunk replay.
- Entry thinking state stays inside the streaming assistant bubble.
- Backend quick actions remain visible whenever backend/RouteDeck actions exist.
- The embedded QA agent can drive the real UI through composer/actions/forms/RouteDeck without direct node jumps.

## Current Evidence

- `python -m pytest backend/tests`: passed with 19 tests.
- `python -m compileall backend`: passed.
- `python -m backend.services.route_deck.validate`: passed.
- `../routedeck/python -m pytest tests`: passed with RouteDeck core and LangGraph adapter coverage.
- `frontend/npm run type-check`: passed.
- `frontend/npm run build`: passed.
- Backend tests cover:
  - RouteDeck manifest validity/completeness
  - RouteDeck node/handler parity
  - RouteDeck edge/resolver parity
  - auth cancel/back/switch recovery
  - typed-node recovery navigation
  - workspace/setup recovery actions
  - public assistant streaming path and no fake token chunking regression
- Embedded QA service tests cover scenario catalog, domain model, reset path, and deterministic evaluator behavior.

## How To Run Current Checks

```powershell
python -m pytest backend/tests
python -m compileall backend
python -m backend.services.route_deck.validate
cd ..\routedeck
python -m pytest tests
cd ..\saastoagent-v0.1\frontend
npm run type-check
npm run build
```

Browser-level execution is improved by the embedded QA panel, but repo-native browser automation still needs to be formalized before treating this as full end-to-end coverage.
