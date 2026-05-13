# Persistent Quick Actions Validation

## Test Approach

Persistent quick actions are backend-owned and distinct from contextual graph actions. Validation should cover protocol shape, frontend rendering, sidebar dispatch, and direct workspace route startup.

## What To Validate

- Anonymous `/` bootstrap returns or fetches persistent actions containing:
  - `intent.sign_in`
  - `intent.register`
  - `entry.learn.platform`
  - `entry.learn.setup`
- Contextual `available_actions` can be empty while persistent auth actions still render.
- Action dock remains visible whenever backend/RouteDeck actions exist, even before a user sends the first message.
- During deterministic auth nodes (`display_name`, `email`, `password`), persistent auth actions are suppressed to avoid conflicting action loops.
- Direct anonymous `/w/:workspaceId` fetches `/api/entry/persistent-actions?workspace_id=...` and renders Sign In/Create Account while leaving workspace chat usable.
- Sidebar Sign In/Create Account dispatches backend action ids even when the current contextual action list is empty.
- Clicking Sign In from direct workspace chat switches the unified shell into entry/email composer mode without replacing the page shell.
- `Open Chat` is not reintroduced as a persistent quick action inside the central chat.

## Current Evidence

- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.
- Entry quick-action visibility regression fix validated by frontend type-check/build after streaming bubble changes.
- Temporary Playwright smoke passed for anonymous landing, direct workspace quick actions, Sign In -> email transition, and mobile side panel fit.

## How To Run Current Checks

```powershell
python -m compileall backend
cd frontend
npm run type-check
npm run build
```

The Playwright smoke was run from a temporary harness because `@playwright/test` is not a repo dependency yet. Add repo-native frontend tests before treating this as automated coverage.
