import {
  AgentChatError,
  runAssistantInitiatedTurn,
  type AssistantInitiatedTurnProgress,
  type AgentHistoryTurn,
  type RouteDeckAgentClient,
  type RouteDeckStore,
} from "@routedeck/core";

export interface InitialConversationRouteDeck {
  store: Pick<
    RouteDeckStore,
    "getState" | "subscribe" | "resync" | "synchronizeTo"
  >;
}

export async function loadInitialConversation(
  routeDeck: InitialConversationRouteDeck,
  chatClient: RouteDeckAgentClient,
  requestId: string,
  options: {
    startGreeting?: boolean;
    onProgress?(progress: AssistantInitiatedTurnProgress): void;
  } = {},
): Promise<readonly AgentHistoryTurn[]> {
  const existing = await chatClient.loadConversation();
  if (existing.length > 0) return existing;
  if (options.startGreeting === false) return existing;
  try {
    return await runAssistantInitiatedTurn(routeDeck.store, chatClient, {
      requestId,
      onProgress: options.onProgress,
    });
  } catch (error) {
    throw greetingError(error);
  }
}

export function shouldStartEntryGreeting(nodeId: string | null): boolean {
  return nodeId === "workspace.lounge";
}

export function createGreetingRetryRequestId(requestIdPrefix: string): string {
  const identifier = globalThis.crypto.randomUUID();
  if (!identifier) {
    throw new AgentChatError(
      "entry_request_id_unavailable",
      "The browser could not create an entry greeting retry ID.",
    );
  }
  return `${requestIdPrefix}.retry.${identifier}`;
}

function greetingError(error: unknown): unknown {
  if (!(error instanceof AgentChatError)) return error;
  const message = GREETING_ERRORS[error.code];
  if (message === undefined) return error;
  return new AgentChatError(error.code, message, error.status, error.outcome);
}

const GREETING_ERRORS: Readonly<Record<string, string>> = Object.freeze({
  routedeck_session_unavailable:
    "The RouteDeck session is unavailable for the entry greeting.",
  assistant_turn_projection_unavailable:
    "The completed entry greeting did not publish a projection version.",
  assistant_turn_interrupted:
    "The entry greeting was interrupted. Retry it explicitly to continue.",
  assistant_turn_not_committed:
    "The entry greeting completed without a durable conversation turn.",
  assistant_turn_convergence_failed:
    "RouteDeck could not observe the active entry greeting.",
  assistant_turn_convergence_lost:
    "The active entry greeting ended without its terminal event.",
  assistant_turn_convergence_timeout:
    "The active entry greeting did not finish in time.",
  assistant_turn_convergence_unavailable:
    "No active entry greeting is available to restore.",
});
