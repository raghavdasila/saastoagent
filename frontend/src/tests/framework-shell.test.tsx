import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type {
  AgentChatClient,
  RouteDeckConversationClient,
  RouteDeckDispatchResult,
} from "@routedeck/core";
import { defineRouteDeckSurfaceRegistry } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { AgentShell, CorpusReviewRequiredNotice } from "../app/AgentShell";
import { CorpusSuggestedActions } from "../app/CorpusSuggestedActions";
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

it("does not resume an entry request that already has a finalized assistant turn", async () => {
  const projection = frameworkProjectionFixture();
  projection.interaction = {
    phase: "active",
    owner: "chat",
    request_id: "entry-completed",
  };
  const loadConversation = vi.fn(
    () => new Promise<never>(() => undefined),
  );
  const client = {
    ...idleChatClient,
    loadConversation,
  } as AgentChatClient;
  const harness = await renderRouteDeckComponent(
    <AgentShell
      registry={testRegistry}
      client={client}
      initialConversation={[{
        turn_id: "assistant-completed",
        request_id: "entry-completed",
        role: "assistant",
        content: "Workspace is ready.",
      }]}
    />,
    { contract: frameworkContractFixture(), projection },
  );

  expect(screen.getByRole("textbox", { name: "Message the assistant" })).toBeEnabled();
  expect(screen.queryByRole("button", { name: "Stop response" })).not.toBeInTheDocument();
  expect(loadConversation).not.toHaveBeenCalled();
  harness.dispose();
});

it("recovers the authoritative conversation when an adopted entry run becomes idle", async () => {
  const active = frameworkProjectionFixture();
  active.interaction = {
    phase: "active",
    owner: "chat",
    request_id: "entry-adopted",
  };
  let historyLoads = 0;
  const loadConversation = vi.fn((signal?: AbortSignal) => {
    historyLoads += 1;
    if (historyLoads === 1) {
      return new Promise<never>((_resolve, reject) => {
        signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
      });
    }
    return Promise.resolve([{
      turn_id: "assistant-adopted",
      request_id: "entry-adopted",
      role: "assistant" as const,
      content: "Workspace is ready.",
    }]);
  });
  const client = { ...idleChatClient, loadConversation } as AgentChatClient;
  const harness = await renderRouteDeckComponent(
    <AgentShell registry={testRegistry} client={client} />,
    { contract: frameworkContractFixture(), projection: active },
  );

  expect(screen.getByRole("button", { name: "Stop response" })).toBeVisible();
  const idle = frameworkProjectionFixture();
  idle.session_version = 2;
  idle.projection_version = 2;
  harness.client.setProjection(idle);
  await act(async () => {
    await harness.store.resync();
  });

  await waitFor(() => {
    expect(screen.getByRole("textbox", { name: "Message the assistant" })).toBeEnabled();
  });
  expect(screen.queryByRole("button", { name: "Stop response" })).not.toBeInTheDocument();
  expect(screen.getByText("Workspace is ready.", { exact: true })).toBeVisible();
  expect(loadConversation).toHaveBeenCalledTimes(2);
  harness.dispose();
});

it("does not remount and abort a chat turn between assistant_end and stream_end", async () => {
  let releaseStreamEnd!: () => void;
  const streamEndGate = new Promise<void>((resolve) => {
    releaseStreamEnd = resolve;
  });
  let streamSignal: AbortSignal | undefined;
  let harness!: Awaited<ReturnType<typeof renderRouteDeckComponent>>;
  const client = {
    ...idleChatClient,
    async *stream(request, signal) {
      streamSignal = signal;
      const active = frameworkProjectionFixture();
      active.interaction = {
        phase: "active",
        owner: "chat",
        request_id: request.request_id,
      };
      harness.client.setProjection(active);
      await harness.store.resync();
      yield {
        type: "stream_start" as const,
        request_id: request.request_id,
        session_version: 1,
      };
      yield {
        type: "user_message" as const,
        request_id: request.request_id,
        turn_id: "user-stream-boundary",
        content: request.message,
      };
      yield {
        type: "assistant_delta" as const,
        request_id: request.request_id,
        content: "The Source workspace is ready.",
      };
      const idle = frameworkProjectionFixture();
      idle.session_version = 2;
      idle.projection_version = 2;
      harness.client.setProjection(idle);
      yield {
        type: "assistant_end" as const,
        request_id: request.request_id,
        session_version: 2,
        projection_version: 2,
        turn_id: "assistant-stream-boundary",
      };
      await streamEndGate;
      yield {
        type: "stream_end" as const,
        request_id: request.request_id,
        status: "completed" as const,
      };
    },
    async loadConversation() {
      return [{
        turn_id: "assistant-stream-boundary",
        request_id: "framework-request-1",
        role: "assistant" as const,
        content: "The Source workspace is ready.",
      }];
    },
  } as AgentChatClient & RouteDeckConversationClient;
  harness = await renderRouteDeckComponent(
    <AgentShell registry={testRegistry} client={client} />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
    },
  );

  fireEvent.change(
    screen.getByRole("textbox", { name: "Message the assistant" }),
    { target: { value: "Help me prepare the Source workspace." } },
  );
  const composer = screen.getByRole("textbox", { name: "Message the assistant" });
  composer.focus();
  fireEvent.keyDown(composer, { key: "Enter" });

  await waitFor(() => {
    expect(screen.getByText("The Source workspace is ready.", { exact: true })).toBeVisible();
    expect(harness.store.getState().projection?.interaction.phase).toBe("idle");
  });
  expect(screen.getByRole("button", { name: "Stop response" })).toBeVisible();
  expect(streamSignal?.aborted).toBe(false);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();

  releaseStreamEnd();
  await waitFor(() => {
    expect(screen.getByRole("textbox", { name: "Message the assistant" })).toBeEnabled();
  });
  expect(screen.getByRole("textbox", { name: "Message the assistant" })).toHaveFocus();
  expect(streamSignal?.aborted).toBe(false);
  expect(screen.queryByRole("button", { name: "Stop response" })).not.toBeInTheDocument();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  harness.dispose();
});

it("shows Corpus-owned review copy without internal operation identity", () => {
  render(<CorpusReviewRequiredNotice />);

  expect(screen.getByRole("status")).toHaveTextContent(
    "A consequential Corpus action is waiting for your explicit review.",
  );
  expect(screen.queryByText(/agents\.(archive|delete)_agent/)).not.toBeInTheDocument();
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

it("renders a projected detail surface alongside the active product surface", async () => {
  const projection = frameworkProjectionFixture();
  projection.surfaces.detail = [{
    surface_id: "test.detail",
    component: "test.detail",
    props: [],
  }];
  const harness = await renderRouteDeckComponent(
    <AgentShell registry={testRegistry} client={idleChatClient} />,
    { contract: frameworkContractFixture(), projection },
  );

  expect(screen.getByText("Framework active surface")).toBeVisible();
  expect(screen.getByText("Framework detail surface")).toBeVisible();
  harness.dispose();
});

it("renders a Corpus-owned terminal failure for a failed suggested action", async () => {
  const projection = frameworkProjectionFixture();
  projection.suggested_actions = [{
    action_id: "verification-resend",
    operation_id: "lounge.request_verification_delivery",
    label: "Resend verification",
    arguments: {},
  }];
  const harness = await renderRouteDeckComponent(
    <CorpusSuggestedActions />,
    {
      contract: frameworkContractFixture(),
      projection,
      dispatchResult: failedOperation("Verification requests are temporarily limited. Try again later."),
    },
  );

  fireEvent.click(screen.getByRole("button", { name: "Resend verification" }));

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Verification requests are temporarily limited. Try again later.",
  );
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
      recent_operations: [],
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
      recent_operations: [],
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

it("resets hidden horizontal surface scroll when the owner maximizes the workspace", async () => {
  const harness = await renderRouteDeckComponent(
    <AgentShell registry={testRegistry} client={idleChatClient} />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
    },
  );
  const shell = document.querySelector<HTMLElement>("[data-agent-shell]");
  const surfaceDock = document.querySelector<HTMLElement>("[data-agent-surface-dock]");
  expect(shell).not.toBeNull();
  expect(surfaceDock).not.toBeNull();
  if (shell === null || surfaceDock === null) {
    throw new Error("Expected the Agent shell and surface dock to render.");
  }
  surfaceDock.scrollLeft = 180;

  fireEvent.click(screen.getByRole("button", { name: "Maximize surface" }));

  await waitFor(() => expect(shell).toHaveAttribute("data-surface-layout", "split"));
  expect(surfaceDock.scrollLeft).toBe(0);
  harness.dispose();
});

it("resets the surface dock scroll position when the current node changes", async () => {
  const projection = frameworkProjectionFixture();
  const harness = await renderRouteDeckComponent(
    <AgentShell registry={testRegistry} client={idleChatClient} />,
    {
      contract: frameworkContractFixture(),
      projection,
    },
  );
  const surfaceDock = document.querySelector<HTMLElement>("[data-agent-surface-dock]");
  expect(surfaceDock).not.toBeNull();
  if (surfaceDock === null) {
    throw new Error("Expected the surface dock to render.");
  }
  surfaceDock.scrollTop = 180;

  const detailProjection = frameworkProjectionFixture();
  detailProjection.current = { node_id: "test.detail", route_params: [] };
  detailProjection.navigation.current = detailProjection.current;
  detailProjection.surfaces.active = {
    surface_id: "test.detail",
    component: "test.detail",
    props: [],
  };
  detailProjection.session_version = 2;
  detailProjection.projection_version = 2;
  harness.client.setProjection(detailProjection);

  await act(async () => {
    await harness.store.resync();
  });

  expect(surfaceDock.scrollTop).toBe(0);
  expect(surfaceDock).toHaveTextContent("Framework detail surface");
  harness.dispose();
});

function failedOperation(publicMessage: string): RouteDeckDispatchResult {
  return {
    disposition: "failed",
    request_id: "request-failed",
    operation_id: "lounge.request_verification_delivery",
    session_version: 1,
    projection_version: 1,
    evidence: {
      source: "surface",
      phases: [],
      attempt_id: "attempt-failed",
      request_fingerprint: "fingerprint-failed",
      delivery_phase: "not_sent",
    },
    outcome: null,
    review: null,
    failure: {
      kind: "business",
      code: "verification_rate_limited",
      phase: "tool_failed",
      correlation_id: "correlation-failed",
      operation_id: "lounge.request_verification_delivery",
      request_id: "request-failed",
      public_message: publicMessage,
      recovery_directive: null,
      safe_details: {},
    },
  };
}

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
