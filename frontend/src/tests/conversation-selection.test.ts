import { describe, expect, it, vi } from "vitest";

import {
  SELECTED_CONVERSATION_KEY,
  createConversationClient,
  selectConversation,
  type ConversationSummary,
} from "../app/conversations";

function conversation(id: string, updatedAt: string): ConversationSummary {
  return {
    id,
    current_node_id: "lounge.home",
    session_version: 1,
    updated_at: updatedAt,
    active_run: null,
  };
}

describe("conversation selection", () => {
  it("retains an authorized per-tab selection", () => {
    const storage = memoryStorage("cv-old");
    const selected = selectConversation(storage, [
      conversation("cv-new", "2026-07-30T11:00:00Z"),
      conversation("cv-old", "2026-07-30T10:00:00Z"),
    ]);
    expect(selected?.id).toBe("cv-old");
  });

  it("uses the explicit anonymous replacement endpoint", async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify(
      conversation("cv-new", "2026-07-30T11:00:00Z"),
    ), { status: 201, headers: { "Content-Type": "application/json" } }));
    const replaced = await createConversationClient(fetcher).replaceAnonymous("cv-old");
    expect(replaced.id).toBe("cv-new");
    expect(fetcher).toHaveBeenCalledWith(
      "/api/conversations/cv-old/replacement",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("replaces a stale selection with the most recently updated conversation", () => {
    const storage = memoryStorage("cv-foreign");
    const selected = selectConversation(storage, [
      conversation("cv-old", "2026-07-30T10:00:00Z"),
      conversation("cv-new", "2026-07-30T11:00:00Z"),
    ]);
    expect(selected?.id).toBe("cv-new");
    expect(storage.getItem(SELECTED_CONVERSATION_KEY)).toBe("cv-new");
  });

  it("clears selection when the authorized catalog is empty", () => {
    const storage = memoryStorage("cv-old");
    expect(selectConversation(storage, [])).toBeNull();
    expect(storage.getItem(SELECTED_CONVERSATION_KEY)).toBeNull();
  });
});

function memoryStorage(initial: string | null) {
  let value = initial;
  return {
    getItem(key: string) {
      return key === SELECTED_CONVERSATION_KEY ? value : null;
    },
    setItem(key: string, next: string) {
      if (key === SELECTED_CONVERSATION_KEY) value = next;
    },
    removeItem(key: string) {
      if (key === SELECTED_CONVERSATION_KEY) value = null;
    },
  };
}
