import persistedDesignState from "../../design-state.json"
import { describe, expect, it } from "vitest"

import { createSeedState } from "@/workbench/seed"
import type { WorkbenchState } from "@/workbench/types"

const EXPECTED_BEHAVIORS: Readonly<Record<string, readonly string[]>> = {
  "agent-designer": [
    "agent-designer-resolve-source-inputs",
    "agent-designer-propose",
    "agent-designer-generate-feature",
    "agent-designer-customize",
    "agent-designer-inspect-navgraph",
    "agent-designer-review",
    "agent-designer-request-build",
    "deployed-agent-clarification",
  ],
  "builder-sandbox": [
    "builder-assemble",
    "builder-observe-lifecycle",
    "builder-resolve-prerequisites",
    "builder-control-runtime",
    "builder-generate-evalset",
    "sandbox-start-run",
    "sandbox-continue-clarification",
    "sandbox-inspect-routedeck",
    "sandbox-inspect-operation-trace",
  ],
  evaluation: [
    "evaluation-resolve-missing-build",
    "evaluation-generate-evalset",
    "evaluation-create-case",
    "evaluation-manage-cases",
    "evaluation-run-build",
    "evaluation-observe-lifecycle",
  ],
  "channels-deployment": [
    "channels-create-hosted-web",
    "channels-view-hosted-address",
    "channels-resolve-missing-eligibility",
    "channels-link-custom-domain",
    "deployment-publish-eligible-build",
    "deployment-observe-lifecycle",
    "deployment-rollback",
    "channels-set-availability",
    "channels-use-hosted-agent",
  ],
  operations: [
    "operations-view-interactions",
    "operations-inspect-evidence",
    "operations-promote-evaluation",
  ],
}

function behaviorIds(state: WorkbenchState, featureId: string): string[] {
  const feature = state.features.find((item) => item.id === featureId)
  if (feature === undefined) throw new Error(`Missing Studio feature ${featureId}`)
  return feature.stories.map((story) => story.id)
}

describe("launch behavior-note coverage", () => {
  it("models every later launch feature as explicit reviewable behaviors", () => {
    const seed = createSeedState()
    for (const [featureId, expected] of Object.entries(EXPECTED_BEHAVIORS)) {
      expect(behaviorIds(seed, featureId), featureId).toEqual(expected)
    }
  })

  it("keeps the accepted persisted Studio state aligned with the seed", () => {
    for (const [featureId, expected] of Object.entries(EXPECTED_BEHAVIORS)) {
      expect(behaviorIds(persistedDesignState as WorkbenchState, featureId), featureId).toEqual(expected)
    }
  })

  it("gives every accepted behavior a normal-path evaluation contract", () => {
    const state = persistedDesignState as WorkbenchState
    for (const featureId of Object.keys(EXPECTED_BEHAVIORS)) {
      const feature = state.features.find((item) => item.id === featureId)!
      for (const story of feature.stories.filter((item) => item.status === "approved")) {
        expect(
          story.behaviorEvals.some((evaluation) => evaluation.enabled && evaluation.coverage.includes("normal")),
          `${feature.name} / ${story.title}`,
        ).toBe(true)
      }
    }
  })
})
