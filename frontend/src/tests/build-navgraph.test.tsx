import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BuildNavGraph } from "@/features/builder/BuildNavGraph";
import type { AgentBuildView } from "@/features/builder/models";


describe("immutable Agent build NavGraph", () => {
  it("renders the RouteDeck node, tool contract, safety, review, and hash", () => {
    const build: AgentBuildView = {
      id: "build-1", agent_id: "agent-1", build_request_id: "request-1", design_revision_id: "design-1",
      agent_version: 2, status: "ready", runtime_build_hash: "r".repeat(64), model: "model", model_digest: "digest",
      allowed_operation_ids: ["PostCarts"], navgraph_hash: "n".repeat(64), frontend_contract: { nodes: {} },
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
    const graph = screen.getByRole("img", { name: "1 NavGraph nodes and 1 transitions" });
    expect(graph).toBeVisible();
    expect(graph.querySelector("rect")).toHaveAttribute("width", "500");
    expect(graph.querySelector("foreignObject .build-navgraph__title")).toHaveTextContent("Answers product taxonomy questions from an approved API.");
    expect(graph).toHaveTextContent("Answers product taxonomy questions from an approved API.");
    expect(screen.getByText("PostCarts")).toBeVisible();
    expect(screen.getByText("POST /store/carts")).toBeVisible();
    expect(screen.getByText("write_external · review required")).toBeVisible();
    expect(screen.getByText("Store tools")).toBeVisible();
    expect(screen.getByText("Designer topology").parentElement).toHaveTextContent("tttttttttttttttt");
  });
});
