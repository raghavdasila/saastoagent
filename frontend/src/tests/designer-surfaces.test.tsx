import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import type { AgentClient } from "../features/agents/client";
import { AgentStore } from "../features/agents/store";
import type { DesignerClient } from "../features/designer/client";
import { DesignerSurface } from "../features/designer/DesignerSurface";
import type { AgentDesignView } from "../features/designer/models";
import { DesignerRefreshStore } from "../features/designer/refreshStore";


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
  };
  const get = vi.fn()
    .mockResolvedValueOnce(base)
    .mockResolvedValue({ ...base, accepted_revision_id: revisionId });
  const client = { get } as unknown as DesignerClient;
  const agentStore = new AgentStore({
    list: vi.fn(async () => ({ agents: [{ id: agentId, name: "Designer Agent", description: "", instructions: "Use curated tools.", lifecycle: "active", current_version: 1, created_at: "2026-08-08T00:00:00Z", updated_at: "2026-08-08T00:00:00Z" }] })),
    listSources: vi.fn(async () => ({ attachments: [] })),
    listBuilds: vi.fn(async () => ({ builds: [] })),
    inspectDependencies: vi.fn(async () => ({ agent_id: agentId, source_attachments: [], build_ids: [], blocks_delete: false })),
  } as unknown as AgentClient);
  const refreshStore = new DesignerRefreshStore();
  const dispatch = vi.fn(async () => ({ disposition: "completed", outcome: "requested", failure: null }));
  const surfaceProps = {
    surface: { surface_id: "designer.home", component: "designer.home", props: [] },
    slot: "active",
    props: { selected_agent_ref: agentRef },
    spec: { id: "designer.home", component: "designer.home", lifecycle: "stable", public_props_schema: {}, affordances: [] },
    dispatchAffordance: dispatch,
  } as unknown as RouteDeckSurfaceComponentProps;
  render(<DesignerSurface {...surfaceProps} agentStore={agentStore} client={client} refreshStore={refreshStore} />);

  expect(await screen.findByText("None")).toBeVisible();
  expect(screen.getByRole("region", { name: "Agent design blueprint" })).toBeVisible();
  expect(screen.getByRole("region", { name: "Proposed RouteDeck topology" })).toHaveTextContent("API Source");
  expect(screen.getByRole("region", { name: "Proposed RouteDeck topology" })).toHaveTextContent("GetProductTypes");
  expect(screen.getByRole("region", { name: "Immutable Source lineage" })).toHaveTextContent("Product taxonomy");
  expect(screen.getByRole("region", { name: "Immutable Source lineage" })).toHaveTextContent("revision-ready01");
  expect(screen.getByRole("region", { name: "Compiled RouteDeck NavGraph preview" })).toHaveTextContent("Taxonomy");
  const navGraph = screen.getByRole("img", { name: "1 proposed NavGraph nodes" });
  expect(navGraph).toBeVisible();
  expect(navGraph.querySelector("foreignObject .designer-navgraph__title")).toHaveTextContent("Serve store operators");
  expect(navGraph).toHaveTextContent("1 capabilities · 1 tools");
  expect(navGraph).not.toHaveTextContent("Â");
  expect(screen.getByRole("button", { name: "Request build" })).toBeDisabled();
  refreshStore.notify();
  await waitFor(() => expect(screen.getByText(revisionId)).toBeVisible());
  const request = screen.getByRole("button", { name: "Request build" });
  expect(request).toBeEnabled();
  fireEvent.click(request);
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("request_build", {
    agent_ref: agentRef,
    accepted_revision_id: revisionId,
  }));
});
