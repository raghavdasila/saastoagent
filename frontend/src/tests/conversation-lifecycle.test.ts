import type {
  ConversationRunSnapshot,
  RouteDeckAgentClient,
} from "@routedeck/core";
import { expect, it, vi } from "vitest";

import { settleConversationRun } from "../app/conversationLifecycle";

it("waits for a new conversation run to reach a durable terminal state", async () => {
  const loadConversationRun = vi.fn(async () => run("generating", 3));
  const streamConversationRunEvents = vi.fn(async function* () {
    yield run("completed", 4);
  });
  const client = {
    loadConversationRun,
    streamConversationRunEvents,
  } as unknown as RouteDeckAgentClient;

  await settleConversationRun(client, "entry-turn");

  expect(loadConversationRun).toHaveBeenCalledWith("entry-turn");
  expect(streamConversationRunEvents).toHaveBeenCalledWith("entry-turn", 3);
});

it("fails when the new conversation arrival turn is interrupted", async () => {
  const client = {
    loadConversationRun: vi.fn(async () => ({
      ...run("interrupted", 4),
      failure: { code: "arrival_failed", message: "Arrival failed." },
    })),
  } as unknown as RouteDeckAgentClient;

  await expect(settleConversationRun(client, "entry-turn"))
    .rejects.toThrow("Arrival failed.");
});

function run(
  stage: ConversationRunSnapshot["stage"],
  cursor: number,
): ConversationRunSnapshot {
  return {
    request_id: "entry-turn",
    kind: "assistant_initiated",
    stage,
    cursor,
    assistant_content: "",
    user_message: null,
    user_turn_id: null,
    session_version: stage === "completed" ? 3 : null,
    projection_version: stage === "completed" ? 3 : null,
    turn_id: stage === "completed" ? "assistant-turn" : null,
    failure: null,
    review: null,
  };
}
