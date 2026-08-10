import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { AgentsHomeSurface } from "../features/agents/AgentsHomeSurface";
import { AgentLifecycleReviewSurface } from "../features/agents/AgentLifecycleReviewSurface";
import { CreateAgentSurface } from "../features/agents/CreateAgentSurface";
import type { AgentClient } from "../features/agents/client";
import type { AgentView } from "../features/agents/models";
import { AgentStore } from "../features/agents/store";
import type { SourceClient } from "../features/sources/sourceClient";
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  renderRouteDeckComponent,
} from "./routeDeckHarness";


function props(
  id: "agents.home" | "agents.create" | "agents.archive_review" | "agents.delete_review",
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"],
  surfaceValues: RouteDeckSurfaceComponentProps["props"] = {},
): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: id, component: id, props: [] },
    slot: "active",
    props: surfaceValues,
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
  return new AgentStore({
    list,
    listSources: vi.fn(async () => ({ attachments: [] })),
    listBuilds: vi.fn(async () => ({ builds: [] })),
    inspectDependencies: vi.fn(async () => ({
      agent_id: "7db3745e-6f77-4b92-929c-4d2292fb3708",
      source_attachments: [],
      build_ids: [],
      blocks_delete: false,
    })),
  } as unknown as AgentClient);
}

const sourceClient = {
  list: vi.fn(async () => []),
} as unknown as SourceClient;


it("keeps exact selected-agent context across the operations hub and immutable build lineage", async () => {
  const selected = agent();
  const agentRef = `agent-${selected.id.replaceAll("-", "").slice(0, 20)}`;
  const buildId = "4bf642f8-18d2-45a9-8a77-b6d293a4fd7a";
  const client = {
    list: vi.fn(async () => ({ agents: [selected] })),
    listSources: vi.fn(async () => ({ attachments: [] })),
    inspectDependencies: vi.fn(async () => ({
      agent_id: selected.id,
      source_attachments: [],
      build_ids: [buildId],
      blocks_delete: true,
    })),
    listBuilds: vi.fn(async () => ({
      builds: [{
        build_id: buildId,
        agent_id: selected.id,
        agent_version: 1,
        created_at: "2026-08-08T00:00:00Z",
        source_references: [{
          source_id: "source-ready-001",
          source_revision_id: "revision-ready01",
          display_name: "Ready API",
          available: true,
        }],
      }],
    })),
  } as unknown as AgentClient;
  const store = new AgentStore(client);
  const dispatch = vi.fn(async (affordance: string) => completed(`agents.${affordance}`, "opened"));
  render(
    <AgentsHomeSurface
      {...props("agents.home", dispatch, {
        selected_agent_ref: agentRef,
        selected_agent_area: "builds",
      })}
      store={store}
      sourceClient={sourceClient}
    />,
  );

  expect(await screen.findByRole("region", { name: "Agent Builds" })).toHaveTextContent(buildId);
  expect(screen.getByText("Revision revision-ready01")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Open source revision" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith(
    "open_build_source_revision",
    {
      agent_ref: agentRef,
      build_id: buildId,
      source_id: "source-ready-001",
      source_revision_id: "revision-ready01",
    },
  ));
});


it("opens Operations from the active selected-Agent hub", async () => {
  const selected = agent();
  const agentRef = `agent-${selected.id.replaceAll("-", "").slice(0, 20)}`;
  const store = storeWith(vi.fn(async () => ({ agents: [selected] })));
  const dispatch = vi.fn(async () => completed("agents.open_operations", "opened"));
  render(
    <AgentsHomeSurface
      {...props("agents.home", dispatch, {
        selected_agent_ref: agentRef,
        selected_agent_area: "hub",
      })}
      store={store}
      sourceClient={sourceClient}
    />,
  );

  const operations = await screen.findByRole("button", { name: "Operations" });
  await waitFor(() => expect(operations).toBeEnabled());
  fireEvent.click(operations);
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("open_operations", {
    agent_ref: agentRef,
  }));
});


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
    selectedId: null,
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

  fireEvent.input(screen.getByLabelText("Name"), {
    target: { value: "Research Agent" },
  });
  fireEvent.input(screen.getByLabelText("Description"), {
    target: { value: "Researches tasks" },
  });
  fireEvent.input(screen.getByLabelText("Instructions"), {
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

it("preserves an in-progress Agent draft across a normal surface remount", async () => {
  const store = storeWith(vi.fn(async () => ({ agents: [] })));
  const dispatch = vi.fn(async () => completed("agents.create_agent", "created"));
  const first = render(<CreateAgentSurface {...props("agents.create", dispatch)} store={store} />);

  fireEvent.input(screen.getByLabelText("Name"), {
    target: { value: "Horizontal Store Agent" },
  });
  fireEvent.input(screen.getByLabelText("Description"), {
    target: { value: "Runs the complete lifecycle." },
  });
  fireEvent.input(screen.getByLabelText("Instructions"), {
    target: { value: "Use the exact user request." },
  });
  first.unmount();

  render(<CreateAgentSurface {...props("agents.create", dispatch)} store={store} />);
  expect(screen.getByLabelText("Name")).toHaveValue("Horizontal Store Agent");
  expect(screen.getByLabelText("Description")).toHaveValue("Runs the complete lifecycle.");
  expect(screen.getByLabelText("Instructions")).toHaveValue("Use the exact user request.");
  fireEvent.click(screen.getByRole("button", { name: "Create agent" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("create_agent", {
    name: "Horizontal Store Agent",
    description: "Runs the complete lifecycle.",
    instructions: "Use the exact user request.",
  }));
});

it("merges rapid field-level Agent draft updates before a remount", () => {
  const store = storeWith(vi.fn(async () => ({ agents: [] })));

  store.updateCreateDraft({ name: "Horizontal Store Agent" });
  store.updateCreateDraft({ description: "Runs the complete lifecycle." });
  store.updateCreateDraft({ instructions: "Use the exact user request." });

  expect(store.createDraft()).toEqual({
    name: "Horizontal Store Agent",
    description: "Runs the complete lifecycle.",
    instructions: "Use the exact user request.",
  });
});

it("publishes a late old-surface draft event to the currently mounted Agent form", () => {
  const store = storeWith(vi.fn(async () => ({ agents: [] })));
  const dispatch = vi.fn(async () => completed("agents.create_agent", "created"));
  const oldSurface = render(<CreateAgentSurface {...props("agents.create", dispatch)} store={store} />);
  const currentSurface = render(<CreateAgentSurface {...props("agents.create", dispatch)} store={store} />);

  fireEvent.input(within(oldSurface.container).getByLabelText("Name"), {
    target: { value: "Late Agent Draft" },
  });

  expect(currentSurface.container.querySelector('input[name="name"]')).toHaveValue("Late Agent Draft");
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
  const dispatch = vi.fn(async (affordance: string) =>
    affordance === "select_agent"
      ? completed("agents.select_agent", "selected")
      : completed("agents.save_changes", "saved"),
  );
  render(<AgentsHomeSurface {...props("agents.home", dispatch)} store={store} sourceClient={sourceClient} />);

  fireEvent.click(await screen.findByRole("button", { name: /Research Agent/ }));
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


it("sends the exact canonical Agent handle and ready Source id through the attach affordance", async () => {
  const selected = agent();
  const list = vi.fn(async () => ({ agents: [selected] }));
  const inspectDependencies = vi.fn(async () => ({
    agent_id: selected.id,
    source_attachments: [],
    blocks_delete: false,
  }));
  const store = new AgentStore({
    list,
    listSources: vi.fn(async () => ({ attachments: [] })),
    inspectDependencies,
  } as unknown as AgentClient);
  const source = {
    source_id: "source-ready-001",
    connector_key: "api",
    display_name: "Ready API",
    created_at: "2026-08-07T00:00:00Z",
    updated_at: "2026-08-07T00:00:00Z",
    revision: {
      revision_id: "revision-ready01",
      source_id: "source-ready-001",
      original_filename: "ready.yaml",
      content_sha256: "a".repeat(64),
      description_filename: null,
      description_sha256: null,
      job_id: "00000000-0000-0000-0000-000000000001",
      state: "ready" as const,
      created_at: "2026-08-07T00:00:00Z",
      updated_at: "2026-08-07T00:00:00Z",
      summary: {},
      failure_code: null,
      failure_message: null,
    },
  };
  const sources = { list: vi.fn(async () => [source]) } as unknown as SourceClient;
  const dispatch = vi.fn(async (affordance: string) =>
    affordance === "select_agent"
      ? completed("agents.select_agent", "selected")
      : completed("agents.attach_source", "attached"),
  );
  const agentRef = `agent-${selected.id.replaceAll("-", "").slice(0, 20)}`;
  render(
    <AgentsHomeSurface
      {...props("agents.home", dispatch, { selected_agent_ref: agentRef })}
      store={store}
      sourceClient={sources}
    />,
  );

  fireEvent.click(await screen.findByRole("button", { name: /Research Agent/ }));
  await screen.findByRole("option", { name: "Ready API" });
  fireEvent.change(screen.getByLabelText("Ready Workspace Source"), {
    target: { value: source.source_id },
  });
  fireEvent.click(screen.getByRole("button", { name: "Attach Source" }));

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("attach_source", {
    agent_ref: agentRef,
    source_id: source.source_id,
  }));
  await waitFor(() => expect(inspectDependencies).toHaveBeenCalledTimes(2));
});


it("requests required archive review for the exact selected Agent handle", async () => {
  const selected = agent();
  const list = vi.fn(async () => ({ agents: [selected] }));
  const store = new AgentStore({
    list,
    listSources: vi.fn(async () => ({ attachments: [] })),
    inspectDependencies: vi.fn(async () => ({
      agent_id: selected.id,
      source_attachments: [],
      blocks_delete: false,
    })),
  } as unknown as AgentClient);
  const dispatch = vi.fn(async (affordance: string) =>
    affordance === "select_agent"
      ? completed("agents.select_agent", "selected")
      : requiresReview(`agents.${affordance}`),
  );
  const agentRef = `agent-${selected.id.replaceAll("-", "").slice(0, 20)}`;
  render(
    <AgentsHomeSurface
      {...props("agents.home", dispatch, { selected_agent_ref: agentRef })}
      store={store}
      sourceClient={sourceClient}
    />,
  );

  const archive = await screen.findByRole("button", { name: "Archive Agent" });
  await waitFor(() => expect(archive).toBeEnabled());
  fireEvent.click(archive);

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("archive_agent", {
    agent_ref: agentRef,
  }));
  expect(screen.queryByText(/could not prepare/i)).not.toBeInTheDocument();
});


it("shows current blockers and sends explicit deletion to the authoritative guard", async () => {
  const selected = agent();
  const list = vi.fn(async () => ({ agents: [selected] }));
  const inspectDependencies = vi.fn(async () => ({
    agent_id: selected.id,
    source_attachments: [{
      source_id: "source-ready-001",
      source_revision_id: "revision-ready01",
    }],
    blocks_delete: true,
  }));
  const store = new AgentStore({
    list,
    listSources: vi.fn(async () => ({ attachments: [] })),
    inspectDependencies,
  } as unknown as AgentClient);
  const agentRef = `agent-${selected.id.replaceAll("-", "").slice(0, 20)}`;
  const publicMessage = "Delete is blocked by 1 Source attachment. The Agent and every dependency remain unchanged.";
  const dispatch = vi.fn(async () => failed("agents.delete_agent", "agent_dependency_conflict", publicMessage));
  render(
    <AgentsHomeSurface
      {...props("agents.home", dispatch, { selected_agent_ref: agentRef })}
      store={store}
      sourceClient={sourceClient}
    />,
  );

  expect(await screen.findByText("Delete blocked: 1 Source attachment remains.")).toBeVisible();
  const deletion = screen.getByRole("button", { name: "Delete permanently" });
  expect(deletion).toBeEnabled();
  fireEvent.click(deletion);
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("delete_agent", {
    agent_ref: agentRef,
  }));
  await waitFor(() => expect(inspectDependencies).toHaveBeenCalledTimes(2));
  expect(await screen.findByRole("alert")).toHaveTextContent(publicMessage);
});


it("refreshes persisted inventory after accepted archive and delete reviews", async () => {
  const selected = agent();
  for (const item of [
    { id: "agents.archive_review" as const, accept: "Archive Agent", outcome: "archived" },
    { id: "agents.delete_review" as const, accept: "Delete Agent permanently", outcome: "deleted" },
  ]) {
    const list = vi.fn()
      .mockResolvedValueOnce({ agents: [selected] })
      .mockResolvedValueOnce({ agents: [] });
    const store = new AgentStore({
      list,
      listSources: vi.fn(async () => ({ attachments: [] })),
      inspectDependencies: vi.fn(async () => ({
        agent_id: selected.id,
        source_attachments: [],
        blocks_delete: false,
      })),
    } as unknown as AgentClient);
    await store.refresh();
    store.select(selected.id);
    await store.refreshDependencies(selected.id);
    const result = completed(
      item.id === "agents.archive_review" ? "agents.archive_agent" : "agents.delete_agent",
      item.outcome,
    );
    const rendered = await renderRouteDeckComponent(
      <AgentLifecycleReviewSurface
        {...props(item.id, vi.fn(), {
          state: "pending",
          review_id: `accepted-${item.id}`,
          expires_at: "2026-08-07T12:00:00Z",
        })}
        store={store}
      />,
      {
        contract: frameworkContractFixture(),
        projection: frameworkProjectionFixture(),
        dispatchResult: result,
      },
    );

    fireEvent.click(screen.getByRole("button", { name: item.accept }));
    await waitFor(() => expect(list).toHaveBeenCalledTimes(2));
    expect(store.snapshot().agents).toEqual([]);
    expect(store.snapshot().selectedId).toBeNull();
    rendered.dispose();
  }
});


it("refreshes authoritative state after a rejected review without mutating the selected Agent", async () => {
  const selected = agent();
  const list = vi.fn(async () => ({ agents: [selected] }));
  const inspectDependencies = vi.fn(async () => ({
    agent_id: selected.id,
    source_attachments: [],
    blocks_delete: false,
  }));
  const store = new AgentStore({
    list,
    listSources: vi.fn(async () => ({ attachments: [] })),
    inspectDependencies,
  } as unknown as AgentClient);
  await store.refresh();
  store.select(selected.id);
  await store.refreshDependencies(selected.id);
  const rendered = await renderRouteDeckComponent(
    <AgentLifecycleReviewSurface
      {...props("agents.archive_review", vi.fn(), {
        state: "pending",
        review_id: "rejected-agents.archive_review",
        expires_at: "2026-08-07T12:00:00Z",
      })}
      store={store}
    />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
      dispatchResult: reviewRejected("agents.archive_agent"),
    },
  );

  fireEvent.click(screen.getByRole("button", { name: "Keep Agent unchanged" }));

  await waitFor(() => expect(list).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(inspectDependencies).toHaveBeenCalledTimes(2));
  expect(store.snapshot()).toMatchObject({
    agents: [selected],
    selectedId: selected.id,
    error: null,
  });
  rendered.dispose();
});


it("keeps an accept-time dependency race visible after the stale review surface disappears", async () => {
  const selected = agent();
  const agentRef = `agent-${selected.id.replaceAll("-", "").slice(0, 20)}`;
  const list = vi.fn(async () => ({ agents: [selected] }));
  const inspectDependencies = vi.fn()
    .mockResolvedValueOnce({
      agent_id: selected.id,
      source_attachments: [],
      blocks_delete: false,
    })
    .mockResolvedValue({
      agent_id: selected.id,
      source_attachments: [{
        source_id: "source-raced-001",
        source_revision_id: "revision-raced01",
      }],
      blocks_delete: true,
    });
  const store = new AgentStore({
    list,
    listSources: vi.fn(async () => ({ attachments: [] })),
    inspectDependencies,
  } as unknown as AgentClient);
  await store.refresh();
  store.select(selected.id);
  await store.refreshDependencies(selected.id);
  const publicMessage = "Delete is blocked because the Agent's dependencies changed. The Agent and every dependency remain unchanged.";
  const home = (
    <AgentsHomeSurface
      {...props("agents.home", vi.fn(), { selected_agent_ref: agentRef })}
      store={store}
      sourceClient={sourceClient}
    />
  );
  const rendered = await renderRouteDeckComponent(
    <>
      {home}
      <AgentLifecycleReviewSurface
        {...props("agents.delete_review", vi.fn(), {
          state: "pending",
          review_id: "stale-agents.delete_review",
          expires_at: "2026-08-07T12:00:00Z",
        })}
        store={store}
      />
    </>,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
      dispatchResult: failedDisposition(
        "agents.delete_agent",
        "review_stale",
        publicMessage,
      ),
    },
  );
  await waitFor(() => expect(store.snapshot().dependencies).not.toBeNull());
  const dependencyReadsBeforeAccept = inspectDependencies.mock.calls.length;

  fireEvent.click(screen.getByRole("button", { name: "Delete Agent permanently" }));

  await waitFor(() => {
    expect(inspectDependencies.mock.calls.length).toBeGreaterThan(dependencyReadsBeforeAccept);
    expect(store.snapshot().error).toBe(publicMessage);
  });
  expect(store.snapshot().selectedId).toBe(selected.id);
  expect(store.snapshot().agents).toEqual([selected]);

  rendered.rerender(home);
  expect(screen.queryByRole("heading", { name: "Confirm permanent deletion" })).not.toBeInTheDocument();
  expect(await screen.findByRole("alert")).toHaveTextContent(publicMessage);
  expect(screen.getByRole("heading", { name: selected.name })).toBeVisible();
  rendered.dispose();
});


it("reconstructs exact archive and delete review copy from persisted surface identity", async () => {
  const selected = agent();
  const cases = [
    {
      id: "agents.archive_review" as const,
      title: "Confirm archive",
      accept: "Archive Agent",
      consequence: /removes this Agent from the active inventory while preserving/i,
    },
    {
      id: "agents.delete_review" as const,
      title: "Confirm permanent deletion",
      accept: "Delete Agent permanently",
      consequence: /Permanent deletion is irreversible/i,
    },
  ];
  for (const item of cases) {
    const store = new AgentStore({
      list: vi.fn(async () => ({ agents: [selected] })),
      listSources: vi.fn(async () => ({ attachments: [] })),
      inspectDependencies: vi.fn(async () => ({
        agent_id: selected.id,
        source_attachments: [],
        blocks_delete: false,
      })),
    } as unknown as AgentClient);
    await store.refresh();
    store.select(selected.id);
    await store.refreshDependencies(selected.id);
    const rendered = await renderRouteDeckComponent(
      <AgentLifecycleReviewSurface
        {...props(item.id, vi.fn(), {
          state: "pending",
          review_id: `review-${item.id}`,
          expires_at: "2026-08-07T12:00:00Z",
        })}
        store={store}
      />,
      {
        contract: frameworkContractFixture(),
        projection: frameworkProjectionFixture(),
      },
    );
    expect(screen.getByRole("heading", { name: item.title })).toBeVisible();
    expect(screen.getByRole("button", { name: item.accept })).toBeEnabled();
    expect(screen.getByText(item.consequence)).toBeVisible();
    expect(screen.queryByText(/agents\.(archive|delete)_agent/)).not.toBeInTheDocument();
    rendered.dispose();
  }
});


it("keeps stable hook order while lifecycle review props move empty to pending and back", async () => {
  const selected = agent();
  const store = new AgentStore({
    list: vi.fn(async () => ({ agents: [selected] })),
    listSources: vi.fn(async () => ({ attachments: [] })),
    inspectDependencies: vi.fn(async () => ({
      agent_id: selected.id,
      source_attachments: [],
      blocks_delete: false,
    })),
  } as unknown as AgentClient);
  await store.refresh();
  store.select(selected.id);
  await store.refreshDependencies(selected.id);
  const empty = (
    <AgentLifecycleReviewSurface
      {...props("agents.archive_review", vi.fn(), {})}
      store={store}
    />
  );
  const pending = (
    <AgentLifecycleReviewSurface
      {...props("agents.archive_review", vi.fn(), {
        state: "pending",
        review_id: "transitioning-agents.archive_review",
        expires_at: "2026-08-07T12:00:00Z",
      })}
      store={store}
    />
  );
  const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);
  const rendered = await renderRouteDeckComponent(empty, {
    contract: frameworkContractFixture(),
    projection: frameworkProjectionFixture(),
    dispatchResult: completed("agents.archive_agent", "archived"),
  });

  try {
    expect(screen.queryByRole("heading", { name: "Confirm archive" })).not.toBeInTheDocument();
    rendered.rerender(pending);
    expect(screen.getByRole("heading", { name: "Confirm archive" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Archive Agent" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Keep Agent unchanged" })).toBeEnabled();
    rendered.rerender(empty);
    expect(screen.queryByRole("heading", { name: "Confirm archive" })).not.toBeInTheDocument();
    expect(consoleError).not.toHaveBeenCalledWith(
      expect.stringContaining("change in the order of Hooks"),
    );
  } finally {
    consoleError.mockRestore();
    rendered.dispose();
  }
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


function requiresReview(operationId: string): RouteDeckDispatchResult {
  return {
    disposition: "requires_review",
    operation_id: operationId,
    request_id: "agent-lifecycle-request",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface",
      phases: ["received", "review_staged"],
      attempt_id: "agent-lifecycle-attempt",
      request_fingerprint: "agent-lifecycle-fingerprint",
      delivery_phase: null,
      result_id: null,
      result_fingerprint: null,
    },
    review: {
      id: "agent-lifecycle-review",
      expires_at: "2026-08-07T12:00:00Z",
    },
    outcome: null,
    failure: null,
  };
}


function failed(operationId: string, code: string, message: string): RouteDeckDispatchResult {
  return {
    disposition: "blocked",
    operation_id: operationId,
    request_id: "agent-lifecycle-blocked-request",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface",
      phases: ["received"],
      attempt_id: "agent-lifecycle-blocked-attempt",
      request_fingerprint: "agent-lifecycle-blocked-fingerprint",
      delivery_phase: null,
      result_id: null,
      result_fingerprint: null,
    },
    review: null,
    outcome: null,
    failure: {
      kind: "guard",
      code,
      phase: "agents_lifecycle_guard",
      correlation_id: "agent-lifecycle-blocked-attempt",
      operation_id: operationId,
      request_id: "agent-lifecycle-blocked-request",
      public_message: message,
      recovery_directive: null,
      safe_details: {},
    },
  };
}


function failedDisposition(
  operationId: string,
  code: string,
  message: string,
): RouteDeckDispatchResult {
  return {
    ...failed(operationId, code, message),
    disposition: "failed",
  };
}


function reviewRejected(operationId: string): RouteDeckDispatchResult {
  return failedDisposition(
    operationId,
    "review_rejected",
    "The review was rejected. The Agent remains unchanged.",
  );
}
