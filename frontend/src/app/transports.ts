import type {
  AuthorizedTransport,
  ConversationTransport,
} from "@/shared/transport/contracts";

export function createConversationTransport(
  authorized: AuthorizedTransport,
): ConversationTransport {
  let conversationId: string | null = null;
  return Object.freeze({
    selectConversation(nextConversationId: string) {
      if (!nextConversationId) {
        throw new Error("Conversation ID must be non-empty.");
      }
      conversationId = nextConversationId;
    },
    clearConversation() {
      conversationId = null;
    },
    fetch(input: RequestInfo | URL, init: RequestInit = {}) {
      const headers = new Headers(init.headers);
      if (conversationId !== null) {
        headers.set("X-Corpus-Conversation-ID", conversationId);
      }
      return authorized.fetch(input, { ...init, headers });
    },
  });
}
