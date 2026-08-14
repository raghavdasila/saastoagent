import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@routedeck/react", () => ({
  NavGraphInspector: ({ contract, showMiniMap }: { readonly contract: { readonly nodes: Readonly<Record<string, { readonly title: string }>>; readonly transitions: readonly unknown[] }; readonly showMiniMap?: boolean }) => <section data-routedeck-inspector="read-only" data-mini-map={String(showMiniMap)}>
    <div data-routedeck-navgraph-canvas="" />
    <span>{Object.keys(contract.nodes).length} nodes · {contract.transitions.length} transitions</span>
    {Object.values(contract.nodes).map((node) => <strong key={node.title}>{node.title}</strong>)}
  </section>,
}));

import { BuildNavGraph } from "@/shared/agent/BuildNavGraph";
import type { AgentBuildView } from "@/features/builder/models";


describe("immutable Agent build NavGraph", () => {
  it("renders the exact persisted frontend contract through RouteDeck's real inspector", async () => {
    const build: AgentBuildView = {
      id: "build-1", agent_id: "agent-1", build_request_id: "request-1", design_revision_id: "design-1",
      agent_version: 2, attempt_number: 1, status: "ready", runtime_lifecycle: "running", runtime_build_hash: "r".repeat(64), model: "model", model_digest: "digest",
      allowed_operation_ids: ["PostCarts"], navgraph_hash: "n".repeat(64), frontend_contract: {
        name: "corpus-agent-build-1",
        entry_node_id: "agent_runtime.home",
        nodes: {
          "agent_runtime.home": {
            id: "agent_runtime.home",
            title: "Answers product taxonomy questions from an approved API.",
            route_template: "/",
            deep_link_policy: "shareable",
            conversation_input: { enabled: true, disabled_message: null },
            operation_ids: ["agent_runtime.tool.post"],
            surfaces: { active: "agent_runtime.home", error: ["agent_runtime.delivery_status"] },
          },
        },
        surfaces: {
          "agent_runtime.home": { id: "agent_runtime.home", component: "agent_runtime.home", lifecycle: "stable", public_props_schema: {}, affordances: [] },
          "agent_runtime.delivery_status": { id: "agent_runtime.delivery_status", component: "agent_runtime.delivery_status", lifecycle: "stable", public_props_schema: {}, affordances: [] },
        },
        transitions: [{ source: "agent_runtime.home", target: "agent_runtime.home", operation_id: "agent_runtime.tool.post", outcome: "observed" }],
      },
      compiled_navgraph: {
        entry_node: { id: "agent_runtime.home" },
        nodes: [{
          id: "agent_runtime.home", title: "Answers product taxonomy questions from an approved API.",
          operations: [{ id: "agent_runtime.tool.post", title: "Create cart", safety_class: "write_external", review_policy: "required", public_metadata: { source_operation_id: "PostCarts", method: "POST", path_template: "/store/carts" } }],
          capabilities: [{ id: "agent_runtime.capability.store", title: "Store tools", operations: [{ id: "agent_runtime.tool.post" }] }], policy_refs: [{ id: "agent_runtime.policy.1" }], suggested_actions: [], surfaces: { active: "agent_runtime.home", error: ["agent_runtime.delivery_status"] },
          public_metadata: { designer_topology: { topology_hash: "t".repeat(64) } },
        }],
        transitions: [{ source: { id: "agent_runtime.home" }, target: { id: "agent_runtime.home" }, operation: { id: "agent_runtime.tool.post" }, outcome: "observed" }],
      },
      failure_code: null, failure_message: null, created_at: "2026-08-08T00:00:00Z", updated_at: "2026-08-08T00:00:00Z",
    };

    render(<BuildNavGraph build={build} />);

    expect(screen.getByRole("region", { name: "RouteDeck NavGraph for build build-1" })).toBeVisible();
    await waitFor(() => expect(document.querySelector("[data-routedeck-inspector='read-only']")).toBeInTheDocument());
    expect(document.querySelector("[data-routedeck-navgraph-canvas]")).toBeInTheDocument();
    expect(screen.getAllByText("Agent home").length).toBeGreaterThan(0);
    expect(document.querySelector("[data-routedeck-inspector='read-only']")).toHaveAttribute("data-mini-map", "false");
    expect(screen.getByText("1 nodes · 1 transitions")).toBeVisible();
    expect(screen.getByText("PostCarts")).toBeVisible();
    expect(screen.getByText("POST /store/carts")).toBeVisible();
    expect(screen.getByText("API change · owner review required")).toBeVisible();
    expect(screen.getByText("Store tools")).toBeVisible();
    expect(screen.getByLabelText("Compiled Agent map summary")).toHaveTextContent("Runtime areas1Transitions1Capabilities1Supervised tools1Policies1Surfaces2");
    expect(screen.getByText("Designer topology").parentElement).toHaveTextContent("tttttttttttttttt");
  });

  it("fails visibly instead of substituting the compiled document when the frontend contract is invalid", () => {
    const build = {
      id: "build-invalid", agent_id: "agent-1", build_request_id: "request-1", design_revision_id: "design-1",
      agent_version: 2, attempt_number: 1, status: "ready", runtime_lifecycle: "running", runtime_build_hash: "r".repeat(64), model: "model", model_digest: "digest",
      allowed_operation_ids: ["PostCarts"], navgraph_hash: "n".repeat(64), frontend_contract: { nodes: {} },
      compiled_navgraph: { nodes: [], transitions: [] }, failure_code: null, failure_message: null,
      created_at: "2026-08-08T00:00:00Z", updated_at: "2026-08-08T00:00:00Z",
    } satisfies AgentBuildView;

    render(<BuildNavGraph build={build} />);

    expect(screen.getByRole("alert")).toHaveTextContent("exact RouteDeck frontend contract is unavailable");
    expect(document.querySelector("[data-routedeck-navgraph-canvas]")).not.toBeInTheDocument();
  });
});
