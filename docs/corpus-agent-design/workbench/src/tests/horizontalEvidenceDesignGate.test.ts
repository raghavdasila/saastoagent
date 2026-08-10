import persistedDesignState from "../../design-state.json"
import { describe, expect, it } from "vitest"

import { createSeedState } from "@/workbench/seed"
import type { DesignFeature, WorkbenchState } from "@/workbench/types"

const HORIZONTAL_FEATURE_IDS = new Set([
  "workspace",
  "agents",
  "source-hub",
  "api-source",
  "agent-designer",
  "builder-sandbox",
  "evaluation",
  "channels-deployment",
  "operations",
])

const SENSITIVE_SURFACE_ONLY_OPERATIONS = new Set([
  "Save API connection",
])

const CHAT_OPERATIONS_WITH_EQUIVALENT_ALWAYS_VISIBLE_SURFACE = new Set([
  "Inspect current API architecture",
])

function horizontalFeatures(state: WorkbenchState): DesignFeature[] {
  return state.features.filter((feature) => HORIZONTAL_FEATURE_IDS.has(feature.id))
}

describe("horizontal chat, surface, and mixed evidence contract", () => {
  it("makes every non-sensitive operation available through chat and product surfaces", () => {
    for (const feature of horizontalFeatures(persistedDesignState as WorkbenchState)) {
      for (const story of feature.stories.filter((item) => item.status === "approved")) {
        for (const operation of story.operations) {
          const expected = SENSITIVE_SURFACE_ONLY_OPERATIONS.has(operation.name)
            ? "product-surface"
            : CHAT_OPERATIONS_WITH_EQUIVALENT_ALWAYS_VISIBLE_SURFACE.has(operation.name)
              ? "chat"
              : "both"
          expect(operation.availableThrough, `${feature.name} / ${story.title} / ${operation.name}`).toBe(expected)
        }
      }
    }
  })

  it("requires independent surface, chat, and mixed lifecycle evidence for every horizontal feature", () => {
    for (const feature of horizontalFeatures(persistedDesignState as WorkbenchState)) {
      const journeyIds = new Set(feature.productJourneyEvals.map((evaluation) => evaluation.id))
      expect(journeyIds, feature.name).toEqual(new Set([
        `${feature.id}-surface-lifecycle`,
        `${feature.id}-chat-lifecycle`,
        `${feature.id}-mixed-lifecycle`,
      ]))
    }
  })

  it("uses ordinary user intent instead of destination or workflow spoonfeeding", () => {
    const forbidden = [
      "source hub", "agent designer", "agent builds", "agent sandbox",
      "channels and deployment", "operations", "routedeck", "navgraph",
      "toolrouter", "open ", "stage ", "exact current", "through chat",
      "through the product surface",
    ]
    for (const feature of horizontalFeatures(persistedDesignState as WorkbenchState)) {
      for (const journey of feature.productJourneyEvals.filter((item) => item.interaction !== "surface")) {
        const normalized = ` ${journey.openingMessage.toLowerCase()} `
        expect(journey.openingMessage.split(/\s+/).length, journey.id).toBeLessThanOrEqual(28)
        for (const phrase of forbidden) {
          expect(normalized, `${journey.id} spoonfeeds ${phrase}`).not.toContain(phrase)
        }
      }
    }
  })

  it("keeps the governed evidence contract identical in seed and persisted Studio state", () => {
    expect(horizontalFeatures(persistedDesignState as WorkbenchState)).toEqual(horizontalFeatures(createSeedState()))
  })

  it("distinguishes publishing a build from changing channel availability", () => {
    const feature = horizontalFeatures(persistedDesignState as WorkbenchState)
      .find((item) => item.id === "channels-deployment")
    expect(feature?.prompt).toContain("Publishing means activating one exact eligible immutable build")
    expect(feature?.prompt).toContain("availability only enables or disables public access")
    expect(feature?.prompt).toContain("never satisfies a request to publish")
    expect(feature?.stories.find((item) => item.id === "channels-set-availability")?.expectedBehavior)
      .toContain("never selects, activates, publishes, rolls back, or substitutes an Agent build")
  })
})
