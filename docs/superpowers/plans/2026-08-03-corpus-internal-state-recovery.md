# Corpus Internal State Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not use a worktree or subagent. Do not commit or push; stage only files changed by this plan.

**Goal:** Ensure Corpus resolves conversation, state, navigation, link, and RouteDeck recovery conditions internally so users never see a RouteDeck error or framework recovery choice.

**Architecture:** Corpus remains a consumer of RouteDeck's existing projection and recovery contracts. A Corpus-owned browser-history coordinator binds RouteDeck history to the selected opaque public conversation, while a Corpus-owned recovery coordinator executes legal RouteDeck recovery actions automatically and exposes only generic Corpus availability UI after automatic recovery fails.

**Tech Stack:** React 19, TypeScript, `@routedeck/core`, `@routedeck/react`, Vitest, Testing Library.

## Global Constraints

- Repository: `D:\Dev\AI Projects\saastoagent-v0.1`.
- RouteDeck remains read-only; use its current public store and recovery contracts.
- Do not change Design Studio state or the implementation manifest.
- Do not expose RouteDeck names, errors, state codes, navigation conflicts, session mechanics, retained requests, or recovery choices in normal Corpus UI.
- Preserve same-conversation Back/Forward behavior and valid new-tab deep links.
- Do not silently create a RouteDeck session through `/api/routedeck/sessions`; missing or expired conversations recover through the Corpus conversation lifecycle.
- Do not add dependencies, migrations, fallbacks, or history/switcher UI.
- Do not commit or push. Stage only the files changed by this plan after verification.

---

### Task 1: Bind browser history to the selected Corpus conversation

**Files:**
- Create: `frontend/src/app/conversationHistory.ts`
- Modify: `frontend/src/app/conversationLifecycle.ts`
- Modify: `frontend/src/app/bootstrapConnection.ts`
- Test: `frontend/src/tests/conversation-history.test.ts`

**Interfaces:**
- Produces `reconcileConversationHistory(browser, conversation, routes): void`.
- Produces `commitConversationHandoff(browser, conversation, routes): void`.
- Both functions use the existing opaque `ConversationSummary.id`; neither receives a RouteDeck session ID.

- [ ] **Step 1: Write failing ownership tests**

Cover these exact cases with a memory `sessionStorage`, mutable `history.state`, and a stub codec:

```ts
it("discards RouteDeck history owned by another conversation", () => {
  history.state = { routedeck: { version: 1, history_entry_id: 7 } };
  storage.setItem(HISTORY_CONVERSATION_KEY, "cv-old");
  reconcileConversationHistory(browser, conversation("cv-new"), routes);
  expect(history.replaceState).toHaveBeenCalledWith({}, "", "/");
});

it("preserves history owned by the selected conversation", () => {
  storage.setItem(HISTORY_CONVERSATION_KEY, "cv-current");
  reconcileConversationHistory(browser, conversation("cv-current"), routes);
  expect(history.replaceState).not.toHaveBeenCalled();
});

it("preserves a new-tab deep link when no RouteDeck history entry exists", () => {
  history.state = null;
  reconcileConversationHistory(browser, conversation("cv-current"), routes);
  expect(history.replaceState).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Run the focused test and confirm it fails**

```powershell
pnpm --dir frontend exec vitest run --config vitest.config.ts src/tests/conversation-history.test.ts
```

- [ ] **Step 3: Implement the history owner contract**

Use a separate per-tab owner marker because RouteDeck's browser-history state has a strict schema:

```ts
export const HISTORY_CONVERSATION_KEY = "corpus.history-conversation.v1";

export function reconcileConversationHistory(
  browser: Pick<Window, "history" | "sessionStorage">,
  conversation: ConversationSummary,
  routes: RouteDeckRouteCodec,
): void {
  const owner = browser.sessionStorage.getItem(HISTORY_CONVERSATION_KEY);
  if (hasRouteDeckHistoryEntry(browser.history.state) && owner !== conversation.id) {
    browser.history.replaceState({}, "", routes.encode(conversation.current_node_id, {}));
  }
  browser.sessionStorage.setItem(HISTORY_CONVERSATION_KEY, conversation.id);
}

export function commitConversationHandoff(
  browser: Pick<Window, "history" | "sessionStorage">,
  conversation: ConversationSummary,
  routes: RouteDeckRouteCodec,
): void {
  browser.history.replaceState({}, "", routes.encode(conversation.current_node_id, {}));
  browser.sessionStorage.setItem(HISTORY_CONVERSATION_KEY, conversation.id);
  rememberConversation(browser.sessionStorage, conversation);
}
```

`hasRouteDeckHistoryEntry` must accept only `{routedeck: {version: 1, history_entry_id: positive safe integer}}`; it must not mutate or decode RouteDeck state.

- [ ] **Step 4: Reorder the lifecycle handoff**

In `ConversationLifecycle.mount`, create the codec, reconcile ownership, and only then expose the store to `RouteDeckBootstrapBoundary`. In `createNext`, remove the early `rememberConversation` call and invoke `commitConversationHandoff` synchronously after `loadRouteDeck` returns and before the next `await`.

The sequence must be:

```text
backend returns new ConversationView
  -> construct conversation-scoped transport and codec
  -> clear old RouteDeck history and bind history owner
  -> save selected public conversation
  -> load canonical chat history
  -> mount new boundary
  -> dispose previous runtime
```

- [ ] **Step 5: Prove refresh and deep-link behavior**

Run the focused test, `conversation-selection.test.ts`, `corpus-connection.test.ts`, and strict typecheck. Expected: all pass; same-owner history is untouched; stale-owner history is removed before bootstrap.

---

### Task 2: Replace the technical recovery screen with an internal Corpus coordinator

**Files:**
- Replace: `frontend/src/app/BootstrapRecoveryShell.tsx` with `frontend/src/app/CorpusRecoveryCoordinator.tsx`
- Modify: `frontend/src/main.tsx`
- Test: `frontend/src/tests/corpus-recovery-coordinator.test.tsx`

**Interfaces:**
- `CorpusRecoveryCoordinator` consumes the existing `RouteDeckBootstrapRecoveryState` supplied by `RouteDeckBootstrapBoundary`.
- It receives `replaceConversation(): Promise<void>` from `CorpusApplication` for missing, expired, or contract-mismatched conversations.
- It renders loading during automatic recovery and only `CorpusUnavailable` after an automatic attempt fails.

- [ ] **Step 1: Write failing policy tests**

Prove the exact mapping:

```ts
it.each([
  ["navigation", "abandon_navigation"],
  ["resync", "resync"],
])("recovers %s internally through %s", async (reason, actionKind) => {
  render(<CorpusRecoveryCoordinator state={recovery(reason, actionKind)} replaceConversation={replace} />);
  await waitFor(() => expect(action.run).toHaveBeenCalledTimes(1));
  expect(screen.queryByText(/RouteDeck|session|navigation|resync/i)).toBeNull();
});

it.each(["resume_expired", "resume_missing", "resume_contract_mismatch"])(
  "replaces an unavailable Corpus conversation for %s",
  async (reason) => {
    render(<CorpusRecoveryCoordinator state={recovery(reason)} replaceConversation={replace} />);
    await waitFor(() => expect(replace).toHaveBeenCalledTimes(1));
  },
);
```

Also prove that `invalid_state`, `disposed`, an absent legal action, and a failed automatic action render only:

```text
Corpus is temporarily unavailable.
Try again
```

- [ ] **Step 2: Run the focused test and confirm it fails**

```powershell
pnpm --dir frontend exec vitest run --config vitest.config.ts src/tests/corpus-recovery-coordinator.test.tsx
```

- [ ] **Step 3: Implement one-attempt internal recovery**

The coordinator must run at most one automatic action per recovery-state identity:

```ts
switch (state.reason) {
  case "navigation":
    return run("abandon_navigation");
  case "resync":
    return run("resync");
  case "resume_expired":
  case "resume_missing":
  case "resume_contract_mismatch":
    return replaceConversation();
  default:
    return failClosed();
}
```

Never render `state.error.message`. The retry button repeats the same Corpus-owned policy explicitly; it does not expose a menu of framework actions.

- [ ] **Step 4: Connect recovery to the existing lifecycle owner**

In `CorpusApplication`, extract one `replaceCurrentConversation()` callback used by both New conversation and recovery. Pass it into the recovery renderer:

```tsx
recovery={(state) => (
  <CorpusRecoveryCoordinator
    state={state}
    replaceConversation={replaceCurrentConversation}
  />
)}
```

Keep the current shell mounted while a recoverable background resync is already handled by RouteDeck; invoke this coordinator only for the boundary's action-required state.

- [ ] **Step 5: Run focused recovery and lifecycle tests**

Expected: navigation conflict automatically resolves to authoritative projection; expired/missing mapping uses Corpus replacement; no rendered text contains `RouteDeck`, `session recovery`, `resync`, or raw error codes.

---

### Task 3: Enforce the no-framework-error product invariant across the shell

**Files:**
- Modify: `frontend/src/app/BootstrapLoadingShell.tsx`
- Modify: `frontend/src/app/CorpusHeader.tsx`
- Modify: `frontend/src/app/CorpusMainHeading.tsx`
- Modify: `frontend/src/app/NavgraphSidebar.tsx`
- Modify: `frontend/src/features/lounge/PrivateFormGate.tsx`
- Modify: `frontend/src/tests/framework-bootstrap.test.tsx`
- Modify: `frontend/src/tests/navgraph-sidebar.test.tsx` if present; otherwise create `frontend/src/tests/corpus-framework-error-boundary.test.tsx`
- Modify: `architecture/components/corpus-routedeck-boundary.md`
- Modify: `SYSTEM_FLOW_INDEX.md`
- Modify: `test_index/README.md`

**Interfaces:**
- Framework state remains available internally and in explicitly developer-scoped diagnostics.
- Normal product surfaces receive Corpus-owned status and error copy only.

- [ ] **Step 1: Add a static user-copy regression test**

Render loading, bootstrap recovery, header status, main status, private-form failure, and normal Navgraph shell failure states. Assert that normal user-visible output does not match:

```ts
expect(renderedText).not.toMatch(
  /RouteDeck|resync|session[_ -](?:id|version|recovery)|navigation[_ -](?:conflict|request)|retained request/i,
);
```

Keep the Navgraph inspector's deliberate developer diagnostics separately scoped and labeled; do not allow its raw errors to replace the application shell.

- [ ] **Step 2: Replace framework-owned copy at Corpus surfaces**

Use these product terms:

```text
Loading Corpus…
Ready
Working…
Corpus is temporarily unavailable.
Try again
```

Remove `Loading the RouteDeck contract and session`, `Application session recovery`, raw status codes, raw `RouteDeckError` messages in normal shell placement, and recovery buttons such as `Abandon and resync`.

- [ ] **Step 3: Document the boundary**

Record this exact invariant in the boundary and flow documents:

```text
RouteDeck may report technical state and legal recovery actions to Corpus.
Corpus resolves state, navigation, link, and recovery mechanics internally.
Users never receive RouteDeck errors, identifiers, state codes, or recovery choices.
```

- [ ] **Step 4: Run the complete verification gate**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
pnpm --dir frontend test -- --reporter=dot
pnpm --dir frontend typecheck
pnpm --dir frontend build
```

Run Docker locally with the existing command:

```powershell
docker compose up --build -d backend frontend
```

Verify at `http://127.0.0.1:5199/`:

- refresh during and after New conversation;
- refresh the previously broken tab;
- open the same URL in a new tab;
- Back/Forward within one conversation;
- stale history from another conversation;
- active entry greeting during navigation reconciliation;
- missing/expired conversation replacement;
- desktop and 390×844 layouts;
- no visible RouteDeck/error/state/navigation terminology.

Confirm `http://127.0.0.1:8099/readyz` returns HTTP 200. Stage only the files changed by this plan and report unrelated unstaged/untracked files separately.

## Acceptance Criteria

- Refresh cannot pair one Corpus conversation with another conversation's RouteDeck history entry.
- A new tab preserves a valid deep link and starts without inherited stale history.
- State, navigation, link, session, and recovery mechanics are automatic and Corpus-owned.
- No normal user-facing surface contains RouteDeck errors, identifiers, state codes, or recovery choices.
- Same-conversation Back/Forward remains functional.
- Missing/expired conversations recover through Corpus mapping and provisioning contracts.
- RouteDeck, Design Studio, manifests, dependencies, migrations, and domain data remain unchanged.
