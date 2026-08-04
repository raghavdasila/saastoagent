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
  const resizeHandle = within(navgraph).getByRole("separator", {
    name: "Resize Navgraph sidebar",
  });
  expect(resizeHandle).toHaveAttribute("aria-valuenow", "420");
  fireEvent.keyDown(resizeHandle, { key: "ArrowLeft" });
  expect(resizeHandle).toHaveAttribute("aria-valuenow", "444");
  expect(navgraph).toHaveStyle({ "--corpus-navgraph-width": "444px" });
  expect(navgraph.querySelector(".corpus-navgraph-inspector")).toBeInTheDocument();
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
        kind: "current_snapshot",
        snapshot: { session_version: 2, projection_version: 2, event_cursor: 4 },
        model: { provider: "ollama", name: "test-model" },
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
        policy_resolution: [
          {
            policy_id: "test.policy",
            instruction: "Use only legal test operations.",
            scope: "node",
            owner_id: "test.home",
            source_order: 0,
          },
        ],
        prompt: {
          base: "Base prompt",
          policy_section: "Effective policy prompt",
          context_section: "Current context",
          assembled: "Base prompt\n\nEffective policy prompt",
        },
        system_prompt: "Base prompt\n\nEffective policy prompt",
        messages: [{ id: "user-1", role: "human", content: "Hello" }],
        tools: [],
        limits: { recent_observations: 8 },
        intentional_exclusions: ["private_form_values"],
      },
      invocation_traces: null,
    },
  });

  fireEvent.click(screen.getByRole("button", { name: "Open docked Navgraph" }));
  fireEvent.click(screen.getByRole("button", { name: "Agent context" }));

  const context = await screen.findByRole("region", { name: "Current agent context" });
  expect(within(context).getByText("test.policy")).toBeVisible();
  expect(within(context).getByText("Use only legal test operations.")).toBeVisible();
  expect(within(context).getAllByText(/Effective policy prompt/)).toHaveLength(2);
  expect(within(context).getByText(/node · test.home/)).toBeVisible();
  expect(within(context).getByText("Navgraph diagnostics")).toBeVisible();

  harness.dispose();
});

it("lays out and renders the invocation trace view as a first-class inspector tab", async () => {
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
      agent_context: null,
      invocation_traces: { traces: [] },
    },
  });

  fireEvent.click(screen.getByRole("button", { name: "Open docked Navgraph" }));
  const switcher = screen.getByLabelText("Navgraph view");
  expect(within(switcher).getAllByRole("button")).toHaveLength(3);
  fireEvent.click(within(switcher).getByRole("button", { name: "Invocation trace" }));

  const traces = await screen.findByRole("region", { name: "Invocation traces" });
  expect(within(traces).getByText("Sanitized RouteDeck-to-model evidence")).toBeVisible();
  expect(within(traces).getByRole("button", { name: "Refresh" })).toBeVisible();
  expect(within(traces).getByText("No model invocation has occurred in this session.")).toBeVisible();

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
