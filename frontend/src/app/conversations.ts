export const SELECTED_CONVERSATION_KEY = "corpus.selected-conversation.v1";

export type ConversationRunStage =
  | "starting"
  | "awaiting_model"
  | "generating"
  | "completed"
  | "interrupted";

export interface ActiveConversationRun {
  request_id: string;
  status: "running" | "completed" | "interrupted";
  stage: ConversationRunStage;
  cursor: number;
}

export interface ConversationSummary {
  id: string;
  current_node_id: string;
  session_version: number;
  updated_at: string;
  active_run: ActiveConversationRun | null;
}

export interface ConversationStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export function selectConversation(
  storage: ConversationStorage,
  conversations: readonly ConversationSummary[],
): ConversationSummary | null {
  if (conversations.length === 0) {
    storage.removeItem(SELECTED_CONVERSATION_KEY);
    return null;
  }
  const stored = storage.getItem(SELECTED_CONVERSATION_KEY);
  const selected = conversations.find((conversation) => conversation.id === stored)
    ?? [...conversations].sort((left, right) =>
      right.updated_at.localeCompare(left.updated_at),
    )[0];
  storage.setItem(SELECTED_CONVERSATION_KEY, selected.id);
  return selected;
}

export function createConversationClient(fetcher: typeof fetch) {
  const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
    const response = await fetcher(path, init);
    if (!response.ok) throw await conversationProblem(response);
    return await response.json() as T;
  };
  return Object.freeze({
    async list(): Promise<readonly ConversationSummary[]> {
      const result = await request<{ conversations: ConversationSummary[] }>(
        "/api/conversations",
      );
      return Object.freeze(
        result.conversations.map((conversation) => Object.freeze(conversation)),
      );
    },
    create(): Promise<ConversationSummary> {
      return request<ConversationSummary>("/api/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
    },
    load(id: string): Promise<ConversationSummary> {
      return request<ConversationSummary>(
        `/api/conversations/${encodeURIComponent(id)}`,
      );
    },
  });
}

async function conversationProblem(response: Response): Promise<Error> {
  const body = await response.json().catch(() => null) as
    | { code?: string; message?: string }
    | null;
  return new Error(
    body?.message ?? `Conversation request failed with HTTP ${response.status}.`,
  );
}
