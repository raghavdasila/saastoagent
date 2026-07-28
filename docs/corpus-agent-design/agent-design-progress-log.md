# Corpus Agent Design Progress Log

- 2026-07-27 - Locked Slice 1 to Workspace first and Agents second, with feature behavior designed before cross-feature handoffs or RouteDeck extraction.
- 2026-07-27 - Created the raw `design-corpus-features` skill for atomic behavior inventories, one behavior story at a time, mock interactions only where useful, and explicit user acceptance.
- 2026-07-27 - Rejected an overbuilt design workspace and reduced the review unit to feature, user story, mock chat, mock surface, and approve or reject.
- 2026-07-27 - Built the local shadcn workbench under `docs/corpus-agent-design/workbench` with story creation and editing, local persistence, review locking, and bounded viewport scrolling.
- 2026-07-27 - Kept surface previews surface-only as sandboxed static iframe reproductions rather than copies of the Corpus shell or live product code.
- 2026-07-27 - Added a persisted system-aware light and slate-dark theme to the workbench and its static surface previews.
- 2026-07-27 - Added and approved seven implementation-backed Workspace authentication stories covering registration, sign-in, sign-out, reset request, password change, verification resend, and verification confirmation.
- 2026-07-28 - Clarified the production surface boundary: RouteDeck projects public state and legal affordances, product React components render them, and Corpus APIs retain product truth.
- 2026-07-28 - Recorded authentication-continuation recovery as GitHub issue `raghavdasila/saastoagent#1`; projected conversation-input policy and compiled-contract registry enforcement remain proposals only.
- 2026-07-28 - Committed the current Corpus design skill and workbench as `5ce8929`; no new behavior implementation or RouteDeck extraction was authorized.
- 2026-07-28 - Next design step is to resume the draft Workspace behavior `Enter the workspace`, review one atomic behavior at a time, and move to Agents only after Workspace behavior is accepted.
