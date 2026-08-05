import { describe, expect, it } from "vitest"

import { getBehaviorEvalReadiness, getFeatureConversationEvalReadiness } from "@/workbench/evaluationReadiness"
import { createSeedState } from "@/workbench/seed"

describe("evaluation definition readiness", () => {
  it("covers all five evaluation categories across every Lounge behavior", () => {
    const lounge = createSeedState().features.find((feature) => feature.id === "lounge")!

    expect(lounge.stories).toHaveLength(8)
    for (const story of lounge.stories) {
      expect(story.behaviorEvals.length).toBeGreaterThanOrEqual(2)
      expect(getBehaviorEvalReadiness(story).issues).toEqual([])
      expect(new Set(story.behaviorEvals.flatMap((evalCase) => evalCase.coverage))).toEqual(new Set(["normal", "boundary", "failure", "privacy", "adversarial"]))
      expect(story.behaviorEvals.every((evalCase) => evalCase.enabled && evalCase.blocking)).toBe(true)
    }
  })

  it("authors the approved adaptive Lounge conversation set", () => {
    const lounge = createSeedState().features.find((feature) => feature.id === "lounge")!

    expect(lounge.conversationEvals.map((scenario) => scenario.title)).toEqual([
      "Grounded product help",
      "Redirect task work",
      "Sign-up and sign-in routing",
      "Recovery without enumeration",
      "Credentials in chat",
      "Private Workspace leakage",
      "Indirect multi-turn bypass",
      "Unknown and unavailable claims",
    ])
    expect(lounge.conversationEvals.every((scenario) => scenario.enabled && scenario.blocking)).toBe(true)
    expect(getFeatureConversationEvalReadiness(lounge).issues).toEqual([])
    expect(JSON.stringify({ stories: lounge.stories.map((story) => story.behaviorEvals), conversations: lounge.conversationEvals })).not.toContain("RouteDeck")
  })

  it("allows semantic references to be omitted and never defines exact-output matching", () => {
    const story = createSeedState().features.find((feature) => feature.id === "lounge")!.stories[0]
    story.behaviorEvals[0].referenceResponse = ""

    expect(getBehaviorEvalReadiness(story).issues).toEqual([])
    expect(JSON.stringify(story.behaviorEvals)).not.toContain("exactResponse")
  })

  it("reports missing coverage, empty criteria, and broken design references", () => {
    const story = createSeedState().features.find((feature) => feature.id === "lounge")!.stories[0]
    story.behaviorEvals = [{
      ...story.behaviorEvals[0],
      coverage: ["normal"],
      requiredCriteria: [],
      forbiddenCriteria: [],
      expectations: { ...story.behaviorEvals[0].expectations, requiredSurfaces: ["Missing surface"] },
    }]

    const messages = getBehaviorEvalReadiness(story).issues.map((issue) => issue.message)
    expect(messages).toContain("Public arrival needs required or forbidden semantic criteria.")
    expect(messages).toContain("Required Surface expectation references missing design item “Missing surface”.")
    expect(messages).toContain("Cover boundary behavior or record why it is not applicable.")
  })

  it("requires bounded adaptive conversation contracts", () => {
    const lounge = createSeedState().features.find((feature) => feature.id === "lounge")!
    lounge.conversationEvals[0] = { ...lounge.conversationEvals[0], hiddenGoal: "", maxTurns: 1, stoppingConditions: [] }

    const messages = getFeatureConversationEvalReadiness(lounge).issues.map((issue) => issue.message)
    expect(messages).toContain("Grounded product help needs a hidden tester goal.")
    expect(messages).toContain("Grounded product help must allow 2 to 20 turns.")
    expect(messages).toContain("Grounded product help needs a stopping condition.")
  })
})
