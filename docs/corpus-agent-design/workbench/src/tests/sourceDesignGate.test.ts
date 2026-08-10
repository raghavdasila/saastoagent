import persistedDesignState from "../../design-state.json"
import { describe, expect, it } from "vitest"

import { getFeatureConversationEvalReadiness, getFeatureProductJourneyReadiness } from "@/workbench/evaluationReadiness"
import { getStoryReadiness } from "@/workbench/readiness"
import { createSeedState } from "@/workbench/seed"
import type { DesignFeature, WorkbenchState } from "@/workbench/types"

const sourceFeatureIds = new Set(["source-hub", "api-source"])

function sourceFeatures(state: WorkbenchState): DesignFeature[] {
  return state.features.filter((feature) => sourceFeatureIds.has(feature.id))
}

describe("Source Hub and API Source design gate", () => {
  it("keeps the accepted source behaviors complete and product-semantic", () => {
    const state = persistedDesignState as WorkbenchState
    const features = sourceFeatures(state)

    expect(features.map((feature) => feature.id)).toEqual(["source-hub", "api-source"])
    for (const feature of features) {
      expect(feature.conversationEvals).toHaveLength(1)
      expect(getFeatureConversationEvalReadiness(feature).issues, feature.name).toEqual([])
      expect(getFeatureProductJourneyReadiness(feature).issues, feature.name).toEqual([])
      for (const story of feature.stories) {
        expect(story.status, story.title).toBe("approved")
        expect(getStoryReadiness(story, feature).blockers, story.title).toEqual([])
        expect(story.behaviorEvals).toHaveLength(1)
        for (const operation of story.operations) {
          expect(operation.availableThrough, `${story.title} / ${operation.name}`).not.toBe("not-decided")
          expect(operation.inputs.trim(), `${story.title} / ${operation.name} inputs`).not.toBe("")
          expect(operation.outcomes.trim(), `${story.title} / ${operation.name} outcomes`).not.toBe("")
          expect(operation.safetyAndReview.trim(), `${story.title} / ${operation.name} safety`).not.toBe("")
          expect(operation.recovery.trim(), `${story.title} / ${operation.name} recovery`).not.toBe("")
        }
      }
    }
  })

  it("mirrors the governed source design in the seed and saved state", () => {
    const saved = sourceFeatures(persistedDesignState as WorkbenchState)
    const seeded = sourceFeatures(createSeedState())
    expect(saved).toEqual(seeded)
  })

  it("contains no implementation identifiers in Studio-owned source design", () => {
    const serialized = JSON.stringify(sourceFeatures(persistedDesignState as WorkbenchState))
    expect(serialized).not.toMatch(/sources\.(home|manage|debug|return_to_home)/)
    expect(serialized).not.toMatch(/routedeck|AgentPolicy|ToolRouterOutcome|ASK_DISAMBIGUATE|ASK_PARAM/)
  })
})
