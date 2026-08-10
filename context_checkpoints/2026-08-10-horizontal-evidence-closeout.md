# Horizontal evidence closeout

The Corpus launch baseline is horizontally complete through Source, Agent,
Designer, Builder, Sandbox, Evaluation, Channels/Deployment, public hosted
sessions, and Operations.

Accepted local evidence:

- surface-only `20260809T153004Z-7cd51d776b`: 24/24, 18 screenshots,
  288.24-second raw 1x video;
- ordinary-chat-only `20260809T165131Z-63d1c6220b`: 24/24, 18 screenshots,
  581.04-second raw 1x video;
- hybrid `20260809T210136Z-853c33486c`: 25/25, 18 screenshots,
  474.28-second raw 1x video, 968 allowlisted safe-trace events, and zero
  unexpected HTTP, console, page, or request failures.

The immutable chat-only artifact predates exact Playwright Request-object
correlation and records ten `POST /api/routedeck/chat` `ERR_ABORTED` entries;
each required chat turn nevertheless has durable completed product evidence.
The correlation fix is focused-test proven and the replacement hybrid run
browser-proves the corrected zero-unexpected-request diagnostic path.

The hybrid video includes the persisted Source semantic graph; visible Designer
topology; compiled Builder, Evaluation, and deployed RouteDeck NavGraphs;
Sandbox and public ToolRouter clarification; reviewed deployment; restart;
owner-only Operations evidence; and 390x844 rendering. Chat prompts are ordinary
owner language and contain no RouteDeck/Corpus operation, feature, node, route,
or hidden entity identifiers.

Continue with individual behavior-note depth. Do not reopen the accepted
horizontal baseline unless a later change invalidates it. No Git operation and
no user behavior-note edit occurred.

