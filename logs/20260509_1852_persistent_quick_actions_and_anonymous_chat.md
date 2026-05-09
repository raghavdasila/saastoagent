# Log - 2026-05-09 6:52 PM - Persistent Quick Actions And Anonymous Chat

## Accomplished

- Added a backend-owned persistent quick actions contract separate from contextual graph `available_actions`.
- Added `persistent_actions` to entry turn responses and frontend entry state.
- Added `GET /api/entry/persistent-actions` so direct workspace routes can receive Sign In/Create Account/Learn/Setup actions without frontend hardcoding.
- Rendered persistent actions in a compact rail near the composer while keeping contextual action cards inline in the chat thread.
- Updated sidebar action dispatch to resolve backend action ids from persistent actions first, then contextual actions.
- Allowed anonymous direct workspace chat through the workspace agent endpoint with configurable IP-based rate limiting.
- Fixed direct `/w/:workspaceId` startup, mobile side panel sizing, bad starter prompt wording, bogus `Bearer undefined/null`, and workspace name normalization for conversational setup phrases.

## Files Changed

- `backend/core/schemas/entry.py`
- `backend/routes/entry.py`
- `backend/routes/agent.py`
- `backend/services/entry_runtime/ui_actions.py`
- `backend/services/entry_runtime/orchestrator.py`
- `backend/services/agent/anonymous_rate_limit.py`
- `frontend/src/components/OperatorGateway.tsx`
- `frontend/src/stores/entryStore.ts`
- `frontend/src/types/entry.ts`
- `frontend/src/hooks/useSSEChat.ts`
- `frontend/src/index.css`
- `frontend/src/lib/api.ts`
- `context.md`
- `SYSTEM_FLOW_INDEX.md`
- `test_index/persistent-quick-actions.md`

## Decisions

- `available_actions` remain graph-node contextual actions.
- `persistent_actions` are the stable, backend-owned action layer for global/auth/setup actions.
- Anonymous Sign In/Create Account must be available across entry, learn/setup, and direct workspace chat unless the user is inside deterministic auth collection.
- The frontend may render and dispatch backend actions, but it should not invent auth actions locally.
- Direct workspace chat can be anonymous for this slice, guarded by process-local IP rate limiting.

## Validation

- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Playwright smoke passed:
  - anonymous landing shows backend-provided Sign In/Create Account quick actions
  - direct anonymous workspace route shows backend-provided auth quick actions
  - Sign In enters email collection
  - direct workspace chat remains visible
  - mobile side panel fits viewport

## Issues Encountered

- `rg` is unavailable in this shell, so targeted searches used `Select-String`.
- Playwright is not installed in the frontend package; smoke tests were run from a temporary external harness without changing package dependencies.
- Existing dev servers must be restarted to load the new backend route and frontend CSS.

## Next Steps

- Browser QA the full live stack after restart.
- Add repo-native frontend tests for persistent action rail and sidebar action dispatch.
- Wire generated REST tools into workspace agent chat execution.
- Replace in-memory anonymous rate limiting with shared storage if multi-process deployment becomes relevant.
