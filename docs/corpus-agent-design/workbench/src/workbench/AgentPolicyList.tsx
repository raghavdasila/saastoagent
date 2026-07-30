import { Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

export function AgentPolicyList({
  label,
  policies,
  disabled = false,
  onChange,
}: {
  label: string
  policies: string[]
  disabled?: boolean
  onChange: (policies: string[]) => void
}) {
  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-medium text-foreground">{label}</p>
        <Button type="button" size="xs" variant="ghost" disabled={disabled} onClick={() => onChange([...policies, ""])}>
          <Plus /> Add policy
        </Button>
      </div>
      {policies.length === 0 && <p className="studio-empty-state">No AgentPolicies defined at this scope.</p>}
      {policies.map((policy, index) => (
        <div key={index} className="flex items-start gap-2">
          <Textarea
            className="min-h-16 flex-1"
            aria-label={`${label} ${index + 1}`}
            value={policy}
            disabled={disabled}
            placeholder="Write the AgentPolicy instruction in plain language..."
            onChange={(event) => onChange(policies.map((item, policyIndex) => policyIndex === index ? event.target.value : item))}
          />
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="mt-0.5 text-muted-foreground hover:text-destructive"
            disabled={disabled}
            aria-label={`Remove ${label} ${index + 1}`}
            onClick={() => onChange(policies.filter((_, policyIndex) => policyIndex !== index))}
          >
            <Trash2 />
          </Button>
        </div>
      ))}
    </div>
  )
}
