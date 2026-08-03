# Corpus New Conversation Implementation Plan

> **For agentic workers:** Execute this plan inline and track the checkboxes. Do not use a worktree, subagent, or Git operation unless the user separately authorizes it.

**Goal:** Let anonymous visitors and authenticated owners deliberately start a fresh Corpus conversation without changing identity, Workspace, owner memory, or domain records.

**Architecture:** Corpus owns public conversation creation, authorization, replacement, selection, and product UI. Each public conversation maps opaquely to one RouteDeck session provisioned through the existing `RouteDeckRuntime.provision_session(...)` boundary; RouteDeck continues to own all state inside that session. Anonymous replacement provisions first and then atomically swaps the Corpus mapping, while owner creation preserves earlier conversations.

**Tech Stack:** FastAPI, SQLAlchemy async, React 19, TypeScript, `@routedeck/core`, `@routedeck/react`, pytest, Vitest.

## Global Constraints

- Authoritative repository: `D:\Dev\AI Projects\saastoagent-v0.1`.
- Backend ownership: `backend/src/corpus/auth/**`; frontend ownership: `frontend/src/app/**`.
- RouteDeck is read-only and receives no changes.
- Do not change Design Studio state or `contracts/corpus-agent-design-routedeck-manifest.json`.
- Do not add dependencies, migrations, compatibility paths, fallback behavior, or conversation-history UI.
- Never expose an internal RouteDeck session ID to the browser.
- Disable New conversation while the current RouteDeck interaction is active.
- A new conversation preserves authenticated owner, Workspace, Corpus owner memory, agents, sources, and other domain state.
- No Git operations.

---

### Task 1: Add explicit anonymous replacement semantics

**Files:**
- Modify: `backend/src/corpus/auth/service.py`
- Modify: `backend/src/corpus/auth/conversations.py`
- Test: `backend/tests/auth/test_conversations_http.py`

**Interface:**
- Existing `POST /api/conversations` remains the creation endpoint used for initial anonymous creation and additional owner conversations.
- Add `POST /api/conversations/{current_public_id}/replacement` for an authenticated anonymous bearer to replace its exact active conversation.
- Both endpoints return the existing strict `ConversationView`; neither exposes the internal RouteDeck session ID.

- [ ] Add failing HTTP tests proving an anonymous replacement returns a different public ID, makes the previous public ID unavailable, and starts at the compiled application entry node.
- [ ] Add failing tests proving the replacement rejects an owner bearer, a foreign conversation, a stale conversation, and a missing conversation without changing the caller's current mapping.
- [ ] Add a service operation that accepts the resolved anonymous principal, exact current public ID, and new internal session ID, then archives the old mapping and creates the new mapping in one database transaction.
- [ ] In the replacement route, authorize same-origin mutation and bearer ownership, generate fresh private session/request IDs, and call `RouteDeckRuntime.provision_session(...)` before the database swap.
- [ ] If provisioning fails, return the failure and leave the old mapping untouched. If the database swap fails, return the failure and leave the old mapping active; do not report or select the unbound RouteDeck session.
- [ ] Keep owner creation on `POST /api/conversations`: it creates another mapping and preserves all earlier owner conversations.
- [ ] Run `\.venv\Scripts\python.exe -m pytest backend\tests\auth\test_conversations_http.py -q` and the focused integration test that proves bearer-selected RouteDeck access.

### Task 2: Introduce one Corpus conversation lifecycle controller

**Files:**
- Create: `frontend/src/app/conversationLifecycle.ts`
- Modify: `frontend/src/app/conversations.ts`
- Test: `frontend/src/tests/conversation-selection.test.ts`

**Interface:**
- Extend the existing conversation client with `replaceAnonymous(currentId)` calling the new replacement endpoint.
- `CorpusConversationLifecycle.startNew({ anonymous: boolean }): Promise<void>` owns creation/replacement, selection, RouteDeck client construction, canonical history load, mounting, and disposal.
- The lifecycle retains the bearer-only authorized transport and recreates only conversation-scoped RouteDeck resources.

- [ ] Add failing tests for owner creation and anonymous replacement request paths and strict error propagation.
- [ ] Add lifecycle tests proving the selected public ID is written to per-tab `sessionStorage` only after the backend returns a valid `ConversationView`.
- [ ] Build the replacement RouteDeck client, chat client, store, private-form state, history, and surface registry against the new selected conversation.
- [ ] Do not dispose the old RouteDeck resources until the new conversation response is accepted and the replacement mount is ready to take ownership.
- [ ] After successful handoff, dispose the old RouteDeck store and private-form state exactly once and remove old run subscriptions through those public disposal contracts.
- [ ] If backend creation fails, retain the old selected conversation and mounted resources. If frontend mounting fails after successful anonymous replacement, retain the new public ID and show explicit recovery for that new conversation; do not fall back to the archived old conversation.
- [ ] Preserve the transport split: Sources and identity use the bearer-only transport; only RouteDeck clients receive the conversation transport.

### Task 3: Add the Corpus shell control

**Files:**
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/app/CorpusHeader.tsx`
- Test: `frontend/src/tests/main-transport-composition.test.tsx`

**Interface:**
- `CorpusHeader` receives an `onNewConversation(): Promise<void>` callback from the Corpus lifecycle owner.
- The header reads `useRouteDeckProjection()` and disables the action when `projection.interaction.phase === "active"` or a new-conversation request is pending.

- [ ] Add failing shell tests for the visible New conversation control, active-turn lockout, duplicate-click lockout, owner creation, and anonymous replacement selection.
- [ ] Refactor the current one-shot startup into the lifecycle controller without creating a second RouteDeck state authority.
- [ ] Render New conversation in the existing Corpus header with accessible text at desktop and representative mobile width.
- [ ] Keep the current shell visible while the request is pending; show a clear Corpus-owned error if creation or remounting fails.
- [ ] Preserve owner-session context, authorized `SourceClient`, navigation, Navgraph inspector, authentication transitions, and the existing pagehide disposal behavior.
- [ ] Prove the recent main transport-composition contract still passes: Source and identity clients remain bearer-only and RouteDeck remains conversation-scoped.

### Task 4: Align product wording and verify the real path

**Files:**
- Modify: `docs/corpus-product-definition.md`
- Modify: `architecture/components/corpus-routedeck-boundary.md`
- Modify: `SYSTEM_FLOW_INDEX.md`

- [ ] Clarify that Corpus provides a permanent conversational interface with multiple owner conversation threads; it does not require one eternal thread.
- [ ] Document that new conversation is a Corpus host-shell action, not a RouteDeck Node, Operation, transition, policy, or recovery action.
- [ ] Record that owner memory and Workspace/domain state survive conversation changes while RouteDeck session-local navigation, history, forms, bindings, reviews, and interaction state start fresh.
- [ ] Run backend tests, frontend tests, strict frontend typecheck/build, the checked-in contract check, and documentation coverage using the commands in `test_index/README.md`.
- [ ] Run locally with `docker compose up --build -d backend frontend`.
- [ ] At `http://127.0.0.1:5199/`, prove: anonymous replacement; old anonymous public ID rejection; owner sign-in/adoption; owner new conversation with the earlier conversation still listed; active-turn disabled state; fresh entry conversation; desktop and mobile rendering; and visible failure behavior.
- [ ] Verify `http://127.0.0.1:8099/readyz` returns HTTP 200 and report the local command and both exact URLs.

## Acceptance Criteria

- New conversation is available to anonymous and authenticated users and cannot run during an active turn.
- Anonymous replacement never removes the usable old mapping before the new RouteDeck session is provisioned.
- Owner conversation creation preserves earlier conversation mappings.
- A successful new conversation has fresh RouteDeck session-local state and the correct entry-node behavior.
- Owner identity, Workspace, owner memory, agents, sources, and domain records remain unchanged.
- No raw RouteDeck session ID reaches the browser.
- No RouteDeck, Design Studio, manifest, dependency, migration, fallback, or Git change occurs.
