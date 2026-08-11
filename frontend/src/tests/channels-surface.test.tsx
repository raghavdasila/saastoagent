import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { AgentStore } from "../features/agents/store";
import type { AgentClient } from "../features/agents/client";
import type { AgentRuntimeClient } from "../features/builder/client";
import { ChannelDraftStore } from "../features/delivery/channelDraftStore";
import { ChannelsSurface } from "../features/delivery/ChannelsSurface";

const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;

function surfaceProps(dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"]): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: "channels.home", component: "channels.home", props: [] },
    slot: "active",
    props: { selected_agent_ref: agentRef },
    spec: { id: "channels.home", component: "channels.home", lifecycle: "stable", public_props_schema: {}, affordances: [] },
    dispatchAffordance,
  };
}

function agentStore(): AgentStore {
  return new AgentStore({
    list: vi.fn(async () => ({ agents: [{
      id: agentId,
      name: "Catalog Agent",
      description: "Catalog help",
      instructions: "Use the approved catalog API.",
      lifecycle: "active",
      current_version: 1,
      created_at: "2026-08-08T00:00:00Z",
      updated_at: "2026-08-08T00:00:00Z",
    }] })),
  } as unknown as AgentClient);
}

const runtimeClient = {
  channels: vi.fn(async () => ({ channels: [] })),
  deployments: vi.fn(async () => ({ deployments: [] })),
  builds: vi.fn(async () => ({ builds: [] })),
  evaluations: vi.fn(async () => ({ evaluation_sets: [] })),
} as unknown as AgentRuntimeClient;

it("restores the exact Agent-scoped hosted-channel draft after a RouteDeck remount", async () => {
  const store = agentStore();
  const drafts = new ChannelDraftStore();
  const dispatch = vi.fn(async () => completed("channels.create", "created"));
  const first = render(<ChannelsSurface {...surfaceProps(dispatch)} agentStore={store} runtimeClient={runtimeClient} draftStore={drafts} />);

  await screen.findByText("Catalog Agent");
  fireEvent.input(screen.getByLabelText("Name"), { target: { value: "Catalog Web" } });
  fireEvent.input(screen.getByLabelText("Address"), { target: { value: "Catalog-Web" } });
  first.unmount();

  render(<ChannelsSurface {...surfaceProps(dispatch)} agentStore={store} runtimeClient={runtimeClient} draftStore={drafts} />);
  expect(await screen.findByLabelText("Name")).toHaveValue("Catalog Web");
  expect(screen.getByLabelText("Address")).toHaveValue("catalog-web");
  fireEvent.click(screen.getByRole("button", { name: "Create channel" }));

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("create", {
    agent_ref: agentRef,
    name: "Catalog Web",
    slug: "catalog-web",
  }));
  await waitFor(() => expect(screen.getByLabelText("Name")).toHaveValue(""));
  expect(drafts.get(agentId)).toEqual({ name: "", slug: "" });
});

it("stages deployment review without misreporting the required review as failure", async () => {
  const dispatch = vi.fn(async () => requiredReview("deployment.deploy"));
  const deliveryClient = {
    channels: vi.fn(async () => ({ channels: [{
      id: "channel-1", name: "Catalog Web", slug: "catalog-web", status: "ready",
      enabled: true, active_deployment_id: null,
    }] })),
    deployments: vi.fn(async () => ({ deployments: [] })),
    builds: vi.fn(async () => ({ builds: [{
      id: "build-1", status: "ready", runtime_lifecycle: "running", agent_version: 3,
    }] })),
    evaluations: vi.fn(async () => ({ evaluation_sets: [{
      id: "set-1", build_id: "build-1", eligible: true, cases: [],
    }] })),
  } as unknown as AgentRuntimeClient;

  render(<ChannelsSurface {...surfaceProps(dispatch)} agentStore={agentStore()} runtimeClient={deliveryClient} draftStore={new ChannelDraftStore()} />);
  const review = await screen.findByRole("button", { name: "Review deployment" });
  await waitFor(() => expect(review).toBeEnabled());
  fireEvent.click(review);

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("deploy", {
    agent_ref: agentRef,
    channel_id: "channel-1",
    build_id: "build-1",
  }));
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

it("explains missing eligibility and continues the same selected Agent to Evaluation", async () => {
  const dispatch = vi.fn(async () => completed("agents.open_evaluation", "opened"));

  render(<ChannelsSurface {...surfaceProps(dispatch)} agentStore={agentStore()} runtimeClient={runtimeClient} draftStore={new ChannelDraftStore()} />);

  expect(await screen.findByText("No evaluated build is eligible to publish.")).toBeVisible();
  expect(screen.getByText("Corpus will not select or substitute another build.", { exact: false })).toBeVisible();
  expect(screen.getByLabelText("Eligible build")).toHaveValue("");
  expect(screen.getByRole("button", { name: "Review deployment" })).toBeDisabled();

  fireEvent.click(screen.getByRole("button", { name: "Continue in Evaluation" }));

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("continue_to_evaluation", {
    agent_ref: agentRef,
  }));
});

function completed(operationId: string, outcome: string): RouteDeckDispatchResult {
  return {
    disposition: "completed",
    operation_id: operationId,
    request_id: "channel-request",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface",
      phases: ["received", "completed"],
      attempt_id: "channel-attempt",
      request_fingerprint: "channel-request-fingerprint",
      delivery_phase: "response_received",
      result_id: "channel-result",
      result_fingerprint: "channel-result-fingerprint",
    },
    review: null,
    outcome,
    failure: null,
  };
}

function requiredReview(operationId: string): RouteDeckDispatchResult {
  return {
    ...completed(operationId, "unused"),
    disposition: "requires_review",
    review: { id: "review-exact", expires_at: "2026-08-12T00:00:00Z" },
    outcome: null,
    evidence: {
      ...completed(operationId, "unused").evidence,
      phases: ["received", "review_staged"],
      delivery_phase: "not_sent",
      result_id: null,
      result_fingerprint: null,
    },
  };
}
