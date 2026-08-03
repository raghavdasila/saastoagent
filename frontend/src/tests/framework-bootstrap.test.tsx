import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { AgentChatClient } from "@routedeck/core";
import {
  defineRouteDeckSurfaceRegistry,
  type RouteDeckBootstrapActionRequiredState,
} from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { ApplicationShell } from "../app/ApplicationShell";
import { BootstrapLoadingShell } from "../app/BootstrapLoadingShell";
import { CorpusRecoveryCoordinator } from "../app/CorpusRecoveryCoordinator";
import { loadRouteDeck } from "../app/loadRouteDeck";
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  TestRouteDeckClient,
} from "./routeDeckHarness";

const idleChatClient: AgentChatClient = Object.freeze({
  async *stream() {},
  async loadConversation() { return []; },
  async startAssistantRun() { throw new Error("not used"); },
  async loadConversationRun() { throw new Error("not used"); },
  async *streamConversationRunEvents() {},
});
const registry = defineRouteDeckSurfaceRegistry({
  "test.active": () => <section>Loaded feature surface</section>,
  "test.detail": () => <section>Loaded detail surface</section>,
});

it("loads the server contract into the product-neutral RouteDeck host", async () => {
  const contract = frameworkContractFixture();
  const client = new TestRouteDeckClient(frameworkProjectionFixture(), contract);
  const routeDeck = await loadRouteDeck(window, client);
  await routeDeck.store.bootstrap();

  render(
    <ApplicationShell
      routeDeck={routeDeck}
      registry={registry}
      chatClient={idleChatClient}
      header={<strong>Injected product header</strong>}
    />,
  );

  expect(screen.getByText("Injected product header")).toBeVisible();
  expect(screen.getByText("Loaded feature surface")).toBeVisible();
  routeDeck.store.dispose();
});

it("opens application navigation from a mobile menu without moving the desktop navigation", async () => {
  const contract = frameworkContractFixture();
  const client = new TestRouteDeckClient(frameworkProjectionFixture(), contract);
  const routeDeck = await loadRouteDeck(window, client);
  await routeDeck.store.bootstrap();

  render(
    <ApplicationShell
      routeDeck={routeDeck}
      registry={registry}
      chatClient={idleChatClient}
      header={<strong>Injected product header</strong>}
      navigation={<div>Workspace destinations</div>}
    />,
  );

  expect(screen.getByRole("navigation")).toHaveTextContent("Workspace destinations");
  const menuButton = screen.getByRole("button", { name: "Open navigation menu" });
  fireEvent.click(menuButton);
  const drawer = screen.getByRole("dialog", { name: "Workspace navigation" });
  expect(within(drawer).getByText("Workspace destinations")).toBeVisible();

  routeDeck.store.dispose();
});

it("keeps the loading shell generic for reuse by a fresh project", () => {
  render(<BootstrapLoadingShell />);

  expect(screen.getByRole("status")).toHaveTextContent("Preparing Corpus");
  expect(screen.queryByText("Corpus")).not.toBeInTheDocument();
});

it("replaces an expired conversation without rendering framework recovery UI", async () => {
  const replaceConversation = vi.fn(async () => undefined);
  const fetch = vi.fn(async () => ({
    ok: true,
    status: 204,
    json: async () => ({}),
  }));
  vi.stubGlobal("fetch", fetch);
  const state: RouteDeckBootstrapActionRequiredState = {
    phase: "recovery",
    syncStatus: "error",
    reason: "resume_expired",
    busy: false,
    activeAction: null,
    error: {
      code: "stream_session_expired",
      message: "The RouteDeck event session has expired.",
    },
    actions: [{ kind: "start_new_session", run: vi.fn() }],
  };

  render(
    <CorpusRecoveryCoordinator
      state={state}
      replaceConversation={replaceConversation}
    />,
  );

  expect(screen.getByRole("status")).toHaveTextContent("Preparing Corpus");
  expect(screen.queryByText("Application session expired")).not.toBeInTheDocument();
  expect(screen.queryByText("The RouteDeck event session has expired.")).not.toBeInTheDocument();
  await waitFor(() => expect(replaceConversation).toHaveBeenCalledOnce());
  expect(fetch).not.toHaveBeenCalled();
});
