# 2026-05-17 12:14 - Agent UX Architecture Reframe Closeout

## Summary

The session ended after identifying that the current graph-first/agent-first implementation still does not match the user vision. The implementation is technically graph-based, but conceptually it remains an action-router UI with a chat surface.

## Current Problem Captured

- Chat is not yet the primary agent runtime.
- RouteDeck action eligibility is too directly coupled to visible UI.
- Forms can render before the user initiates an action.
- `home` is still treated like an app/page state rather than the opening context inside the agent conversation.
- The no-model router fallback still behaves like a setup menu instead of an agent.
- Existing validation missed this because it tested plumbing, not the product interaction contract.

## Artifact Updates

- Archived previous context to `context_history/20260517_1214_context_before_agent_ux_architecture_reframe.md`.
- Added checkpoint `context_checkpoints/context_checkpoint_17-05-2026-12-14PM.md`.
- Rewrote `context.md` to mark the current architecture as disputed and point to the new checkpoint.
- Updated flow/test/plan notes to warn against continuing implementation before the agent-turn contract reset.

## Next Session Handoff

Begin with the checkpoint above. Do not keep patching the current UI. First define the corrected agent-turn contract: capabilities are internal, proposals are visible, forms open only after user acceptance, and RouteDeck remains infrastructure/diagnostics rather than product UX.

