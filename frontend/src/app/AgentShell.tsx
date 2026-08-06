import { useEffect, useMemo, useRef } from "react";
import {
  createRouteDeckAgentClient,
  type AgentChatClient,
  type AgentHistoryTurn,
  type RouteDeckClientState,
} from "@routedeck/core";
import {
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
import { CorpusSuggestedActions } from "./CorpusSuggestedActions";

const CONVERSATION_SURFACE_SLOTS: readonly RouteDeckSurfaceSlot[] = Object.freeze([
  "active",
  "review",
]);
const EMPTY_LEGAL_OPERATIONS = Object.freeze([]);
const selectSessionVersion = (state: RouteDeckClientState) => state.sessionVersion;
const selectCurrentNodeId = (state: RouteDeckClientState) =>
  state.projection?.current.node_id ?? null;
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
  const currentNodeId = useRouteDeckSelector(selectCurrentNodeId);
  const legalOperations = useRouteDeckSelector(selectLegalOperations);
  const activeRunRequestId = useRouteDeckSelector(selectActiveChatRequestId);
  const conversationInput = useRouteDeckConversationInputPolicy();
  const surfaceDockRef = useRef<HTMLDivElement>(null);
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

  useEffect(() => {
    if (surfaceDockRef.current !== null) {
      surfaceDockRef.current.scrollTop = 0;
    }
  }, [currentNodeId]);

  return (
    <main data-agent-shell="">
      <Conversation
        messages={agent.messages}
        status={agent.status}
        suggestedActions={
          <CorpusSuggestedActions disabled={agent.status === "streaming"} />
        }
      />
      <div ref={surfaceDockRef} data-agent-surface-dock="">
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
          Corpus could not complete that request. Try again.
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
