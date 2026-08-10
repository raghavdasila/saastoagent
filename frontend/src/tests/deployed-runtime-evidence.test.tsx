import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";

import { DeployedRuntimeEvidence } from "@/features/operations/DeployedRuntimeEvidence";
import type { AgentBuildView, OperationsInteractionView } from "@/features/builder/models";

it("shows the exact deployed build NavGraph and ToolRouter clarification evidence to the owner", () => {
  const build: AgentBuildView = {
    id: "build-deployed", agent_id: "agent-1", build_request_id: "request-1", design_revision_id: "design-1",
    agent_version: 1, status: "ready", runtime_build_hash: "r".repeat(64), model: "model", model_digest: "digest",
    allowed_operation_ids: ["GetProductTypesId"], navgraph_hash: "n".repeat(64), frontend_contract: { nodes: {} },
    compiled_navgraph: {
      entry_node: { id: "agent_runtime.home" },
      nodes: [{
        id: "agent_runtime.home", title: "Catalog Agent",
        operations: [{ id: "agent_runtime.tool.types", title: "Get product type", safety_class: "read_external", review_policy: "none", public_metadata: { source_operation_id: "GetProductTypesId", method: "GET", path_template: "/store/product-types/{id}" } }],
        capabilities: [{ id: "agent_runtime.capability.catalog", title: "Catalog", operations: [{ id: "agent_runtime.tool.types" }] }],
        policy_refs: [{ id: "agent_runtime.policy.1" }], suggested_actions: [], surfaces: { active: "agent_runtime.home", detail: ["agent_runtime.clarification"], status: ["agent_runtime.toolrouter_status"] },
        public_metadata: { designer_topology: { topology_hash: "t".repeat(64) } },
      }],
      transitions: [{ source: { id: "agent_runtime.home" }, target: { id: "agent_runtime.home" }, operation: { id: "agent_runtime.tool.types" }, outcome: "observed" }],
    },
    failure_code: null, failure_message: null, created_at: "2026-08-09T00:00:00Z", updated_at: "2026-08-09T00:00:00Z",
  };
  const interaction: OperationsInteractionView = {
    interaction_id: "interaction-1", agent_id: "agent-1", build_id: build.id, deployment_id: "deployment-1", session_id: "public-session-1",
    input_summary: "Show product type exact", output_summary: "Product type loaded", status: "succeeded",
    events: [
      { sequence: 1, kind: "router.decision", safe_data: { resolution: "route", operation_id: "GetProductTypesId", credential: "must-not-render" } },
      { sequence: 2, kind: "run.completed", safe_data: { status: "succeeded" } },
    ],
  };

  render(<DeployedRuntimeEvidence interaction={interaction} build={build} />);

  expect(screen.getByRole("region", { name: "Deployed RouteDeck evidence for interaction interaction-1" })).toBeVisible();
  expect(screen.getByRole("region", { name: "RouteDeck NavGraph for build build-deployed" })).toBeVisible();
  expect(screen.getByRole("region", { name: "Deployed ToolRouter clarification subagent" })).toBeVisible();
  expect(screen.getByText("ToolRouter resolution")).toBeVisible();
  expect(screen.getAllByText(/GetProductTypesId/)).toHaveLength(2);
  expect(screen.queryByText(/must-not-render/)).not.toBeInTheDocument();
});
