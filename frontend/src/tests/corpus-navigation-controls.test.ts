import { describe, expect, it } from "vitest";
import type {
  FrontendContract,
  RouteDeckProjectedSurface,
} from "@routedeck/core";

import { selectedAgentReturnForBack } from "../app/CorpusNavigationControls";

const contract = {
  surfaces: {
    "sources.api": {
      id: "sources.api",
      component: "sources.api",
      lifecycle: "stable",
      affordances: [
        { id: "return_to_agent", event: "open", operation: { id: "agents.return_from_source" } },
        { id: "return_to_builder", event: "open", operation: { id: "agents.open_builds" } },
      ],
    },
    "designer.home": {
      id: "designer.home",
      component: "designer.home",
      lifecycle: "stable",
      affordances: [
        { id: "return_to_agent", event: "open", operation: { id: "designer.return_to_agent" } },
      ],
    },
  },
} as unknown as FrontendContract;

function surface(
  surfaceId: "sources.api" | "designer.home",
  name: "return_agent_ref" | "selected_agent_ref",
): RouteDeckProjectedSurface {
  return {
    surface_id: surfaceId,
    component: surfaceId,
    props: [{ name, value: "agent-public-ref" }],
  };
}

describe("selected-Agent Back continuity", () => {
  it("uses the Source handoff operation when canonical Back targets the Agent hub", () => {
    expect(selectedAgentReturnForBack(
      "agents.home",
      surface("sources.api", "return_agent_ref"),
      contract,
    )).toEqual({
      operationId: "agents.return_from_source",
      argumentsValue: { agent_ref: "agent-public-ref" },
    });
  });

  it("uses the exact Builder return when Source was opened from a build", () => {
    expect(selectedAgentReturnForBack(
      "builder.home",
      surface("sources.api", "return_agent_ref"),
      contract,
    )).toEqual({
      operationId: "agents.open_builds",
      argumentsValue: { agent_ref: "agent-public-ref" },
    });
  });

  it("uses each selected-Agent surface's declared return operation", () => {
    expect(selectedAgentReturnForBack(
      "agents.home",
      surface("designer.home", "selected_agent_ref"),
      contract,
    )).toEqual({
      operationId: "designer.return_to_agent",
      argumentsValue: { agent_ref: "agent-public-ref" },
    });
  });

  it("leaves ordinary canonical navigation unchanged", () => {
    expect(selectedAgentReturnForBack(
      "workspace.home",
      surface("designer.home", "selected_agent_ref"),
      contract,
    )).toBeNull();
  });

  it("fails closed when projected identity or the declared affordance is unavailable", () => {
    expect(selectedAgentReturnForBack(
      "agents.home",
      { surface_id: "designer.home", component: "designer.home", props: [] },
      contract,
    )).toBeNull();
    expect(selectedAgentReturnForBack(
      "agents.home",
      { ...surface("designer.home", "selected_agent_ref"), component: "wrong" },
      contract,
    )).toBeNull();
  });
});
