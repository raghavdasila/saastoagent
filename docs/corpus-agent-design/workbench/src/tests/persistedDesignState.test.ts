import { readFileSync } from "node:fs"
import { resolve } from "node:path"

import { afterEach, beforeEach, describe, expect, it } from "vitest"

import { installDesignStateFileMock, removeDesignStateFileMock, setDesignStateFile } from "@/tests/designStateFileMock"
import { loadWorkbenchState } from "@/workbench/storage"
import { createSeedState } from "@/workbench/seed"

describe("persisted Design Studio state", () => {
  beforeEach(() => installDesignStateFileMock())
  afterEach(() => removeDesignStateFileMock())

  it("loads the repository-owned design-state.json through the runtime validator", async () => {
    const designState = readFileSync(resolve(process.cwd(), "design-state.json"), "utf8")
    setDesignStateFile(designState)

    const result = await loadWorkbenchState()

    expect(result.ok).toBe(true)
    if (result.ok) expect(result.source).toBe("saved")
  })

  it("mirrors the governed Lounge truth and clarification design in seed and saved state", () => {
    const saved = JSON.parse(readFileSync(resolve(process.cwd(), "design-state.json"), "utf8"))
    const seed = createSeedState()
    const savedLounge = saved.features.find((feature: { id: string }) => feature.id === "lounge")
    const seedLounge = seed.features.find((feature) => feature.id === "lounge")
    const savedDesigner = saved.features.find((feature: { id: string }) => feature.id === "agent-designer")
    const seedDesigner = seed.features.find((feature) => feature.id === "agent-designer")
    const savedClarification = savedDesigner.stories.find((story: { id: string }) => story.id === "deployed-agent-clarification")
    const seedClarification = seedDesigner?.stories.find((story) => story.id === "deployed-agent-clarification")

    expect(savedLounge.stories.find((story: { id: string }) => story.id === "lounge-product-help").nodePolicies)
      .toEqual(seedLounge?.stories.find((story) => story.id === "lounge-product-help")?.nodePolicies)
    expect(savedDesigner.policies).toEqual(seedDesigner?.policies)
    expect(savedClarification.expectedBehavior).toEqual(seedClarification?.expectedBehavior)
    expect(savedClarification.behaviorEvals.map((item: { id: string }) => item.id))
      .toEqual(seedClarification?.behaviorEvals.map((item) => item.id))
  })
})
