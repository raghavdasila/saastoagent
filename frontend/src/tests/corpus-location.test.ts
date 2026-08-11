import { describe, expect, it } from "vitest";

import { corpusLocation } from "../app/corpusLocation";

describe("Corpus feature location presentation", () => {
  it.each([
    ["agents.home", "Agents", "Corpus Agents"],
    ["designer.home", "Designer", "Agent Designer"],
    ["builder.home", "Builder", "Agent Builder"],
    ["sandbox.home", "Sandbox", "Agent Sandbox"],
    ["evaluation.home", "Evaluation", "Agent Evaluation"],
    ["channels.home", "Channels", "Channels and Deployment"],
    ["operations.home", "Operations", "Agent Operations"],
  ])("keeps %s visibly inside its owning feature", (nodeId, feature, title) => {
    expect(corpusLocation(nodeId)).toMatchObject({ feature, title });
  });
});
