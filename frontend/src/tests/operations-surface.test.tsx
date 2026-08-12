import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import type { AgentClient } from "../features/agents/client";
import { AgentStore } from "../features/agents/store";
import type { AgentRuntimeClient } from "../features/builder/client";
import type { OperationsCollectionView } from "../features/builder/models";
import { OperationsSurface } from "../features/operations/OperationsSurface";

const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;

function props(dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"]): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: "operations.home", component: "operations.home", props: [] },
    slot: "active",
    props: { selected_agent_ref: agentRef },
    spec: { id: "operations.home", component: "operations.home", lifecycle: "stable", public_props_schema: {}, affordances: [] },
    dispatchAffordance,
  };
}

function store(): AgentStore {
  return new AgentStore({ list: vi.fn(async () => ({ agents: [{
    id: agentId, name: "Catalog Agent", description: "Catalog help", instructions: "Use the approved API.",
    lifecycle: "active", current_version: 1, created_at: "2026-08-08T00:00:00Z", updated_at: "2026-08-08T00:00:00Z",
  }] })) } as unknown as AgentClient);
}

it("does not report an empty Operations history while authoritative state is loading", async () => {
  let resolveOperations!: (value: OperationsCollectionView) => void;
  const operations = new Promise<OperationsCollectionView>((resolve) => { resolveOperations = resolve; });
  const runtimeClient = {
    operations: vi.fn(() => operations), builds: vi.fn(async () => ({ builds: [] })),
  } as unknown as AgentRuntimeClient;

  render(<OperationsSurface {...props(vi.fn())} runtimeClient={runtimeClient} agentStore={store()} />);

  expect(await screen.findByRole("status")).toHaveTextContent("Loading exact deployed interactions and immutable build lineage");
  expect(screen.queryByText("No deployed Agent interactions yet.")).not.toBeInTheDocument();

  resolveOperations({ interactions: [] });
  expect(await screen.findByText("No deployed Agent interactions yet.")).toBeVisible();
});

it("presents one deployed interaction as a readable outcome and promotes it explicitly", async () => {
  const dispatch = vi.fn(async () => completed());
  const runtimeClient = {
    operations: vi.fn(async () => ({ interactions: [{
      interaction_id: "interaction-1", agent_id: agentId, build_id: "build-1", deployment_id: "deployment-1", session_id: "session-1",
      input_summary: "List product types", output_summary: "Three product types are available.", status: "completed",
      evaluation_case_id: null,
      events: [{ sequence: 1, kind: "api.result", safe_data: { operation_id: "GetProductTypes", status: "succeeded", http_status: 200 } }],
    }] })),
    builds: vi.fn(async () => ({ builds: [] })),
  } as unknown as AgentRuntimeClient;

  render(<OperationsSurface {...props(dispatch)} runtimeClient={runtimeClient} agentStore={store()} />);

  expect(await screen.findByRole("heading", { name: "List product types" })).toBeVisible();
  expect(screen.getByText("Three product types are available.")).toBeVisible();
  expect(screen.getByText("Successful").nextElementSibling).toHaveTextContent("1");
  fireEvent.click(screen.getByText("Create an Evaluation case from this interaction"));
  fireEvent.click(screen.getByRole("button", { name: "Create Evaluation case" }));

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("promote", {
    interaction_id: "interaction-1",
    set_name: "Operations regressions",
    title: "List product types",
    category: "deployed-interaction",
    difficulty: "medium",
    mandatory: true,
  }));
  expect(await screen.findByRole("status")).toHaveTextContent("Evaluation case created from this interaction.");
  expect(screen.getByRole("button", { name: "Evaluation case created" })).toBeDisabled();
});

it("restores the persisted promotion result after Operations reloads", async () => {
  const runtimeClient = {
    operations: vi.fn(async () => ({ interactions: [{
      interaction_id: "interaction-promoted", agent_id: agentId, build_id: "build-1", deployment_id: "deployment-1", session_id: "session-1",
      input_summary: "List product types", output_summary: "Three product types are available.", status: "completed",
      evaluation_case_id: "case-1",
      events: [{ sequence: 1, kind: "api.result", safe_data: { operation_id: "GetProductTypes", status: "succeeded", http_status: 200 } }],
    }] })),
    builds: vi.fn(async () => ({ builds: [] })),
  } as unknown as AgentRuntimeClient;

  render(<OperationsSurface {...props(vi.fn())} runtimeClient={runtimeClient} agentStore={store()} />);

  fireEvent.click(await screen.findByText("Create an Evaluation case from this interaction"));
  expect(screen.getByRole("status")).toHaveTextContent("Evaluation case created from this interaction.");
  expect(screen.getByRole("button", { name: "Evaluation case created" })).toBeDisabled();
});

function completed(): RouteDeckDispatchResult {
  return {
    disposition: "completed", operation_id: "operations.promote_evaluation_case", request_id: "request-1",
    session_version: 2, projection_version: 2, review: null, outcome: "promoted", failure: null,
    evidence: {
      source: "surface", phases: ["received", "completed"], attempt_id: "attempt-1", request_fingerprint: "request-fingerprint",
      delivery_phase: "response_received", result_id: "result-1", result_fingerprint: "result-fingerprint",
    },
  };
}
