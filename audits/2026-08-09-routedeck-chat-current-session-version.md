# RouteDeck change: current session version for chained chat

Date: 2026-08-09

## Why the framework changed

Corpus can complete one or more declared RouteDeck operations while preparing a
chat submission. The concrete launch path is an Agent-bound API attachment:
open Source creation, persist the Source, and attach its exact revision before
sending the user's accompanying message. Those operations advance the same
RouteDeck session. React retains the original submit callback while the async
attachment work completes, so `useRouteDeckConversation` previously sent the
session version captured before those operations and RouteDeck correctly
rejected the chat turn with HTTP 409.

Conversation version selection is framework-owned. The operation mutation
controller already reads the current RouteDeck store at dispatch time; chat now
supports the same current-state boundary without weakening optimistic
concurrency or retry semantics.

## RouteDeck files changed

- `packages/react/src/conversation/useRouteDeckConversation.ts`
  - Adds the optional `currentSessionVersion` reader.
  - Reads it only when creating a new chat request.
  - Retained outcome-unknown retries still replay their original immutable
    request and expected version.
- `packages/react/src/conversation/useRouteDeckConversation.test.tsx`
  - Proves a chat send uses session version 8 after an earlier operation moved
    the session from the render-time version 4.

## Corpus composition

- `frontend/src/app/AgentShell.tsx` supplies
  `runtime.store.getState().sessionVersion` as the current reader.

No RouteDeck HTTP, persistence, review, navigation, or operation contract was
changed. A stale session is still rejected; only the authoritative version is
read at the moment a new chat request is created.
