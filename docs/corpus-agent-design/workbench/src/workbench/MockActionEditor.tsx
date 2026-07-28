import { Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Field, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import type { MockAction } from "@/workbench/types"

interface MockActionEditorProps {
  actions: MockAction[]
  disabled: boolean
  onChange: (actions: MockAction[]) => void
}

export function MockActionEditor({ actions, disabled, onChange }: MockActionEditorProps) {
  function addAction() {
    onChange([...actions, { id: `action-${Date.now()}`, label: "" }])
  }

  return (
    <section aria-labelledby="mock-actions-heading" className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="mock-actions-heading" className="text-sm font-semibold">Available actions</h2>
        <Button size="sm" variant="ghost" disabled={disabled} onClick={addAction}>
          <Plus data-icon="inline-start" /> Add action
        </Button>
      </div>

      {actions.length === 0 ? (
        <p className="border-y border-border py-3 text-sm text-muted-foreground">No separate actions for this behavior.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {actions.map((action, index) => (
            <div key={action.id} className="flex items-end gap-2">
              <Field className="min-w-0 flex-1">
                <FieldLabel htmlFor={`action-${action.id}`}>Action {index + 1}</FieldLabel>
                <Input
                  id={`action-${action.id}`}
                  value={action.label}
                  disabled={disabled}
                  placeholder="Action label"
                  onChange={(event) => onChange(actions.map((item) => item.id === action.id ? { ...item, label: event.target.value } : item))}
                />
              </Field>
              <Button
                size="icon"
                variant="ghost"
                disabled={disabled}
                aria-label={`Remove action ${index + 1}`}
                onClick={() => onChange(actions.filter((item) => item.id !== action.id))}
              >
                <Trash2 />
              </Button>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
