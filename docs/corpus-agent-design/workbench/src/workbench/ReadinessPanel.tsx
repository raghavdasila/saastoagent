import { AlertCircle, CheckCircle2, Info } from "lucide-react"

import { cn } from "@/lib/utils"
import type { StoryReadiness } from "@/workbench/readiness"

export function ReadinessPanel({ readiness, onNavigate }: { readiness: StoryReadiness; onNavigate?: (targetId: string) => void }) {
  return (
    <section aria-labelledby="readiness-heading" className="studio-readiness-panel">
      <div className="studio-readiness-summary">
        <span className={cn("studio-readiness-mark", readiness.isReady ? "is-ready" : "has-blockers")}>
          {readiness.isReady ? <CheckCircle2 aria-hidden="true" /> : <AlertCircle aria-hidden="true" />}
        </span>
        <div>
          <h3 id="readiness-heading" className="text-sm font-semibold">
            {readiness.isReady ? "Ready for review" : `${readiness.blockers.length} blocking ${readiness.blockers.length === 1 ? "issue" : "issues"}`}
          </h3>
          <p className="mt-0.5 text-xs leading-5 text-muted-foreground">
            {readiness.isReady ? "The behavior has enough product meaning to approve." : "Resolve these design gaps before approval."}
          </p>
        </div>
      </div>

      {readiness.issues.length === 0 ? (
        <p className="studio-readiness-empty">No completeness issues found.</p>
      ) : (
        <ol className="studio-issue-list">
          {readiness.issues.map((issue) => (
            <li key={issue.id}>
              <button
                type="button"
                className="studio-issue-row"
                disabled={!issue.targetId || !onNavigate}
                onClick={() => issue.targetId && onNavigate?.(issue.targetId)}
              >
                {issue.severity === "blocking"
                  ? <AlertCircle className="text-[var(--studio-warning)]" aria-hidden="true" />
                  : <Info className="text-muted-foreground" aria-hidden="true" />}
                <span>{issue.message}</span>
              </button>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
