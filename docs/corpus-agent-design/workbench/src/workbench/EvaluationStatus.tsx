import { CheckCircle2, Clock3, RefreshCcw, XCircle } from "lucide-react"
import { useEffect, useState } from "react"

type ResultState = "loading" | "not-run" | "passed" | "failed" | "stale"

export function EvaluationStatus({ compact = false, evaluationId }: { compact?: boolean; evaluationId?: string }) {
  const [state, setState] = useState<ResultState>(evaluationId ? "loading" : "not-run")

  useEffect(() => {
    if (!evaluationId) return
    let active = true
    void fetch("/__design-studio/evaluation-results", { cache: "no-store" }).then(async (response) => {
      if (!active) return
      if (response.status === 404) { setState("not-run"); return }
      if (!response.ok) throw new Error("evaluation results unavailable")
      const payload = await response.json() as { currentDesignSha256: string; evaluations?: Record<string, { status: string; designSha256: string }> }
      const result = payload.evaluations?.[evaluationId]
      if (!result) setState("not-run")
      else if (result.designSha256 !== payload.currentDesignSha256) setState("stale")
      else setState(result.status === "passed" ? "passed" : "failed")
    }).catch(() => { if (active) setState("not-run") })
    return () => { active = false }
  }, [evaluationId])

  const label = state === "loading" ? "Loading" : state === "not-run" ? "Not run" : state[0].toUpperCase() + state.slice(1)
  const Icon = state === "passed" ? CheckCircle2 : state === "failed" ? XCircle : state === "stale" ? RefreshCcw : Clock3
  return (
    <span className="studio-eval-status" data-status={state} title="Runtime evaluation results are read from external immutable evidence.">
      <Icon aria-hidden="true" />
      {compact ? label : `${label} · runtime evidence is external`}
    </span>
  )
}
