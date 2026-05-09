# Context Checkpoint - May 9, 2026 6:52 PM

## Completed

- Added persistent backend-owned quick actions separate from contextual `available_actions`.
- Added `persistent_actions` to entry turn responses and frontend state.
- Added `/api/entry/persistent-actions` for direct route startup surfaces.
- Rendered persistent actions near the composer and kept contextual graph actions inline.
- Updated sidebar Sign In/Create Account/Learn/Setup dispatch to use backend-provided actions.
- Enabled anonymous direct workspace chat with configurable IP-based rate limiting.
- Fixed mobile side panel viewport sizing, direct workspace startup mode, invalid bearer token handling, and workspace-name cleanup for natural-language setup phrases.
- Archived the previous `context.md` into `context_history/20260509_1852_context_before_persistent_quick_actions_closeout.md`.

## Current Runtime

- Unified shell: `OperatorGateway`
- Entry protocol: `/api/entry/stream`
- Persistent action protocol: `/api/entry/persistent-actions`
- Workspace chat protocol: `/api/workspaces/{workspaceId}/agent/chat`
- Anonymous workspace chat limit defaults: `10` messages per `3600` seconds per IP.

## Validation Snapshot

- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Temporary Playwright smoke passed for:
  - anonymous landing persistent auth actions
  - direct workspace persistent auth actions
  - Sign In -> email graph transition
  - direct workspace chat visibility
  - mobile side panel viewport fit

## Known Gaps

- Live browser QA should be rerun after restarting current dev servers.
- Persistent action rail and sidebar dispatch need repo-native frontend tests.
- Generated REST tools are still not bound into the workspace agent execution loop.
- Anonymous rate limiting is in-memory and process-local.
- Platform KB and citation UX remain intentionally small for this slice.

## Next Recommended Slice

Restart the stack and run visible QA over anonymous landing, login/signup, workspace creation, API setup, direct workspace chat, and persistent action visibility. After that, wire generated REST tools into workspace chat execution.
