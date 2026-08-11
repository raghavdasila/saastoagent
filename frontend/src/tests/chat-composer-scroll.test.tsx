import { act, fireEvent, render, screen } from "@testing-library/react";
import type { AgentConversationMessage } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { Composer } from "../app/Composer";
import { Conversation } from "../app/Conversation";
import type { ConversationScrollState } from "../app/Conversation";

it("marks only a genuinely empty conversation so mobile surfaces can reclaim the unused chat space", () => {
  const view = render(
    <Conversation messages={[]} status="idle" suggestedActions={null} />,
  );
  const conversation = document.querySelector<HTMLElement>("[data-agent-conversation]");
  expect(conversation).toHaveAttribute("data-agent-conversation-empty");

  view.rerender(
    <Conversation messages={[]} status="streaming" suggestedActions={null} />,
  );
  expect(conversation).not.toHaveAttribute("data-agent-conversation-empty");

  view.rerender(
    <Conversation
      messages={[{
        id: "user-empty-marker",
        requestId: "request-empty-marker",
        role: "user",
        content: "Continue with the current build.",
        status: "finalized",
      }]}
      status="idle"
      suggestedActions={null}
    />,
  );
  expect(conversation).not.toHaveAttribute("data-agent-conversation-empty");
});

it("returns keyboard focus to the composer when an Enter send becomes available again", async () => {
  let finishSend!: () => void;
  const send = vi.fn(
    () => new Promise<void>((resolve) => {
      finishSend = resolve;
    }),
  );
  const props = {
    showCancel: false,
    onSend: send,
    onCancel: vi.fn(),
  };
  const view = render(<Composer {...props} disabled={false} />);
  const textbox = screen.getByRole("textbox", { name: "Message the assistant" });

  textbox.focus();
  fireEvent.change(textbox, { target: { value: "Show my Sources" } });
  fireEvent.keyDown(textbox, { key: "Enter" });

  expect(send).toHaveBeenCalledWith("Show my Sources");
  textbox.blur();
  expect(textbox).not.toHaveFocus();
  view.rerender(<Composer {...props} disabled />);

  view.rerender(<Composer {...props} disabled={false} />);
  expect(textbox).toHaveFocus();

  await act(async () => finishSend());
});

it("keeps Shift+Enter available for a multiline draft without sending", () => {
  const send = vi.fn(async () => undefined);
  render(
    <Composer
      disabled={false}
      showCancel={false}
      onSend={send}
      onCancel={vi.fn()}
    />,
  );
  const textbox = screen.getByRole("textbox", { name: "Message the assistant" });

  textbox.focus();
  fireEvent.change(textbox, { target: { value: "First line\nSecond line" } });
  const notCancelled = fireEvent.keyDown(textbox, { key: "Enter", shiftKey: true });

  expect(notCancelled).toBe(true);
  expect(send).not.toHaveBeenCalled();
  expect(textbox).toHaveValue("First line\nSecond line");
  expect(textbox).toHaveFocus();
});

it("pins streaming content only while the reader remains near the bottom", () => {
  const firstMessages: AgentConversationMessage[] = [
    {
      id: "user-1",
      requestId: "request-1",
      role: "user",
      content: "Explain this Source.",
      status: "finalized",
    },
  ];
  const view = render(
    <Conversation messages={firstMessages} status="idle" suggestedActions={null} />,
  );
  const conversation = document.querySelector<HTMLElement>("[data-agent-conversation]");
  if (conversation === null) throw new Error("Expected the conversation to render.");
  Object.defineProperties(conversation, {
    clientHeight: { configurable: true, value: 400 },
    scrollHeight: { configurable: true, value: 1_000 },
  });

  view.rerender(
    <Conversation
      messages={[
        ...firstMessages,
        {
          id: "assistant-1",
          requestId: "request-1",
          role: "assistant",
          content: "First chunk",
          status: "streaming",
        },
      ]}
      status="streaming"
      suggestedActions={null}
    />,
  );
  expect(conversation.scrollTop).toBe(600);

  conversation.scrollTop = 180;
  fireEvent.scroll(conversation);
  Object.defineProperty(conversation, "scrollHeight", { configurable: true, value: 1_200 });
  view.rerender(
    <Conversation
      messages={[
        ...firstMessages,
        {
          id: "assistant-1",
          requestId: "request-1",
          role: "assistant",
          content: "First chunk and second chunk",
          status: "streaming",
        },
      ]}
      status="streaming"
      suggestedActions={null}
    />,
  );
  expect(conversation.scrollTop).toBe(180);

  conversation.scrollTop = 800;
  fireEvent.scroll(conversation);
  Object.defineProperty(conversation, "scrollHeight", { configurable: true, value: 1_400 });
  view.rerender(
    <Conversation
      messages={[
        ...firstMessages,
        {
          id: "assistant-1",
          requestId: "request-1",
          role: "assistant",
          content: "First, second, and final chunk",
          status: "streaming",
        },
      ]}
      status="streaming"
      suggestedActions={null}
    />,
  );
  expect(conversation.scrollTop).toBe(1_000);
});

it("preserves a deliberate scroll-up across authoritative conversation remounts", () => {
  const clientHeight = vi
    .spyOn(HTMLElement.prototype, "clientHeight", "get")
    .mockReturnValue(400);
  const scrollHeight = vi
    .spyOn(HTMLElement.prototype, "scrollHeight", "get")
    .mockReturnValue(1_400);
  const scrollState: ConversationScrollState = {
    pinnedToBottom: false,
    scrollTop: 240,
  };
  const messages: AgentConversationMessage[] = [{
    id: "assistant-remount",
    requestId: "request-remount",
    role: "assistant",
    content: "A completed streamed response.",
    status: "finalized",
  }];
  const view = render(
    <Conversation
      key="streaming-view"
      messages={messages}
      status="streaming"
      suggestedActions={null}
      scrollState={scrollState}
    />,
  );

  view.rerender(
    <Conversation
      key="authoritative-view"
      messages={messages}
      status="idle"
      suggestedActions={null}
      scrollState={scrollState}
    />,
  );

  expect(document.querySelector<HTMLElement>("[data-agent-conversation]")?.scrollTop).toBe(240);
  expect(scrollState).toEqual({ pinnedToBottom: false, scrollTop: 240 });
  clientHeight.mockRestore();
  scrollHeight.mockRestore();
});
