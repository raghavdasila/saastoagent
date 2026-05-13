# ADR-008 - Live Entry Streaming Contract

Date: 2026-05-13
Status: Accepted

## Context

SaaStoAgent entry chat is an agentic control surface, not a form wizard. Users need immediate feedback when the assistant is thinking and answering. A previous entry-runtime implementation produced a full assistant message through a non-streaming structured LLM call, then split the finished text into delayed `message_delta` chunks. That made the UI look like it was streaming while still forcing users to wait for the whole response.

The main SaaStoAgent project and Neura already use live SSE mapping from model or LangGraph stream events. SaaStoAgent v0.1 should follow that pattern instead of replaying completed text.

## Decision

LLM-generated entry assistant text must stream from the live model or graph event source.

- Public entry assistant turns use a streaming model client and emit `message_delta` events as chunks arrive.
- `message_delta` events for LLM-backed text must not be produced by post-hoc splitting of a completed assistant message.
- The stage output recorder still persists the final assistant message after the handler returns.
- If a message has already streamed live, the stage output recorder records it without replaying deltas.
- Deterministic system messages may emit a single immediate `message_delta` after stage execution; they should not simulate token streaming with sleeps.
- `entry_turn_result` remains the authoritative final payload for state, actions, RouteDeck snapshot, artifacts, and persistence.

## Consequences

- The composer thinking state can clear on the first real `message_delta`, not after the whole LLM response completes.
- Frontend clients should treat `message_delta` as incremental display evidence and `entry_turn_result` as final state reconciliation.
- Structured navigation decisions must be handled before the LLM stream when possible, or represented through deterministic runtime state rather than delaying text for structured output.
- Tests should guard against artificial chunk replay so a future implementation does not reintroduce delayed fake streaming.
