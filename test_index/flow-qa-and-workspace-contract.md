# Flow QA And Workspace Contract Validation

## Test Approach

This index entry covers the May 13 implementation pass that added stream-aware collapsible assistant sections, expanded embedded QA flow execution, REST/OpenAPI catalog/operator smoke coverage, and corrected the workspace creation flow back to workspace naming/configuration.

## What To Validate

- Assistant responses with two or more sections render `details` panels.
- While streaming, only the newest parsed section is open and previous completed sections are collapsed.
- After completion, the first section is open and later sections are collapsed.
- Backend entry/setup assistant prompts emit explicit markdown section headings.
- Embedded QA fails if backend scenario action names are unsupported by the frontend QA runner.
- Embedded QA can execute:
  - first load
  - signin/cancel/signup
  - invalid email recovery
  - RouteDeck smoke
  - OpenAPI connection preview/activation
  - Actions/Entities catalog views
  - read-safe generated REST execution trace
  - write approval-required response
- Workspace creation asks for a workspace name/configuration, not a SaaS job or operator ownership prompt.
- RouteDeck manifest copy does not include `SaaS job`, `operator should own`, or `workspace job`.
- Generated REST operator matching can infer Petstore `status=available` from a normal read-safe prompt.

## Automated Coverage

- `backend/tests/test_entry_assistant.py`
  - pre-auth API draft no longer invents a workspace job
  - explicit workspace names are preserved as workspace names
- `backend/tests/test_qa_service.py`
  - scenario catalog includes new connection/catalog/operator scenarios
  - evaluator checks workspace view, catalog totals, API status, tool calls
  - frontend QA runner supports every backend scenario action
- `backend/tests/test_rest_catalog.py`
  - OpenAPI preview/entities behavior
  - generated REST operator token splitting and status inference
- `backend/tests/test_route_deck_contract.py`
  - RouteDeck runtime parity
  - workspace creation copy drift guard

## Browser Smoke Evidence

Temporary Playwright harnesses validated:

- collapsible streaming state: previous section collapsed, newest section open with `data-section-state="streaming-active"`
- completed collapsibles: first section open, later sections closed
- entry auth back/cancel/invalid email flows
- signup -> workspace-name prompt -> workspace confirm
- Petstore OpenAPI setup -> Connection Confirm -> activation with 19 generated tools
- setup Back/Cancel/Edit Details recovery
- Actions and Entities canvases
- read-safe operator tool trace: `findpetsbystatus(status: available)`
- write request returns approval-required copy and does not silently execute POST
- embedded QA panel passes old and new scenarios

## How To Run Current Checks

```powershell
python -m pytest backend/tests
python -m compileall backend
python -m backend.services.route_deck.validate
cd frontend
npm run type-check
npm run build
```

Then rebuild and smoke locally:

```powershell
docker compose up -d --build backend frontend
```

Use Playwright from `frontend/node_modules` against `http://localhost:3007` until repo-native browser tests are added.

## Remaining Test Work

- Promote the temporary Playwright harnesses into committed repo-native tests.
- Add browser assertions for workspace-mode RouteDeck execution states once approval/resume controls exist.
- Add learning-loop QA once governed learning persistence is implemented.
