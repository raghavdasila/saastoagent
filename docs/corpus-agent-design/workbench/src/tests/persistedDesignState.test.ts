import { readFileSync } from "node:fs"
import { resolve } from "node:path"

import { afterEach, beforeEach, describe, expect, it } from "vitest"

import { installDesignStateFileMock, removeDesignStateFileMock, setDesignStateFile } from "@/tests/designStateFileMock"
import { loadWorkbenchState } from "@/workbench/storage"

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
})
