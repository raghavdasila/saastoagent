import { Clock3 } from "lucide-react"

export function EvaluationStatus({ compact = false }: { compact?: boolean }) {
  return (
    <span className="studio-eval-status" title="Runtime evaluation results are external to Studio design state.">
      <Clock3 aria-hidden="true" />
      {compact ? "Not run" : "Not run · runtime evidence is external"}
    </span>
  )
}
