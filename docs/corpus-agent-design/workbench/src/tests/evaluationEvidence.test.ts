import { describe, expect, it } from "vitest"

import {
  canonicalEvaluationJson,
  evaluationDefinitionSha256,
  resolveEvaluationResultState,
} from "@/workbench/evaluationEvidence"

describe("external evaluation evidence identity", () => {
  it("matches the evaluator's sorted ASCII JSON definition identity", async () => {
    const definition = {
      title: "Clarify “safely”",
      enabled: true,
      expectations: { allowed: [], count: 2 },
    }

    expect(canonicalEvaluationJson(definition)).toBe('{"enabled":true,"expectations":{"allowed":[],"count":2},"title":"Clarify \\u201csafely\\u201d"}')
    expect(await evaluationDefinitionSha256(definition)).toBe("28bd1abc2e50593ff8243925c0e54171d3199be83c272b6b990417b17c94e766")
  })

  it("resolves current evidence independently for each definition", () => {
    expect(resolveEvaluationResultState(undefined, "current-a")).toBe("not-run")
    expect(resolveEvaluationResultState({ status: "passed", definitionSha256: "old-a" }, "current-a")).toBe("stale")
    expect(resolveEvaluationResultState({ status: "passed", definitionSha256: "current-a" }, "current-a")).toBe("passed")
    expect(resolveEvaluationResultState({ status: "infrastructure_failure", definitionSha256: "current-b" }, "current-b")).toBe("failed")
  })
})
