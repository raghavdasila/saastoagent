import { describe, expect, it } from "vitest"

import { getBehaviorEvalReadiness, getFeatureConversationEvalReadiness } from "@/workbench/evaluationReadiness"
import { getStoryReadiness } from "@/workbench/readiness"
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

  it("requires authored product actions and deterministic state checkpoints", () => {
    const lounge = createSeedState().features.find((feature) => feature.id === "lounge")!
    const registration = lounge.stories.find((story) => story.id === "owner-auth-register")!.behaviorEvals.find((evalCase) => evalCase.id === "register-normal")!

    expect(registration.actionPlan.steps.map((step) => step.kind)).toEqual(["message", "surface-submit", "checkpoint"])
    const checkpoint = registration.actionPlan.steps.at(-1)
    expect(checkpoint?.kind).toBe("checkpoint")
    if (checkpoint?.kind === "checkpoint") expect(checkpoint.stateAssertions).toHaveLength(2)

    registration.actionPlan.steps[2] = { id: "broken-action", kind: "suggested-action", behavior: "Sign in", action: "Continue to Workspace" }
    registration.actionPlan.steps[3] = { id: "empty-state", kind: "checkpoint", label: "", stateAssertions: [] }
    const messages = getBehaviorEvalReadiness(lounge.stories.find((story) => story.id === "owner-auth-register")!).issues.map((issue) => issue.message)
    expect(messages).toContain("Action step references missing SuggestedAction “Sign in / Continue to Workspace”.")
    expect(messages).toContain("Checkpoint needs a label.")
    expect(messages).toContain("Checkpoint needs at least one product-state assertion.")
  })

  it("authors autonomous clarification as an approved Agent Designer contract", () => {
    const designer = createSeedState().features.find((feature) => feature.id === "agent-designer")!
    const clarification = designer.stories.find((story) => story.id === "deployed-agent-clarification")!
    const serialized = JSON.stringify(clarification)

    expect(designer.name).toBe("Agent Designer")
    expect(clarification.status).toBe("approved")
    expect(clarification.operations.map((item) => item.name)).toEqual(["Continue waiting agent run"])
    expect(clarification.behaviorEvals.map((item) => item.id)).toEqual([
      "clarification-explicit-operation",
      "clarification-parameter-provenance",
      "clarification-material-ambiguity",
      "clarification-unproven-values",
      "clarification-safe-write-review",
      "clarification-multicall-atomicity",
    ])
    expect(getStoryReadiness(clarification, designer).blockers).toEqual([])
    expect(serialized).toContain("Do not make an additional lookup call")
    expect(serialized).toContain("resume the same run")
    expect(serialized).toContain("safe provenance in Operations")
    expect(serialized).not.toContain("ASK_DISAMBIGUATE")
    expect(serialized).not.toContain("ASK_PARAM")
    expect(serialized).not.toContain("RouteDeck")
  })
})
