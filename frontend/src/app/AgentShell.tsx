import { useMemo } from "react";
import {
  createRouteDeckAgentClient,
  type AgentChatClient,
  type AgentHistoryTurn,
  type RouteDeckClientState,
} from "@routedeck/core";
import {
  RouteDeckSuggestedActions,
  RouteDeckSurfaceHost,
  useRouteDeckConversation,
  useRouteDeckConversationInputPolicy,
  useRouteDeckRuntime,
  useRouteDeckSelector,
  type RouteDeckSurfaceRegistry,
  type RouteDeckSurfaceSlot,
} from "@routedeck/react";

import { Composer } from "./Composer";
import { Conversation } from "./Conversation";

const CONVERSATION_SURFACE_SLOTS: readonly RouteDeckSurfaceSlot[] = Object.freeze([
  "active",
  "review",
]);
const EMPTY_LEGAL_OPERATIONS = Object.freeze([]);
const selectSessionVersion = (state: RouteDeckClientState) => state.sessionVersion;
const selectLegalOperations = (state: RouteDeckClientState) =>
  state.projection?.legal_operations ?? EMPTY_LEGAL_OPERATIONS;
const selectActiveChatRequestId = (state: RouteDeckClientState) => {
  const interaction = state.projection?.interaction;
  return interaction?.phase === "active" && interaction.owner === "chat"
    ? interaction.request_id
    : null;
};
export interface AgentShellProps {
  registry: RouteDeckSurfaceRegistry;
  client?: AgentChatClient;
  initialConversation?: readonly AgentHistoryTurn[];
}

export function AgentShell({
  registry,
  client,
  initialConversation = [],
}: AgentShellProps) {
  const runtime = useRouteDeckRuntime();
  const sessionVersion = useRouteDeckSelector(selectSessionVersion);
  const legalOperations = useRouteDeckSelector(selectLegalOperations);
  const activeRunRequestId = useRouteDeckSelector(selectActiveChatRequestId);
  const conversationInput = useRouteDeckConversationInputPolicy();
  const chatClient = useMemo(
    () => client ?? createRouteDeckAgentClient(),
    [client],
  );
  const agent = useRouteDeckConversation({
    client: chatClient,
    initialConversation,
    sessionVersion,
    createRequestId: runtime.createRequestId,
    synchronizeTo: runtime.store.synchronizeTo,
    resync: runtime.store.resync,
    activeRunRequestId,
  });
  const reviewIsCurrent =
    agent.review !== null &&
    legalOperations.some(
      (operation) =>
        operation.operation_id === agent.review?.operation_id &&
        operation.review_required,
    );
  const conversationInputDisabled = conversationInput?.enabled === false;
  const composerDisabled =
    agent.status === "streaming" ||
    conversationInputDisabled;
  const disabledReason = conversationInputDisabled
    ? conversationInput.disabled_message ?? undefined
    : undefined;

  return (
    <main data-agent-shell="">
      <Conversation
        messages={agent.messages}
        status={agent.status}
        suggestedActions={
          <RouteDeckSuggestedActions disabled={agent.status === "streaming"} />
        }
      />
      <div data-agent-surface-dock="">
        <div data-agent-surface="">
          <RouteDeckSurfaceHost
            registry={registry}
            slots={CONVERSATION_SURFACE_SLOTS}
          />
        </div>
      </div>
      {!reviewIsCurrent || agent.review === null ? null : (
        <section role="status" data-agent-review-required="">
          <h2>Approval required</h2>
          <p>{agent.review.operation_id} is waiting for explicit review.</p>
        </section>
      )}
      {agent.error === null ? null : (
        <p role="alert" data-agent-chat-error={agent.error.code}>
          {agent.error.message}
        </p>
      )}
      <div data-agent-input-dock="">
        <Composer
          disabled={composerDisabled}
          showCancel={agent.status === "streaming"}
          disabledReason={disabledReason}
          onSend={agent.send}
          onCancel={agent.cancel}
          {...(agent.pendingRequest === null
            ? {}
            : {
                onRetry: agent.retry,
                onDiscardPending: agent.discardPending,
              })}
        />
      </div>
    </main>
  );
}
