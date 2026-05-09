# Conversational Entry + Canvas Validation

Date: 2026-05-08

## Scope

Validation for the first conversational entry and widget canvas core slice.

## Automated/Scripted Coverage Added

- `backend/tests/test_entry_assistant.py`

These tests cover:

- anonymous platform question returns assistant answer, follow-up prompts, KB citations, and platform overview artifact
- setup request creates a pre-auth `entry_draft` without activation
- explicit auth intent routes deterministically while preserving the existing draft

## Commands Run

```powershell
python -m compileall backend
npm run type-check
npm run build
```

```powershell
python -m pytest backend/tests/test_entry_assistant.py
```

The pytest command did not execute in the current environments:

- host Python has pytest but lacks `pgvector`
- Docker backend has runtime dependencies but lacks `pytest`

Equivalent assistant assertions were validated with a direct in-container Python harness.

## Live Protocol Smoke

Validated through `POST http://localhost:8085/api/entry/turn`:

- anonymous platform question returns `intent`, chip actions, and `platform_overview`
- anonymous setup description persists workspace/API draft and emits `setup_draft_summary`
- register action routes to `display_name` without losing draft
- invalid password keeps the setup draft
- valid signup with draft routes to `workspace_confirm`
- workspace launch returns `setup_intro`
- API draft carries into `connection_draft`

## Remaining Coverage

- browser QA for desktop canvas promotion and mobile inline rendering
- frontend sanitizer tests for scripts, event handlers, iframes, forms, unsafe links, and external loading elements
- full signup -> workspace -> real OpenAPI activation smoke through the visible UI
