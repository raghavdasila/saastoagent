import { expect, it, vi } from "vitest";

import {
  HISTORY_CONVERSATION_KEY,
  commitConversationHandoff,
  historyNeedsReconciliation,
  reconcileConversationHistory,
} from "../app/conversationHistory";
import { SELECTED_CONVERSATION_KEY, type ConversationSummary } from "../app/conversations";

it("discards RouteDeck history owned by another conversation", () => {
  const browser = memoryBrowser({ routedeck: { version: 1, history_entry_id: 7 } });
  browser.sessionStorage.setItem(HISTORY_CONVERSATION_KEY, "cv-old");
  expect(historyNeedsReconciliation(browser, "cv-new")).toBe(true);
  reconcileConversationHistory(browser, "cv-new", "/");
  expect(browser.history.replaceState).toHaveBeenCalledWith({}, "", "/");
  expect(browser.sessionStorage.getItem(HISTORY_CONVERSATION_KEY)).toBe("cv-new");
});

it("preserves history owned by the selected conversation", () => {
  const state = { routedeck: { version: 1, history_entry_id: 7 } };
  const browser = memoryBrowser(state);
  browser.sessionStorage.setItem(HISTORY_CONVERSATION_KEY, "cv-current");
  reconcileConversationHistory(browser, "cv-current", "/ignored");
  expect(browser.history.replaceState).not.toHaveBeenCalled();
});

it("preserves a new-tab deep link without a RouteDeck history entry", () => {
  const browser = memoryBrowser(null);
  reconcileConversationHistory(browser, "cv-current", "/ignored");
  expect(browser.history.replaceState).not.toHaveBeenCalled();
  expect(browser.sessionStorage.getItem(HISTORY_CONVERSATION_KEY)).toBe("cv-current");
});

it("commits history ownership before selecting the replacement", () => {
  const browser = memoryBrowser({ routedeck: { version: 1, history_entry_id: 7 } });
  commitConversationHandoff(browser, conversation("cv-new"), "/");
  expect(browser.history.replaceState).toHaveBeenCalledWith({}, "", "/");
  expect(browser.sessionStorage.getItem(HISTORY_CONVERSATION_KEY)).toBe("cv-new");
  expect(browser.sessionStorage.getItem(SELECTED_CONVERSATION_KEY)).toBe("cv-new");
});

function memoryBrowser(state: unknown) {
  const values = new Map<string, string>();
  return {
    history: {
      state,
      replaceState: vi.fn(),
    },
    sessionStorage: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => { values.set(key, value); },
      removeItem: (key: string) => { values.delete(key); },
    },
  };
}

function conversation(id: string): ConversationSummary {
  return {
    id,
    current_node_id: "lounge.home",
    session_version: 1,
    updated_at: "2026-08-03T00:00:00Z",
    active_run: null,
  };
}
