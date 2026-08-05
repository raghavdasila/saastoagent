import { describe, expect, it } from "vitest"

import persistedDesignState from "../../design-state.json"
import { getStoryReadiness } from "@/workbench/readiness"
import { createSeedState } from "@/workbench/seed"
import type { DesignStory, WorkbenchState } from "@/workbench/types"

function completeStory(): DesignStory {
  return {
    id: "review-ready",
    title: "Review a complete behavior",
    userIntent: "Understand the outcome.",
    agentIntent: "Present a reviewable result.",
    expectedBehavior: "Corpus presents the result and identifies completion.",
    messages: [],
    mockSurfacePath: "/mock-surfaces/example.html",
    nodePolicies: ["Keep the result scoped to this behavior."],
    capabilities: [{
      name: "Review",
      purpose: "Group the result and its presentation.",
      operationNames: ["Present result"],
      surfaceNames: ["Result"],
      policies: [],
    }],
    surfaces: [{ name: "Result", purpose: "Show the reviewable result.", policies: [] }],
    operations: [{
      name: "Present result",
      purpose: "Present the exact result selected for review.",
      inputs: "The selected result.",
      outcomes: "The exact result is visible; unavailable results remain unavailable.",
      safetyAndReview: "No external write occurs; the user reviews the result.",
      recovery: "Keep the failure visible and let the user return to the previous state.",
      policies: [],
    }],
    suggestedActions: [{ id: "review", label: "Review result", operationName: "Present result", visibility: "When a result exists." }],
    behaviorEvals: [{
      id: "review-ready-normal",
      title: "Review the result",
      enabled: true,
      blocking: true,
      coverage: ["normal", "boundary", "failure", "privacy", "adversarial"],
      input: "Show me the result.",
      referenceResponse: "",
      requiredCriteria: ["Presents the selected result."],
      forbiddenCriteria: [],
      expectations: {
        startingBehavior: "Review a complete behavior",
        finalBehavior: "Review a complete behavior",
        authentication: "unchanged",
        requiredOperations: ["Present result"],
        allowedOperations: [],
        forbiddenOperations: [],
        requiredSurfaces: ["Result"],
        requiredSuggestedActions: ["Review result"],
        forbiddenOutcomes: [],
      },
    }],
    evalExemptions: [],
    status: "draft",
    rejectionReason: "",
  }
}

describe("behavior readiness", () => {
  it("accepts a complete product-design contract", () => {
    const readiness = getStoryReadiness(completeStory())
    expect(readiness.isReady).toBe(true)
    expect(readiness.blockers).toEqual([])
  })

  it("requires the behavior meaning and every operation contract field", () => {
    const story = completeStory()
    story.userIntent = ""
    story.operations[0].inputs = ""
    story.operations[0].outcomes = ""
    story.operations[0].safetyAndReview = ""
    story.operations[0].recovery = ""

    const issueIds = getStoryReadiness(story).blockers.map((issue) => issue.id)
    expect(issueIds).toEqual(expect.arrayContaining([
      "behavior-user-intent",
      "operation-0-inputs",
      "operation-0-outcomes",
      "operation-0-safety",
      "operation-0-recovery",
    ]))
  })

  it("detects duplicate names and broken capability/action references", () => {
    const story = completeStory()
    story.operations.push({ ...story.operations[0] })
    story.capabilities[0].operationNames = ["Missing operation"]
    story.suggestedActions[0].operationName = "Missing operation"

    const messages = getStoryReadiness(story).blockers.map((issue) => issue.message)
    expect(messages).toContain("Operation name “Present result” is duplicated.")
    expect(messages).toContain("Review references missing Operation “Missing operation”.")
    expect(messages).toContain("Review result must reference a defined Operation.")
  })

  it("keeps every Lounge behavior free of blocking completeness issues", () => {
    const lounge = createSeedState().features.find((feature) => feature.id === "lounge")!
    const blockers = lounge.stories.flatMap((story) => getStoryReadiness(story).blockers)

    expect(lounge.stories.flatMap((story) => story.operations)).toHaveLength(21)
    expect(blockers).toEqual([])
  })

  it("persists the review-ready Lounge design without accepting it for the owner", () => {
    const lounge = (persistedDesignState as WorkbenchState).features.find((feature) => feature.id === "lounge")!
    const blockers = lounge.stories.flatMap((story) => getStoryReadiness(story).blockers)

    expect(lounge.stories.flatMap((story) => story.operations)).toHaveLength(21)
    expect(lounge.stories.every((story) => story.status === "draft")).toBe(true)
    expect(blockers).toEqual([])
  })
})
