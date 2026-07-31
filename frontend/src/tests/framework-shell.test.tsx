import { fireEvent, screen, within } from "@testing-library/react";
import type { AgentChatClient } from "@routedeck/core";
import { defineRouteDeckSurfaceRegistry } from "@routedeck/react";
import { expect, it } from "vitest";

import { AgentShell } from "../app/AgentShell";
import { NavgraphSidebar } from "../app/NavgraphSidebar";
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  renderRouteDeckComponent,
} from "./routeDeckHarness";

const idleChatClient: AgentChatClient = Object.freeze({
  async *stream() {},
  async loadConversation() { return []; },
  async startAssistantRun() { throw new Error("not used"); },
  async loadConversationRun() { throw new Error("not used"); },
  async *streamConversationRunEvents() {},
});

const testRegistry = defineRouteDeckSurfaceRegistry({
  "test.active": () => <section>Framework active surface</section>,
  "test.detail": () => <section>Framework detail surface</section>,
});

it("proves the test-only feature contract before product composition", () => {
  const contract = frameworkContractFixture();

  expect(contract.entry_node_id).toBe("test.home");
  expect(Object.keys(contract.nodes)).toEqual(["test.home", "test.detail"]);
  expect(contract.nodes["test.home"]?.operation_ids).toEqual([
    "test.open_detail",
  ]);
  expect(contract.transitions).toEqual([
    {
      source: "test.home",
      operation_id: "test.open_detail",
      outcome: "opened",
      target: "test.detail",
    },
  ]);
  expect(contract.surfaces["test.active"]?.affordances?.at(0)).toEqual({
    id: "open_detail",
    event: "open",
    operation: { id: "test.open_detail" },
  });
});

it("renders the permanent chat, projected surface, and Navgraph slot", async () => {
  const harness = await renderRouteDeckComponent(
    <>
      <AgentShell registry={testRegistry} client={idleChatClient} />
      <NavgraphSidebar />
    </>,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
    },
  );

  expect(screen.getByText("Framework active surface")).toBeVisible();
  expect(
    screen.getByRole("textbox", { name: "Message the assistant" }),
  ).toBeVisible();
  const navgraph = screen.getByRole("complementary", { name: "Navgraph" });
  expect(
    navgraph.querySelector("[data-navgraph-docked]"),
  ).toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Open docked Navgraph" }),
  );
  expect(navgraph).toHaveAttribute("data-expanded", "true");
  expect(
    within(navgraph).getByRole("region", { name: "Navgraph" }),
  ).toBeVisible();
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

  harness.dispose();
});

it("shows the exact current agent context, effective policy prompts, and system prompt", async () => {
  const harness = await renderRouteDeckComponent(<NavgraphSidebar />, {
    contract: frameworkContractFixture(),
    projection: frameworkProjectionFixture(),
    inspection: {
      current_node: "test.home",
      reachable_nodes: [],
      legal_operations: [],
      blocked_operations: [],
      guard_explanations: [],
      capabilities: [],
      surfaces: {},
      route_traces: [],
      diagnostics: {},
      agent_context: {
        model_context: {
          current_node: "test.home",
          active_surface: null,
          visible_entities: [],
          legal_tools: [],
          suggested_actions: [],
          policies: [
            {
              policy_id: "test.policy",
              instruction: "Use only legal test operations.",
            },
          ],
          status: { code: "ready", message: null },
          recent_observations: [],
        },
        system_prompt: "Base prompt\n\nEffective policy prompt",
      },
    },
  });

  fireEvent.click(screen.getByRole("button", { name: "Open docked Navgraph" }));
  fireEvent.click(screen.getByRole("button", { name: "Agent context" }));

  const context = await screen.findByRole("region", { name: "Current agent context" });
  expect(within(context).getByText("test.policy")).toBeVisible();
  expect(within(context).getByText("Use only legal test operations.")).toBeVisible();
  expect(within(context).getByText(/Effective policy prompt/)).toBeVisible();

  harness.dispose();
});

it("docks the projected surface immediately above the composer outside chat history", async () => {
  const harness = await renderRouteDeckComponent(
    <AgentShell registry={testRegistry} client={idleChatClient} />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
    },
  );

  const shell = document.querySelector("[data-agent-shell]");
  const conversation = document.querySelector("[data-agent-conversation]");
  const surfaceDock = document.querySelector("[data-agent-surface-dock]");
  const inputDock = document.querySelector("[data-agent-input-dock]");

  expect(shell).not.toBeNull();
  expect(surfaceDock).not.toBeNull();
  expect(inputDock).not.toBeNull();
  expect(surfaceDock?.parentElement).toBe(shell);
  expect(inputDock?.parentElement).toBe(shell);
  expect(surfaceDock?.nextElementSibling).toBe(inputDock);
  expect(conversation?.querySelector("[data-routedeck-surface-host]")).toBeNull();
  expect(surfaceDock).toHaveTextContent("Framework active surface");

  harness.dispose();
});

it("applies the compiled node conversation-input policy without product node IDs", async () => {
  const contract = frameworkContractFixture();
  contract.nodes["test.home"]!.conversation_input = {
    enabled: false,
    disabled_message: "Input is unavailable for this test node.",
  };
  const harness = await renderRouteDeckComponent(
    <AgentShell registry={testRegistry} client={idleChatClient} />,
    {
      contract,
      projection: frameworkProjectionFixture(),
    },
  );

  expect(screen.getByLabelText("Message the assistant")).toBeDisabled();
  expect(screen.getByText("Input is unavailable for this test node.")).toBeVisible();

  harness.dispose();
});

it("keeps framework conversation labels product-neutral", async () => {
  const projection = frameworkProjectionFixture();
  projection.surfaces.active = null;
  const harness = await renderRouteDeckComponent(
    <AgentShell
      registry={testRegistry}
      client={idleChatClient}
      initialConversation={[
        {
          turn_id: "assistant-framework",
          request_id: "entry-framework",
          role: "assistant",
          content: "Framework response",
        },
      ]}
    />,
    {
      contract: frameworkContractFixture(),
      projection,
    },
  );

  expect(screen.getByText("Assistant")).toBeVisible();
  expect(screen.queryByText("Corpus")).not.toBeInTheDocument();
  expect(screen.queryByText("Lounge")).not.toBeInTheDocument();
  expect(screen.queryByText("Workspace")).not.toBeInTheDocument();

  harness.dispose();
});

it("places projected quick actions under the latest assistant turn", async () => {
  const projection = frameworkProjectionFixture();
  projection.surfaces.active = null;
  projection.suggested_actions = [
    {
      action_id: "test.learn_more",
      label: "Learn more",
      operation_id: "test.open_detail",
      arguments: {},
    },
  ];
  const harness = await renderRouteDeckComponent(
    <AgentShell
      registry={testRegistry}
      client={idleChatClient}
      initialConversation={[
        {
          turn_id: "assistant-actions",
          request_id: "entry-actions",
          role: "assistant",
          content: "Framework response",
        },
      ]}
    />,
    { contract: frameworkContractFixture(), projection },
  );

  const turn = screen.getByText("Framework response").closest("[data-agent-turn]");
  expect(turn).not.toBeNull();
  expect(within(turn as HTMLElement).getByRole("button", { name: "Learn more" })).toBeVisible();
  expect(
    document.querySelector("[data-agent-input-dock] [data-agent-quick-actions]"),
  ).toBeNull();

  harness.dispose();
});
