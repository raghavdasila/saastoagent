import { render, screen } from "@testing-library/react";
import type { AgentChatClient } from "@routedeck/core";
import { defineRouteDeckSurfaceRegistry } from "@routedeck/react";
import { expect, it } from "vitest";

import { ApplicationShell } from "../app/ApplicationShell";
import { BootstrapLoadingShell } from "../app/BootstrapLoadingShell";
import { loadRouteDeck } from "../app/loadRouteDeck";
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  TestRouteDeckClient,
} from "./routeDeckHarness";

const idleChatClient: AgentChatClient = Object.freeze({
  async *stream() {},
});
const registry = defineRouteDeckSurfaceRegistry({
  "test.active": () => <section>Loaded feature surface</section>,
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

it("keeps the loading shell generic for reuse by a fresh project", () => {
  render(<BootstrapLoadingShell />);

  expect(screen.getByRole("status")).toHaveTextContent("Preparing application");
  expect(screen.queryByText("Corpus")).not.toBeInTheDocument();
});
