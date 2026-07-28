import { useState } from "react"
import { Check, RotateCcw, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldLabel } from "@/components/ui/field"
import { Textarea } from "@/components/ui/textarea"
import type { DesignStory } from "@/workbench/types"

interface ReviewControlsProps {
  story: DesignStory
  onChange: (patch: Partial<DesignStory>, reopen?: boolean) => void
}

export function ReviewControls({ story, onChange }: ReviewControlsProps) {
  const [validationError, setValidationError] = useState("")
  const [isRejecting, setIsRejecting] = useState(false)

  if (story.status !== "draft") {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-3 shadow-sm">
        <div>
          <p className="text-sm font-semibold">{story.status === "approved" ? "Approved" : "Rejected"}</p>
          {story.status === "rejected" && <p className="mt-1 text-sm text-muted-foreground">{story.rejectionReason}</p>}
        </div>
        <Button variant="outline" onClick={() => onChange({ status: "draft", rejectionReason: "" }, true)}>
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

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-3 shadow-sm">
      {isRejecting && (
        <Field data-invalid={Boolean(validationError)}>
          <FieldLabel htmlFor="rejection-reason">Why reject this story?</FieldLabel>
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
      <div className="flex justify-end gap-2">
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
              <X data-icon="inline-start" /> Reject story
            </Button>
            <Button onClick={() => onChange({ status: "approved", rejectionReason: "" }, true)}>
              <Check data-icon="inline-start" /> Approve story
            </Button>
          </>
        )}
      </div>
    </div>
  )
}
