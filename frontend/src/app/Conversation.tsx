import { useEffect, useRef, type ReactNode } from "react";
import type {
  AgentConversationMessage,
  AgentStreamStatus,
} from "@routedeck/react";

import { AssistantMarkdown } from "./AssistantMarkdown";

export interface ConversationProps {
  messages: readonly AgentConversationMessage[];
  status: AgentStreamStatus;
  activeSurface: ReactNode;
  suggestedActions: ReactNode;
}

export function Conversation({
  messages,
  status,
  activeSurface,
  suggestedActions,
}: ConversationProps) {
  const activityAnchor = useRef<HTMLLIElement>(null);
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

  useEffect(() => {
    if (status === "streaming") {
      activityAnchor.current?.scrollIntoView?.({ block: "nearest" });
    }
  }, [messages.length, status]);

  return (
    <div aria-busy={status === "streaming"} data-agent-conversation="">
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
        <li ref={activityAnchor} aria-hidden="true" data-agent-activity-anchor="" />
        <li data-agent-experience="">
          <div data-agent-surface="">{activeSurface}</div>
        </li>
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
