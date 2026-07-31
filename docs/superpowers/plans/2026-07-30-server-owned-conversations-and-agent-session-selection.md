# Bearer Authentication, Conversation Selection, And Reconnectable RouteDeck Runs

Status: completed 2026-07-31. Final implementation/evidence is recorded in
`logs/20260731_server_owned_conversations.md`. RouteDeck modification authority
was limited to this plan and does not carry forward.

## Summary

Replace the browser-cookie session model with a client-neutral protocol:

```text
Bearer token -> caller identity
Conversation ID -> selected conversation
Corpus -> authorization and RouteDeck-session resolution
RouteDeck -> active run and durable conversation state
```

The same API serves web, mobile, desktop, and CLI clients. The implementation
has three modules and reuses RouteDeck's existing session store, turn lease,
request idempotency, and restart recovery.

## Module 1: Bearer Identity

- Replace auth, guest, and owner-route cookies with opaque access/refresh token
  pairs returned as JSON.
- Use `Authorization: Bearer <access_token>` on anonymous and owner requests.
- Issue anonymous credentials through `POST /api/auth/anonymous`. Registration
  and sign-in adopt the selected anonymous conversation, revoke the anonymous
  credentials, and issue owner credentials.
- Access tokens live for 15 minutes. Rotating refresh tokens retain the current
  7-day idle and 30-day absolute limits.
- Store only token hashes. Refresh rotation is atomic; a stale refresh token
  fails.
- Expose `POST /api/auth/refresh`, `POST /api/auth/sign-out`, and bearer-backed
  `GET /api/auth/session`. Password reset revokes all owner token pairs.
- Browser access tokens stay in memory; refresh tokens live in IndexedDB behind
  a credential adapter and serialized refresh lock. Mobile clients use secure
  platform storage through the same adapter contract.
- Remove cookie configuration, cookie mutation, `/api/auth/recover`, and
  cookie-dependent session selection. Retain CORS, rate limits, and secret
  redaction.

Token responses contain opaque access/refresh tokens, their expiries, and an
anonymous or owner principal view.

## Module 2: Corpus Conversations

- Add a Corpus-owned conversation record with a public opaque ID, exactly one
  anonymous-session or owner-user association, an internal RouteDeck session
  ID, timestamps, and archive state.
- RouteDeck session IDs never leave the backend.
- Provide `GET /api/conversations`, `POST /api/conversations`, and
  `GET /api/conversations/{conversation_id}`.
- Anonymous principals may own one active conversation; owners may own many.
- Existing-owner sign-in adopts and keeps the current anonymous conversation
  selected.
- Session-bound RouteDeck requests carry both headers:

```http
Authorization: Bearer <access_token>
X-Corpus-Conversation-ID: <conversation_id>
```

- Corpus's RouteDeck session selector authenticates the bearer principal,
  authorizes the public conversation ID, and returns the internal RouteDeck
  session ID.
- The frontend stores only the selected conversation ID in `sessionStorage`,
  validates it against the catalog, otherwise selects the most recently
  updated item, and creates a conversation when the catalog is empty.
- Catalog and connection support ship now; visible switching UI is deferred.
- Foreign, missing, malformed, or archived conversation IDs fail explicitly
  and never select another conversation.

Conversation summaries include public ID, node, session version, updated time,
and an optional active run summary. They never contain internal IDs.

## Module 3: RouteDeck Active Runs And Declarative Entry Turns

- Decouple model execution from the SSE iterator. Starting a turn creates one
  server task; SSE connections are subscribers only.
- Reuse the existing turn lease as durable active-request authority and
  existing mutation/history records as terminal truth. Do not add renewable
  leases, a recovery worker, or a separate durable run store.
- Keep active task, transient accumulated output, stage, cursor, and subscriber
  state in a process-local coordinator keyed by session and request ID.
- Provide:

```http
POST /api/routedeck/conversation/runs
GET  /api/routedeck/conversation/runs/{request_id}
GET  /api/routedeck/conversation/runs/{request_id}/events?after={cursor}
```

- Starting with the same request ID and fingerprint attaches; conflicting reuse
  fails. Reconnection resumes from the last accepted monotonic cursor.
- Stages are `starting`, `awaiting_model`, `generating`, `completed`, and
  `interrupted`.
- Client disconnect removes only the subscriber. Agent/store failure interrupts
  through the existing durable path. Backend restart uses RouteDeck's existing
  abandoned-turn recovery and does not resume model generation.
- Remove the frontend 30-second convergence timer and all conversation-failure
  authentication resets.
- Add an optional generic node `EntryTurnDeclaration` with
  `once_per_session_node` occurrence. Corpus declares `welcome` on Lounge home;
  RouteDeck derives request identity and starts it on node entry.
- Interrupted entry runs do not silently repeat. The frontend contains no
  Lounge node check or greeting request ID.

## Verification

- Prove bearer issuance, expiry, rotation, revocation, sign-out, password-reset
  revocation, and absence of auth/session cookies.
- Prove anonymous-to-owner adoption retains the public conversation and
  RouteDeck history; foreign conversation access fails.
- Prove every session-bound RouteDeck request carries both headers.
- Through real local TCP, start a real Ollama turn, disconnect, reconnect by
  cursor, and observe one model invocation and one terminal mutation.
- Restart during a controlled turn and verify a durable interrupted result
  without losing the conversation or owner identity.
- Prove Lounge entry fires once without frontend product literals.
- Run backend/frontend/RouteDeck focused suites, typechecks, builds, local smoke,
  and documentation coverage.

## Constraints

- No compatibility migration; update the initial development schema directly.
- No new dependency, Git operation, commit, push, database reset, or deployment.
- The backend remains one Uvicorn worker. Multi-process live-run handoff is
  deferred.
- Partial output survives client reconnect within one backend process, not a
  backend restart.
- HTTPS is mandatory outside local development.
- `docs/corpus-agent-design/feature-behavior-notes.md` is user-owned and must not
  be modified.
