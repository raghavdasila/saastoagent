import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import type { AgentClient } from "../features/agents/client";
import { AgentStore } from "../features/agents/store";
import type { AgentRuntimeClient } from "../features/builder/client";
import type { PlaygroundInteractionView, SandboxDeploymentCollectionView } from "../features/builder/models";
import { SandboxSurface } from "../features/builder/SandboxSurface";

it("continues one deployment-pinned Playground conversation through review and another turn", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const buildId = "5c1ad911-849f-4ef6-aadb-b2a793ac4ae0";
  const deploymentId = "b1641679-a74c-4b11-8964-fd146847a21d";
  const sessionId = "sandbox-playground-session";
  const createdAt = "2026-08-19T00:00:00Z";
  const session = {
    session_id: sessionId,
    target_id: "sandbox-target",
    deployment_id: deploymentId,
    runtime_deployment_id: "runtime-sandbox-deployment",
    build_id: buildId,
    purpose: "playground" as const,
    created_at: createdAt,
    projection: null,
  };
  const sandbox: SandboxDeploymentCollectionView = {
    agent_id: agentId,
    target_id: "sandbox-target",
    active_deployment_id: deploymentId,
    deployments: [{
      id: deploymentId, target_id: "sandbox-target", agent_id: agentId,
      build_id: buildId, mode: "sandbox", status: "ready",
      request_key: "deploy-request", runtime_deployment_id: "runtime-sandbox-deployment",
      failure_code: null, failure_message: null, created_at: createdAt, updated_at: createdAt,
    }],
    playground_sessions: [session],
  };
  const waiting: PlaygroundInteractionView = {
    session,
    interaction_id: "interaction-1",
    projection: {
      revision: 3,
      messages: [
        { role: "user", content: "Create the exact cart." },
        { role: "assistant", content: "I prepared the action for review." },
      ],
      surfaces: [{ component: "agent_runtime.write_review", props: { review_id: "review-1" } }],
      suggested_actions: [],
    },
  };
  const reviewed: PlaygroundInteractionView = {
    ...waiting,
    projection: {
      revision: 4,
      messages: [...waiting.projection.messages, { role: "assistant", content: "The reviewed cart action completed." }],
      surfaces: [], suggested_actions: [],
    },
  };
  const continued: PlaygroundInteractionView = {
    ...reviewed,
    interaction_id: "interaction-2",
    projection: {
      ...reviewed.projection,
      revision: 5,
      messages: [
        ...reviewed.projection.messages,
        { role: "user", content: "What is in that same cart?" },
        { role: "assistant", content: "The same cart contains one Medusa T-Shirt." },
      ],
    },
  };
  const runtimeClient = {
    builds: vi.fn(async () => ({ agent_id: agentId, builds: [] })),
    sandboxDeployment: vi.fn(async () => sandbox),
    evaluations: vi.fn(async () => ({ agent_id: agentId, evaluation_sets: [] })),
    playgroundSession: vi.fn(async () => waiting),
    resolvePlaygroundReview: vi.fn(async () => reviewed),
    sendPlaygroundMessage: vi.fn(async () => continued),
    sandboxDiagnostics: vi.fn(async () => ({
      session, projection: continued.projection,
      interactions: [{ interaction_id: "interaction-2", status: "succeeded" }],
    })),
  } as unknown as AgentRuntimeClient;
  const agentStore = new AgentStore({
    list: vi.fn(async () => ({ agents: [{
      id: agentId, name: "Store Agent", description: "", instructions: "Use exact operations.",
      lifecycle: "active", current_version: 1, created_at: createdAt, updated_at: createdAt,
    }] })),
    listSources: vi.fn(async () => ({ attachments: [] })),
    listBuilds: vi.fn(async () => ({ builds: [] })),
    inspectDependencies: vi.fn(async () => ({ agent_id: agentId, source_attachments: [], build_ids: [], blocks_delete: false })),
  } as unknown as AgentClient);
  const dispatch = vi.fn(async () => ({ disposition: "completed", outcome: "opened", failure: null }));
  const props = {
    surface: { surface_id: "sandbox.home", component: "sandbox.home", props: [] }, slot: "active",
    props: { selected_agent_ref: agentRef },
    spec: { id: "sandbox.home", component: "sandbox.home", lifecycle: "stable", public_props_schema: {}, affordances: [] },
    dispatchAffordance: dispatch,
  } as unknown as RouteDeckSurfaceComponentProps;

  render(<SandboxSurface {...props} agentStore={agentStore} runtimeClient={runtimeClient} />);
  await screen.findByRole("heading", { name: "Deployment" });
  fireEvent.click(screen.getByRole("button", { name: "Playground" }));
  expect(await screen.findByText("I prepared the action for review.")).toBeVisible();
  expect(screen.getByRole("heading", { name: "Review Agent action" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Approve action" }));
  expect(await screen.findByText("The reviewed cart action completed.")).toBeVisible();
  expect(runtimeClient.resolvePlaygroundReview).toHaveBeenCalledWith(agentId, sessionId, "review-1", true);

  fireEvent.change(screen.getByLabelText("Message"), { target: { value: "What is in that same cart?" } });
  fireEvent.click(screen.getByRole("button", { name: "Send message" }));
  expect(await screen.findByText("The same cart contains one Medusa T-Shirt.")).toBeVisible();
  expect(runtimeClient.sendPlaygroundMessage).toHaveBeenCalledWith(agentId, sessionId, "What is in that same cart?");

  fireEvent.click(screen.getByRole("button", { name: "Open diagnostics" }));
  await waitFor(() => expect(screen.getByText("Runtime revision 5")).toBeVisible());
  expect(runtimeClient.sandboxDiagnostics).toHaveBeenCalledWith(agentId, sessionId);
});
