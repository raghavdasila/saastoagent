import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import type { AgentClient } from "../features/agents/client";
import { AgentStore } from "../features/agents/store";
import type { DesignerClient } from "../features/designer/client";
import { DesignerSurface } from "../features/designer/DesignerSurface";
import type { AgentDesignView } from "../features/designer/models";
import { DesignerRefreshStore } from "../features/designer/refreshStore";

vi.mock("@routedeck/react", async (importOriginal) => {
  const original = await importOriginal<typeof import("@routedeck/react")>();
  return {
    ...original,
    NavGraphInspector: ({ contract }: { readonly contract: { readonly nodes: Readonly<Record<string, { readonly title: string }>>; readonly transitions: readonly unknown[] } }) => <section data-routedeck-inspector="read-only">
      <div data-routedeck-navgraph-canvas="" />
      <span>{Object.keys(contract.nodes).length} nodes · {contract.transitions.length} transitions</span>
      {Object.values(contract.nodes).map((node) => <strong key={node.title}>{node.title}</strong>)}
    </section>,
  };
});


it("adopts accepted design refresh and requests only that exact revision", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const revisionId = "5c1ad911-849f-4ef6-aadb-b2a793ac4ae0";
  const base: AgentDesignView = {
    agent_id: agentId,
    current_revision_id: revisionId,
    accepted_revision_id: null,
    revisions: [{
      id: revisionId,
      revision: 1,
      agent_version: 1,
      input_fingerprint: "a".repeat(64),
      content: { goal: "Serve store operators", instructions: "Use curated tools.", features: ["API Source"], behaviors: ["Answer taxonomy questions"], policies: ["Use exact inputs"], capabilities: ["Taxonomy: GetProductTypes"], tools: ["GetProductTypes"] },
      topology: {
        topology_hash: "t".repeat(64),
        entry_node_id: "agent_runtime.home",
        nodes: [{ id: "agent_runtime.home", title: "Serve store operators", capability_ids: ["agent_runtime.capability.taxonomy"], operation_ids: ["GetProductTypes"], surface_ids: ["agent_runtime.home", "agent_runtime.clarification", "agent_runtime.toolrouter_status", "agent_runtime.delivery_status"], policy_count: 2 }],
        capabilities: [{ id: "agent_runtime.capability.taxonomy", title: "Taxonomy", operation_ids: ["GetProductTypes"] }],
        operation_ids: ["GetProductTypes"],
      },
      source_inputs: [{
        source_id: "source-ready-001",
        source_revision_id: "revision-ready01",
        curation_id: "curation-ready1",
        semantic_groups: [{ label: "Product taxonomy", operation_ids: ["GetProductTypes"] }],
      }],
      created_at: "2026-08-08T00:00:00Z",
    }],
    build_request: null,
    current_inputs_ready: true,
    current_inputs_match: true,
  };
  const get = vi.fn()
    .mockResolvedValueOnce(base)
    .mockResolvedValueOnce({ ...base, accepted_revision_id: revisionId })
    .mockResolvedValue({
      ...base,
      accepted_revision_id: revisionId,
      build_request: {
        id: "build-request-exact",
        design_revision_id: revisionId,
        status: "pending",
        created_at: "2026-08-08T00:01:00Z",
      },
    });
  const client = { get } as unknown as DesignerClient;
  const agentStore = new AgentStore({
    list: vi.fn(async () => ({ agents: [{ id: agentId, name: "Designer Agent", description: "", instructions: "Use curated tools.", lifecycle: "active", current_version: 1, created_at: "2026-08-08T00:00:00Z", updated_at: "2026-08-08T00:00:00Z" }] })),
    listSources: vi.fn(async () => ({ attachments: [] })),
    listBuilds: vi.fn(async () => ({ builds: [] })),
    inspectDependencies: vi.fn(async () => ({ agent_id: agentId, source_attachments: [], build_ids: [], blocks_delete: false })),
  } as unknown as AgentClient);
  const refreshStore = new DesignerRefreshStore();
  const dispatch = vi.fn(async (affordance: string) => ({
    disposition: "completed",
    outcome: affordance === "continue_to_builds" ? "opened" : "requested",
    failure: null,
  }));
  const surfaceProps = {
    surface: { surface_id: "designer.home", component: "designer.home", props: [] },
    slot: "active",
    props: { selected_agent_ref: agentRef },
    spec: { id: "designer.home", component: "designer.home", lifecycle: "stable", public_props_schema: {}, affordances: [] },
    dispatchAffordance: dispatch,
  } as unknown as RouteDeckSurfaceComponentProps;
  render(<DesignerSurface {...surfaceProps} agentStore={agentStore} client={client} refreshStore={refreshStore} />);

  expect(await screen.findByText("Needs review")).toBeVisible();
  expect(screen.getByRole("region", { name: "Agent design blueprint" })).toBeVisible();
  fireEvent.click(screen.getByText("Review feature, capability, policy, and tool mapping"));
  expect(screen.getByRole("region", { name: "Proposed RouteDeck topology" })).toHaveTextContent("API Source");
  expect(screen.getByRole("region", { name: "Proposed RouteDeck topology" })).toHaveTextContent("GetProductTypes");
  fireEvent.click(screen.getByText("Inspect immutable Source lineage"));
  expect(screen.getByRole("region", { name: "Immutable Source lineage" })).toHaveTextContent("Product taxonomy");
  expect(screen.getByRole("region", { name: "Immutable Source lineage" })).toHaveTextContent("revision-ready01");
  expect(screen.getByRole("region", { name: "Proposed RouteDeck NavGraph preview" })).toHaveTextContent("Taxonomy");
  expect(document.querySelector("[data-routedeck-inspector='read-only']")).toBeInTheDocument();
  expect(document.querySelector("[data-routedeck-navgraph-canvas]")).toBeInTheDocument();
  expect(screen.getByText("1 nodes · 1 transitions")).toBeVisible();
  expect(screen.getByRole("button", { name: "Request build" })).toBeDisabled();
  refreshStore.notify();
  await waitFor(() => expect(screen.getByText("Accepted")).toBeVisible());
  const request = screen.getByRole("button", { name: "Request build" });
  expect(request).toBeEnabled();
  fireEvent.click(request);
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("request_build", {
    agent_ref: agentRef,
    accepted_revision_id: revisionId,
  }));
  const continueButton = await screen.findByRole("button", { name: "Continue to Builds" });
  fireEvent.click(continueButton);
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("continue_to_builds", {
    agent_ref: agentRef,
  }));
});


it("offers an immutable refresh when current Agent inputs changed and ignores an older build request", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const priorRevisionId = "5c1ad911-849f-4ef6-aadb-b2a793ac4ae0";
  const nextRevisionId = "875eb1f6-a6c4-4bc2-b444-eccbb9a63880";
  const content = { goal: "Serve store operators", instructions: "Use curated tools.", features: ["API Source"], behaviors: ["Answer taxonomy questions"], policies: ["Use exact inputs"], capabilities: ["Taxonomy: GetProductTypes"], tools: ["GetProductTypes"] };
  const topology = { topology_hash: "t".repeat(64), entry_node_id: "agent_runtime.home", nodes: [{ id: "agent_runtime.home", title: "Serve store operators", capability_ids: ["agent_runtime.capability.taxonomy"], operation_ids: ["GetProductTypes"], surface_ids: ["agent_runtime.home"], policy_count: 2 }], capabilities: [{ id: "agent_runtime.capability.taxonomy", title: "Taxonomy", operation_ids: ["GetProductTypes"] }], operation_ids: ["GetProductTypes"] };
  const stale: AgentDesignView = {
    agent_id: agentId,
    current_revision_id: priorRevisionId,
    accepted_revision_id: priorRevisionId,
    revisions: [{ id: priorRevisionId, revision: 1, agent_version: 1, input_fingerprint: "a".repeat(64), content, topology, source_inputs: [], created_at: "2026-08-08T00:00:00Z" }],
    build_request: { id: "old-build", design_revision_id: priorRevisionId, status: "failed", created_at: "2026-08-08T00:01:00Z" },
    current_inputs_ready: true,
    current_inputs_match: false,
  };
  const refreshed: AgentDesignView = {
    ...stale,
    current_revision_id: nextRevisionId,
    revisions: [...stale.revisions, { ...stale.revisions[0]!, id: nextRevisionId, revision: 2, input_fingerprint: "b".repeat(64) }],
    current_inputs_match: true,
  };
  const client = { get: vi.fn().mockResolvedValueOnce(stale).mockResolvedValue(refreshed) } as unknown as DesignerClient;
  const agentStore = new AgentStore({
    list: vi.fn(async () => ({ agents: [{ id: agentId, name: "Designer Agent", description: "", instructions: "Use curated tools.", lifecycle: "active", current_version: 1, created_at: "2026-08-08T00:00:00Z", updated_at: "2026-08-08T00:00:00Z" }] })),
    listSources: vi.fn(async () => ({ attachments: [] })),
    listBuilds: vi.fn(async () => ({ builds: [] })),
    inspectDependencies: vi.fn(async () => ({ agent_id: agentId, source_attachments: [], build_ids: [], blocks_delete: false })),
  } as unknown as AgentClient);
  const dispatch = vi.fn(async () => ({ disposition: "completed", outcome: "proposed", failure: null }));
  const surfaceProps = {
    surface: { surface_id: "designer.home", component: "designer.home", props: [] }, slot: "active", props: { selected_agent_ref: agentRef },
    spec: { id: "designer.home", component: "designer.home", lifecycle: "stable", public_props_schema: {}, affordances: [] }, dispatchAffordance: dispatch,
  } as unknown as RouteDeckSurfaceComponentProps;

  render(<DesignerSurface {...surfaceProps} agentStore={agentStore} client={client} refreshStore={new DesignerRefreshStore()} />);
  const update = await screen.findByRole("button", { name: "Update proposal from current inputs" });
  expect(screen.getByText("Agent inputs changed")).toBeVisible();
  expect(screen.getByRole("button", { name: "Review for approval" })).toBeDisabled();
  fireEvent.click(update);
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("propose", { agent_ref: agentRef }));
  await waitFor(() => expect(screen.getByText("Revision 2")).toBeVisible());
  expect(screen.getByText("Awaiting approval")).toBeVisible();
  expect(screen.getByRole("button", { name: "Request build" })).toBeDisabled();
  expect(screen.queryByRole("button", { name: "Continue to Builds" })).not.toBeInTheDocument();
});


it("turns missing design inputs into an exact attached Source handoff", async () => {
  const agentId = "cd4520ec-e89d-41fd-88bd-b16df8489116";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const sourceId = "source-ready-001";
  const sourceRevisionId = "revision-ready01";
  const agentStore = new AgentStore({
    list: vi.fn(async () => ({ agents: [{ id: agentId, name: "Shopping Agent", description: "", instructions: "Use curated tools.", lifecycle: "active", current_version: 1, created_at: "2026-08-11T00:00:00Z", updated_at: "2026-08-11T00:00:00Z" }] })),
    listSources: vi.fn(async () => ({ attachments: [{ source_id: sourceId, source_revision_id: sourceRevisionId, display_name: "Store API", attached_at: "2026-08-11T00:01:00Z" }] })),
    listBuilds: vi.fn(async () => ({ builds: [] })),
    inspectDependencies: vi.fn(async () => ({ agent_id: agentId, source_attachments: [{ source_id: sourceId, source_revision_id: sourceRevisionId }], build_ids: [], blocks_delete: true })),
  } as unknown as AgentClient);
  const dispatch = vi.fn(async () => ({ disposition: "completed", outcome: "opened", failure: null }));
  const surfaceProps = {
    surface: { surface_id: "designer.home", component: "designer.home", props: [] },
    slot: "active",
    props: { selected_agent_ref: agentRef },
    spec: { id: "designer.home", component: "designer.home", lifecycle: "stable", public_props_schema: {}, affordances: [] },
    dispatchAffordance: dispatch,
  } as unknown as RouteDeckSurfaceComponentProps;

  render(<DesignerSurface {...surfaceProps} agentStore={agentStore} client={{ get: vi.fn(async () => null) } as unknown as DesignerClient} refreshStore={new DesignerRefreshStore()} />);

  expect(await screen.findByRole("heading", { name: "Prepare the attached Sources" })).toBeVisible();
  expect(await screen.findByText("Store API")).toBeVisible();
  expect(screen.getByText(`API version ${sourceRevisionId}`)).toBeVisible();
  const open = screen.getByRole("button", { name: "Open Source setup" });
  fireEvent.click(open);
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("open_source_prerequisite", {
    agent_ref: agentRef,
    source_id: sourceId,
  }));
});
