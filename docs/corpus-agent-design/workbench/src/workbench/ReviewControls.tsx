import { useState } from "react"
import { Check, RotateCcw, Trash2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldLabel } from "@/components/ui/field"
import { Textarea } from "@/components/ui/textarea"
import type { DesignStory } from "@/workbench/types"
import type { StoryReadiness } from "@/workbench/readiness"

interface ReviewControlsProps {
  story: DesignStory
  readiness: StoryReadiness
  canDelete: boolean
  onChange: (patch: Partial<DesignStory>, reopen?: boolean) => void
  onDelete: () => void
}

export function ReviewControls({ story, readiness, canDelete, onChange, onDelete }: ReviewControlsProps) {
  const [validationError, setValidationError] = useState("")
  const [isRejecting, setIsRejecting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  if (story.status !== "draft") {
    const invalidApproval = story.status === "approved" && !readiness.isReady
    return (
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className={invalidApproval ? "text-sm font-semibold text-[var(--studio-warning)]" : "text-sm font-semibold"}>
            {invalidApproval ? "Approval invalid" : story.status === "approved" ? "Approved" : "Rejected"}
          </p>
          {invalidApproval && <p className="mt-1 text-xs text-[var(--studio-warning)]">This saved approval has {readiness.blockers.length} blocking {readiness.blockers.length === 1 ? "issue" : "issues"}. Reopen it before editing or approving again.</p>}
          {story.status === "rejected" && <p className="mt-1 text-sm text-muted-foreground">{story.rejectionReason}</p>}
        </div>
        <Button variant="ghost" onClick={() => onChange({ status: "draft", rejectionReason: "" }, true)}>
          <RotateCcw data-icon="inline-start" /> Reopen draft
        </Button>
      </div>
    )
  }

  function reject() {
    if (!story.rejectionReason.trim()) {
      setValidationError("Add a reason before rejecting")
      return
    }
    setValidationError("")
    onChange({ status: "rejected", rejectionReason: story.rejectionReason.trim() }, true)
  }

  if (isDeleting) {
    return (
      <div role="alertdialog" aria-label="Confirm behavior deletion" className="flex flex-wrap items-center justify-between gap-3 border border-destructive/30 bg-destructive/5 p-3">
        <div>
          <p className="text-sm font-semibold">Delete &quot;{story.title}&quot;?</p>
          <p className="mt-1 text-xs text-muted-foreground">This removes the local draft and cannot be undone.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={() => setIsDeleting(false)}>Cancel</Button>
          <Button variant="destructive" onClick={onDelete}>
            <Trash2 data-icon="inline-start" /> Confirm delete behavior
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {!readiness.isReady && (
        <p id="approval-readiness-message" className="text-xs text-[var(--studio-warning)]">
          Resolve {readiness.blockers.length} blocking {readiness.blockers.length === 1 ? "issue" : "issues"} before approval.
        </p>
      )}
      {isRejecting && (
        <Field data-invalid={Boolean(validationError)}>
          <FieldLabel htmlFor="rejection-reason">Why reject this behavior?</FieldLabel>
          <Textarea
            id="rejection-reason"
            className="min-h-16"
            placeholder="Short reason"
            value={story.rejectionReason}
            aria-invalid={Boolean(validationError)}
            onChange={(event) => {
              setValidationError("")
              onChange({ rejectionReason: event.target.value }, true)
            }}
          />
          <FieldError>{validationError}</FieldError>
        </Field>
      )}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Button variant="ghost" disabled={!canDelete} onClick={() => setIsDeleting(true)}>
          <Trash2 data-icon="inline-start" /> Delete behavior
        </Button>
        <div className="flex gap-2">
        {isRejecting ? (
          <>
            <Button variant="ghost" onClick={() => { setIsRejecting(false); setValidationError("") }}>Cancel</Button>
            <Button variant="destructive" onClick={reject}>
              <X data-icon="inline-start" /> Confirm rejection
            </Button>
          </>
        ) : (
          <>
            <Button variant="destructive" onClick={() => setIsRejecting(true)}>
              <X data-icon="inline-start" /> Reject behavior
            </Button>
            <Button disabled={!readiness.isReady} aria-describedby={!readiness.isReady ? "approval-readiness-message" : undefined} onClick={() => onChange({ status: "approved", rejectionReason: "" }, true)}>
              <Check data-icon="inline-start" /> Approve behavior
            </Button>
          </>
        )}
        </div>
      </div>
    </div>
  )
}
