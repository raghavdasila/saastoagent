import { CheckCircle2, Clock3, RefreshCcw, XCircle } from "lucide-react"
import { useEffect, useState } from "react"

import {
  evaluationDefinitionSha256,
  resolveEvaluationResultState,
  type EvaluationEvidence,
  type EvaluationResultState,
} from "@/workbench/evaluationEvidence"

export function EvaluationStatus({ compact = false, definition, evaluationId }: { compact?: boolean; definition?: unknown; evaluationId?: string }) {
  const [state, setState] = useState<EvaluationResultState>(evaluationId ? "loading" : "not-run")
  const definitionFingerprint = definition === undefined ? "" : JSON.stringify(definition)

  useEffect(() => {
    if (!evaluationId || definition === undefined) return
    let active = true
    setState("loading")
    void Promise.all([
      fetch("/__design-studio/evaluation-results", { cache: "no-store" }),
      evaluationDefinitionSha256(definition),
    ]).then(async ([response, currentDefinitionSha256]) => {
      if (!active) return
      if (response.status === 404) { setState("not-run"); return }
      if (!response.ok) throw new Error("evaluation results unavailable")
      const payload = await response.json() as { evaluations?: Record<string, EvaluationEvidence> }
      setState(resolveEvaluationResultState(payload.evaluations?.[evaluationId], currentDefinitionSha256))
    }).catch(() => { if (active) setState("not-run") })
    return () => { active = false }
  }, [definitionFingerprint, evaluationId])

  const label = state === "loading" ? "Loading" : state === "not-run" ? "Not run" : state[0].toUpperCase() + state.slice(1)
  const Icon = state === "passed" ? CheckCircle2 : state === "failed" ? XCircle : state === "stale" ? RefreshCcw : Clock3
  return (
    <span className="studio-eval-status" data-status={state} title="Runtime evaluation results are read from external immutable evidence.">
      <Icon aria-hidden="true" />
      {compact ? label : `${label} · runtime evidence is external`}
    </span>
  )
}
