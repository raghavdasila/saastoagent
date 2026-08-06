import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { AgentsHomeSurface } from "../features/agents/AgentsHomeSurface";
import { CreateAgentSurface } from "../features/agents/CreateAgentSurface";
import type { AgentClient } from "../features/agents/client";
import type { AgentView } from "../features/agents/models";
import { AgentStore } from "../features/agents/store";


function props(
  id: "agents.home" | "agents.create",
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"],
): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: id, component: id, props: [] },
    slot: "active",
    props: {},
    spec: {
      id,
      component: id,
      lifecycle: "stable",
      public_props_schema: {},
      affordances: [],
    },
    dispatchAffordance,
  };
}


function agent(overrides: Partial<AgentView> = {}): AgentView {
  return {
    id: "7db3745e-6f77-4b92-929c-4d2292fb3708",
    name: "Research Agent",
    description: "Researches the owner's task",
    instructions: "Research carefully.",
    lifecycle: "active",
    current_version: 1,
    created_at: "2026-08-06T00:00:00Z",
    updated_at: "2026-08-06T00:00:00Z",
    ...overrides,
  };
}


function storeWith(list: ReturnType<typeof vi.fn>) {
  return new AgentStore({ list } as unknown as AgentClient);
}


it("loads, selects, and edits only domain state in the Agents store", async () => {
  const first = agent();
  const second = agent({
    id: "ca39d0cf-33f7-4b4c-ae7e-ad7331856bf8",
    name: "Support Agent",
  });
  const list = vi.fn(async () => ({ agents: [first, second] }));
  const store = storeWith(list);

  await store.refresh();
  expect(store.snapshot()).toMatchObject({
    agents: [first, second],
    selectedId: first.id,
    loading: false,
    error: null,
  });
  store.select(second.id);
  expect(store.snapshot().selectedId).toBe(second.id);
  expect(store.snapshot()).not.toHaveProperty("currentNodeId");
  expect(store.snapshot()).not.toHaveProperty("legalOperations");
});


it("creates an agent through the declared RouteDeck action and refreshes persisted truth", async () => {
  const list = vi.fn(async () => ({ agents: [] }));
  const store = storeWith(list);
  const dispatch = vi.fn(async () => completed("agents.create_agent", "created"));
  render(<CreateAgentSurface {...props("agents.create", dispatch)} store={store} />);

  fireEvent.change(screen.getByLabelText("Name"), {
    target: { value: "Research Agent" },
  });
  fireEvent.change(screen.getByLabelText("Description"), {
    target: { value: "Researches tasks" },
  });
  fireEvent.change(screen.getByLabelText("Instructions"), {
    target: { value: "Research carefully." },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create agent" }));

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("create_agent", {
    name: "Research Agent",
    description: "Researches tasks",
    instructions: "Research carefully.",
  }));
  await waitFor(() => expect(list).toHaveBeenCalledTimes(1));
});


it("saves a new immutable configuration version with the selected version guard", async () => {
  const original = agent();
  const updated = agent({
    instructions: "Research and cite carefully.",
    current_version: 2,
  });
  const list = vi.fn()
    .mockResolvedValueOnce({ agents: [original] })
    .mockResolvedValueOnce({ agents: [updated] });
  const store = storeWith(list);
  const dispatch = vi.fn(async () => completed("agents.save_changes", "saved"));
  render(<AgentsHomeSurface {...props("agents.home", dispatch)} store={store} />);

  await screen.findByDisplayValue("Research carefully.");
  fireEvent.change(screen.getByLabelText("Instructions"), {
    target: { value: "Research and cite carefully." },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save new version" }));

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("save_changes", {
    agent_id: original.id,
    expected_version: 1,
    name: original.name,
    description: original.description,
    instructions: "Research and cite carefully.",
  }));
  await waitFor(() => expect(screen.getAllByText("Version 2")).toHaveLength(2));
});


function completed(operationId: string, outcome: string): RouteDeckDispatchResult {
  return {
    disposition: "completed",
    operation_id: operationId,
    request_id: "agent-action-request",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface",
      phases: ["received", "completed"],
      attempt_id: "agent-action-attempt",
      request_fingerprint: "agent-action-fingerprint",
      delivery_phase: "response_received",
      result_id: "agent-action-result",
      result_fingerprint: "agent-action-result-fingerprint",
    },
    review: null,
    outcome,
    failure: null,
  };
}
