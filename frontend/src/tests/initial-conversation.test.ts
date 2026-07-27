import type { AgentHistoryTurn, RouteDeckAgentClient } from "@routedeck/core";
import { expect, it, vi } from "vitest";

import {
  loadInitialConversation,
  shouldStartEntryGreeting,
} from "../app/initialConversation";


it("reuses the durable conversation without starting another greeting", async () => {
  const existing: AgentHistoryTurn[] = [
    {
      turn_id: "assistant-existing",
      request_id: "entry-existing",
      role: "assistant",
      content: "Welcome back.",
    },
  ];
  const streamAssistantTurn = vi.fn(async function* () {});
  const client = {
    loadConversation: vi.fn(async () => existing),
    streamAssistantTurn,
    async *stream() {},
  } satisfies RouteDeckAgentClient;

  const result = await loadInitialConversation(
    {
      store: {
        getState: vi.fn(),
        subscribe: vi.fn(),
        resync: vi.fn(),
        synchronizeTo: vi.fn(),
      },
    },
    client,
    "test.entry-greeting.v1",
  );

  expect(result).toBe(existing);
  expect(streamAssistantTurn).not.toHaveBeenCalled();
});


it("does not start an entry greeting on credential surfaces", async () => {
  const streamAssistantTurn = vi.fn(async function* () {});
  const client = {
    loadConversation: vi.fn(async () => []),
    streamAssistantTurn,
    async *stream() {},
  } satisfies RouteDeckAgentClient;

  const result = await loadInitialConversation(
    {
      store: {
        getState: vi.fn(),
        subscribe: vi.fn(),
        resync: vi.fn(),
        synchronizeTo: vi.fn(),
      },
    },
    client,
    "test.entry-greeting.v1",
    { startGreeting: false },
  );

  expect(result).toEqual([]);
  expect(streamAssistantTurn).not.toHaveBeenCalled();
  expect(shouldStartEntryGreeting("workspace.verify_email")).toBe(false);
  expect(shouldStartEntryGreeting("workspace.reset_password")).toBe(false);
  expect(shouldStartEntryGreeting("workspace.lounge")).toBe(true);
});
