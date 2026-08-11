import persistedDesignState from "../../design-state.json"
import { describe, expect, it } from "vitest"

import { getFeatureConversationEvalReadiness, getFeatureProductJourneyReadiness } from "@/workbench/evaluationReadiness"
import { getStoryReadiness } from "@/workbench/readiness"
import { createSeedState } from "@/workbench/seed"
import type { DesignFeature, WorkbenchState } from "@/workbench/types"

const lifecycleIds = new Set([
  "agents-attach-source",
  "agents-detach-source",
  "agents-create-source",
  "agents-setup-from-api-file",
  "agents-open-source",
  "agents-archive",
  "agents-delete",
  "agents-operations-hub",
  "agents-build-source-lineage",
])

function agents(state: WorkbenchState): DesignFeature {
  const feature = state.features.find((item) => item.id === "agents")
  if (!feature) throw new Error("Agents feature is required")
  return feature
}

function lifecycle(feature: DesignFeature) {
  return feature.stories.filter((story) => lifecycleIds.has(story.id))
}

describe("Agents lifecycle design gate", () => {
  it("keeps opening creation distinct from a completed create request", () => {
    const feature = agents(persistedDesignState as WorkbenchState)
    const view = feature.stories.find((story) => story.id === "agents-view")
    const openCreate = view?.operations.find((operation) => operation.name === "Open agent creation")

    expect(openCreate?.purpose).toBe(
      "Begin a distinct new-agent design path only when the owner's current request still needs a new agent; navigation creates nothing and must not be used after that request already created its agent.",
    )
    expect(openCreate?.inputs).toBe(
      "An authenticated owner explicitly asks to begin a distinct new agent and the current request has not already created it; no agent fields are submitted during navigation.",
    )
    expect(openCreate?.safetyAndReview).toContain(
      "do not reopen creation unless the owner separately asks to start another agent",
    )
  })

  it("accepts every Step 5 behavior with complete product contracts", () => {
    const feature = agents(persistedDesignState as WorkbenchState)
    expect(lifecycle(feature).map((story) => story.title)).toEqual([
      "Attach an existing source",
      "Detach a source from an agent",
      "Create and attach a source",
      "Set up an agent from an attached API definition",
      "Open an attached source",
      "Archive an agent",
      "Delete an agent",
      "Use selected-agent operations",
      "Inspect historical build source references",
    ])
    for (const story of lifecycle(feature)) {
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
    expect(getFeatureConversationEvalReadiness(feature).issues).toEqual([])
    expect(getFeatureProductJourneyReadiness(feature).issues).toEqual([])
  })

  it("mirrors the governed lifecycle slice in seed and saved state", () => {
    const saved = agents(persistedDesignState as WorkbenchState)
    const seeded = agents(createSeedState())
    expect(lifecycle(saved)).toEqual(lifecycle(seeded))
    expect(saved.conversationEvals).toEqual(seeded.conversationEvals)
    expect(saved.productJourneyEvals).toEqual(seeded.productJourneyEvals)
  })

  it("keeps implementation identifiers out of Studio-owned Agents design", () => {
    const feature = agents(persistedDesignState as WorkbenchState)
    const serialized = JSON.stringify({ policies: feature.policies, stories: lifecycle(feature) })
    expect(serialized).not.toMatch(/agents\.(home|create|inventory|creation|open_create|save_changes)/)
    expect(serialized).not.toMatch(/routedeck|AgentPolicy|NodeRef|OperationRef|EntityProvider|GuardRef/)
  })

  it("does not model selected agent or source identifiers as literal SuggestedAction arguments", () => {
    const feature = agents(persistedDesignState as WorkbenchState)
    const attachExisting = feature.stories.find((story) => story.id === "agents-attach-source")
    const detachExisting = feature.stories.find((story) => story.id === "agents-detach-source")
    const createSource = feature.stories.find((story) => story.id === "agents-create-source")

    expect(attachExisting?.suggestedActions).toEqual([])
    expect(detachExisting?.suggestedActions).toEqual([])
    expect(createSource?.suggestedActions).toEqual([])
    expect(attachExisting?.operations.map((operation) => operation.name)).toContain("Attach source to agent")
    expect(detachExisting?.operations.map((operation) => operation.name)).toEqual(["Detach source from agent"])
    expect(createSource?.operations.map((operation) => operation.name)).toEqual([
      "Open source creation",
      "Attach newly created source",
    ])
    expect(attachExisting?.surfaces.map((surface) => surface.name)).toContain("Agent source picker")
    expect(detachExisting?.surfaces.map((surface) => surface.name)).toContain("Agent source picker")
    expect(detachExisting?.expectedBehavior).toContain("historical accepted designs and builds retain their exact Source revisions")
  })

  it("keeps attached-file setup model-driven across existing product operations", () => {
    const feature = agents(persistedDesignState as WorkbenchState)
    const setup = feature.stories.find((story) => story.id === "agents-setup-from-api-file")

    expect(setup?.status).toBe("approved")
    expect(setup?.capabilities.map((capability) => capability.name)).toEqual(["Source attachments"])
    expect(setup?.surfaces.map((surface) => surface.name)).toEqual(["Agent source picker"])
    expect(setup?.operations.map((operation) => operation.name)).toEqual([
      "Choose existing agent for source",
      "Open agent creation",
      "Attach source to agent",
    ])
    expect(setup?.expectedBehavior).toContain("Attaching the file only stages it")
    expect(setup?.expectedBehavior).toContain("asks whether to use an existing agent or create one")
    expect(setup?.expectedBehavior).toContain("never invents operation selections")
    expect(JSON.stringify(setup)).not.toMatch(/workspace\.open_sources|sources\.accept_staged_api|sources\.process_api|agents\.create_agent/)
  })
})
