import { useCallback, useLayoutEffect, useRef, type ReactNode } from "react";
import type {
  AgentConversationMessage,
  AgentStreamStatus,
} from "@routedeck/react";

import { AssistantMarkdown } from "./AssistantMarkdown";

export interface ConversationProps {
  messages: readonly AgentConversationMessage[];
  status: AgentStreamStatus;
  suggestedActions: ReactNode;
  scrollState?: ConversationScrollState;
}

export interface ConversationScrollState {
  pinnedToBottom: boolean;
  scrollTop: number;
}

const BOTTOM_PROXIMITY_PX = 80;

export function Conversation({
  messages,
  status,
  suggestedActions,
  scrollState: suppliedScrollState,
}: ConversationProps) {
  const conversationRef = useRef<HTMLDivElement>(null);
  const localScrollState = useRef<ConversationScrollState>({
    pinnedToBottom: true,
    scrollTop: 0,
  });
  const scrollState = suppliedScrollState ?? localScrollState.current;
  const previousStatusRef = useRef(status);
  const previousLastMessageIdRef = useRef(messages.at(-1)?.id ?? null);
  const hasStreamingAssistant = messages.some(
    (message) =>
      message.role === "assistant" && message.status === "streaming",
  );
  const isThinking = status === "streaming" && !hasStreamingAssistant;
  const lastAssistantIndex = messages.reduce(
    (latest, message, index) =>
      message.role === "assistant" ? index : latest,
    -1,
  );

  const updateBottomPin = useCallback(() => {
    const conversation = conversationRef.current;
    if (conversation === null) return;
    const distanceFromBottom =
      conversation.scrollHeight - conversation.scrollTop - conversation.clientHeight;
    scrollState.scrollTop = conversation.scrollTop;
    scrollState.pinnedToBottom = distanceFromBottom <= BOTTOM_PROXIMITY_PX;
  }, [scrollState]);

  useLayoutEffect(() => {
    const conversation = conversationRef.current;
    if (conversation === null) return;
    const lastMessage = messages.at(-1);
    const startedStreaming =
      status === "streaming" && previousStatusRef.current !== "streaming";
    const userMessageWasAppended =
      lastMessage?.role === "user" &&
      lastMessage.id !== previousLastMessageIdRef.current;
    if (startedStreaming || userMessageWasAppended) {
      scrollState.pinnedToBottom = true;
    }
    const maximumScrollTop = Math.max(
      0,
      conversation.scrollHeight - conversation.clientHeight,
    );
    if (scrollState.pinnedToBottom) {
      conversation.scrollTop = Math.max(
        0,
        conversation.scrollHeight - conversation.clientHeight,
      );
    } else {
      conversation.scrollTop = Math.min(scrollState.scrollTop, maximumScrollTop);
    }
    scrollState.scrollTop = conversation.scrollTop;
    previousStatusRef.current = status;
    previousLastMessageIdRef.current = lastMessage?.id ?? null;
  }, [messages, scrollState, status]);

  return (
    <div
      ref={conversationRef}
      aria-busy={status === "streaming"}
      data-agent-conversation=""
      onScroll={updateBottomPin}
    >
      <ol aria-live="polite" aria-relevant="additions text">
        {messages.map((message, index) => (
          <li key={message.id} data-agent-turn="">
            <div
              data-agent-message={message.role}
              data-agent-message-status={message.status}
            >
              <article>
                <header>{message.role === "user" ? "You" : "Assistant"}</header>
                {message.role === "user" ? (
                  <p>{message.content}</p>
                ) : (
                  <AssistantMarkdown>{message.content}</AssistantMarkdown>
                )}
                {message.status === "streaming" ? (
                  <ThinkingDots label="Assistant is responding" />
                ) : null}
              </article>
            </div>
            {index === lastAssistantIndex ? (
              <div data-agent-quick-actions="">{suggestedActions}</div>
            ) : null}
          </li>
        ))}
        {isThinking ? (
          <li data-agent-message="assistant" data-agent-message-status="thinking">
            <article>
              <header>Assistant</header>
              <ThinkingDots label="Assistant is thinking" />
            </article>
          </li>
        ) : null}
        <li aria-hidden="true" data-agent-activity-anchor="" />
      </ol>
    </div>
  );
}

function ThinkingDots({ label }: { label: string }) {
  return (
    <span role="status" aria-label={label} data-agent-thinking="">
      <span aria-hidden="true" />
      <span aria-hidden="true" />
      <span aria-hidden="true" />
    </span>
  );
}
