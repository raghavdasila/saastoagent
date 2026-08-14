export type AuthorizedFetch = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

export interface AuthorizedTransport {
  fetch: AuthorizedFetch;
}

export interface ConversationTransport extends AuthorizedTransport {
  selectConversation(conversationId: string): void;
  clearConversation(): void;
}
