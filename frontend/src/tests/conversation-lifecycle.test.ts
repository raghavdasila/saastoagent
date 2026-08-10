import type {
  ConversationRunSnapshot,
  RouteDeckAgentClient,
} from "@routedeck/core";
import { decodeFrontendContract } from "@routedeck/core";
import { afterEach, expect, it, vi } from "vitest";

import {
  ConversationLifecycle,
  settleConversationRun,
} from "../app/conversationLifecycle";
import { HISTORY_CONVERSATION_KEY } from "../app/conversationHistory";
import { SELECTED_CONVERSATION_KEY } from "../app/conversations";
import compiledContract from "../routedeck/corpus-frontend-contract.generated.json";
import {
  TestRouteDeckClient,
  frameworkProjectionFixture,
} from "./routeDeckHarness";

const clients = vi.hoisted(() => ({
  routeDeck: null as unknown,
  loadConversation: vi.fn(async () => []),
  chat: {
    async loadConversation() { return clients.loadConversation(); },
    async *stream() {},
    async startAssistantRun() { throw new Error("not used"); },
    async loadConversationRun() { throw new Error("not used"); },
    async *streamConversationRunEvents() {},
  },
}));

vi.mock("@routedeck/core", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@routedeck/core")>();
  return {
    ...actual,
    createRouteDeckClient: vi.fn(() => clients.routeDeck),
    createRouteDeckAgentClient: vi.fn(() => clients.chat),
  };
});

afterEach(() => {
  clients.loadConversation.mockReset();
  clients.loadConversation.mockResolvedValue([]);
  window.history.replaceState({}, "", "/");
  window.sessionStorage.clear();
});

it("commits a new authenticated conversation from its exact session-bound Workspace projection", async () => {
  const resumeHandle = "resume-workspace-exact";
  const location = { node_id: "workspace.home", route_params: [] };
  const projection = {
    ...frameworkProjectionFixture(),
    current: location,
    diagnostics: {
      ...frameworkProjectionFixture().diagnostics,
      current_node_id: "workspace.home",
    },
    navigation: {
      ...frameworkProjectionFixture().navigation,
      current: location,
      route_template: "/home",
      resume_handle: resumeHandle,
    },
  };
  clients.routeDeck = new TestRouteDeckClient(
    projection,
    decodeFrontendContract(compiledContract),
  );
  window.history.replaceState({}, "", "/");
  window.sessionStorage.setItem(SELECTED_CONVERSATION_KEY, "conversation-old");
  const next = {
    id: "conversation-workspace",
    current_node_id: "workspace.home",
    session_version: 1,
    updated_at: "2026-08-07T15:22:41Z",
    active_run: null,
  } as const;
  const conversationMounted = vi.fn();
  const lifecycle = new ConversationLifecycle(
    window,
    { fetch: vi.fn() },
    {
      create: vi.fn(async () => next),
      replaceAnonymous: vi.fn(async () => {
        throw new Error("not used");
      }),
    },
    conversationMounted,
  );

  const mounted = await lifecycle.createNext(
    { ...next, id: "conversation-old" },
    false,
  );

  expect(window.sessionStorage.getItem(SELECTED_CONVERSATION_KEY))
    .toBe(next.id);
  expect(window.location.pathname).toBe("/home");
  expect(new URLSearchParams(window.location.search).get("resume_handle"))
    .toBe(resumeHandle);
  await mounted.routeDeck.store.bootstrap();
  expect(mounted.routeDeck.store.getState().projection?.current.node_id)
    .toBe("workspace.home");
  expect(() => mounted.routeDeck.routes.encode(
    "workspace.home",
    {},
    { resumeHandle: "resume-workspace-mismatched" },
  )).toThrow(/resume capability is unavailable or mismatched/i);
  expect(conversationMounted).toHaveBeenCalledOnce();
  expect(conversationMounted).toHaveBeenCalledWith(next.id);
  lifecycle.dispose(mounted);
});

it("keeps an anonymous replacement on the shareable Lounge route", async () => {
  const location = { node_id: "lounge.home", route_params: [] };
  const projection = {
    ...frameworkProjectionFixture(),
    current: location,
    diagnostics: {
      ...frameworkProjectionFixture().diagnostics,
      current_node_id: "lounge.home",
    },
    navigation: {
      ...frameworkProjectionFixture().navigation,
      current: location,
      route_template: "/",
      resume_handle: null,
    },
  };
  clients.routeDeck = new TestRouteDeckClient(
    projection,
    decodeFrontendContract(compiledContract),
  );
  const current = {
    id: "conversation-anonymous-old",
    current_node_id: "lounge.home",
    session_version: 1,
    updated_at: "2026-08-07T15:22:40Z",
    active_run: null,
  } as const;
  const next = {
    ...current,
    id: "conversation-anonymous-next",
    updated_at: "2026-08-07T15:22:41Z",
  } as const;
  window.sessionStorage.setItem(SELECTED_CONVERSATION_KEY, current.id);
  const lifecycle = new ConversationLifecycle(
    window,
    { fetch: vi.fn() },
    {
      create: vi.fn(async () => {
        throw new Error("not used");
      }),
      replaceAnonymous: vi.fn(async () => next),
    },
  );

  const mounted = await lifecycle.createNext(current, true);

  expect(window.sessionStorage.getItem(SELECTED_CONVERSATION_KEY)).toBe(next.id);
  expect(window.location.pathname).toBe("/");
  expect(window.location.search).toBe("");
  await mounted.routeDeck.store.bootstrap();
  expect(mounted.routeDeck.store.getState().projection?.current.node_id)
    .toBe("lounge.home");
  lifecycle.dispose(mounted);
});

it("keeps the current conversation selected when new chat history cannot load", async () => {
  const resumeHandle = "resume-workspace-failed-history";
  const location = { node_id: "workspace.home", route_params: [] };
  clients.routeDeck = new TestRouteDeckClient(
    {
      ...frameworkProjectionFixture(),
      current: location,
      diagnostics: {
        ...frameworkProjectionFixture().diagnostics,
        current_node_id: "workspace.home",
      },
      navigation: {
        ...frameworkProjectionFixture().navigation,
        current: location,
        route_template: "/home",
        resume_handle: resumeHandle,
      },
    },
    decodeFrontendContract(compiledContract),
  );
  clients.loadConversation.mockRejectedValueOnce(
    new Error("Conversation history unavailable."),
  );
  window.history.replaceState({}, "", "/");
  window.sessionStorage.setItem(SELECTED_CONVERSATION_KEY, "conversation-old");
  window.sessionStorage.setItem(HISTORY_CONVERSATION_KEY, "conversation-old");
  const next = {
    id: "conversation-new",
    current_node_id: "workspace.home",
    session_version: 1,
    updated_at: "2026-08-07T15:22:42Z",
    active_run: null,
  } as const;
  const conversationMounted = vi.fn();
  const lifecycle = new ConversationLifecycle(
    window,
    { fetch: vi.fn() },
    {
      create: vi.fn(async () => next),
      replaceAnonymous: vi.fn(async () => {
        throw new Error("not used");
      }),
    },
    conversationMounted,
  );

  await expect(lifecycle.createNext(
    { ...next, id: "conversation-old" },
    false,
  )).rejects.toThrow("Conversation history unavailable.");

  expect(window.location.pathname).toBe("/");
  expect(window.location.search).toBe("");
  expect(window.sessionStorage.getItem(SELECTED_CONVERSATION_KEY))
    .toBe("conversation-old");
  expect(window.sessionStorage.getItem(HISTORY_CONVERSATION_KEY))
    .toBe("conversation-old");
  expect(conversationMounted).not.toHaveBeenCalled();
});

it("keeps the Source conversation binding when handoff history cannot commit", async () => {
  const location = { node_id: "workspace.home", route_params: [] };
  clients.routeDeck = new TestRouteDeckClient(
    {
      ...frameworkProjectionFixture(),
      current: location,
      diagnostics: {
        ...frameworkProjectionFixture().diagnostics,
        current_node_id: "workspace.home",
      },
      navigation: {
        ...frameworkProjectionFixture().navigation,
        current: location,
        route_template: "/home",
        resume_handle: "resume-failed-history-commit",
      },
    },
    decodeFrontendContract(compiledContract),
  );
  window.sessionStorage.setItem(SELECTED_CONVERSATION_KEY, "conversation-old");
  const next = {
    id: "conversation-uncommitted",
    current_node_id: "workspace.home",
    session_version: 1,
    updated_at: "2026-08-07T15:22:43Z",
    active_run: null,
  } as const;
  const conversationMounted = vi.fn();
  const replaceState = vi.spyOn(window.history, "replaceState")
    .mockImplementationOnce(() => {
      throw new Error("History commit unavailable.");
    });
  const lifecycle = new ConversationLifecycle(
    window,
    { fetch: vi.fn() },
    {
      create: vi.fn(async () => next),
      replaceAnonymous: vi.fn(async () => {
        throw new Error("not used");
      }),
    },
    conversationMounted,
  );

  try {
    await expect(lifecycle.createNext(
      { ...next, id: "conversation-old" },
      false,
    )).rejects.toThrow("History commit unavailable.");
    expect(conversationMounted).not.toHaveBeenCalled();
    expect(window.sessionStorage.getItem(SELECTED_CONVERSATION_KEY))
      .toBe("conversation-old");
  } finally {
    replaceState.mockRestore();
  }
});

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
