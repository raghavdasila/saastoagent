import { Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import type { AgentPolicyDesign, AgentPolicyScope } from "@/workbench/types"

const POLICY_SCOPES: Array<{ value: AgentPolicyScope; label: string }> = [
  { value: "feature", label: "Feature" },
  { value: "behavior", label: "Behavior" },
  { value: "node", label: "Node" },
  { value: "capability", label: "Capability" },
  { value: "surface", label: "Surface" },
  { value: "action", label: "Action" },
  { value: "operation", label: "Operation" },
  { value: "other", label: "Other" },
]

export function PolicyScopeEditor({
  policies,
  title,
  description,
  availableScopes,
  suggestedNames,
  onChange,
}: {
  policies: AgentPolicyDesign[]
  title: string
  description: string
  availableScopes: AgentPolicyScope[]
  suggestedNames: Partial<Record<AgentPolicyScope, string>>
  onChange: (policies: AgentPolicyDesign[]) => void
}) {
  const scopes = POLICY_SCOPES.filter((scope) => availableScopes.includes(scope.value))
  const defaultScope = scopes[0]?.value ?? "other"

  function updatePolicy(index: number, patch: Partial<AgentPolicyDesign>) {
    onChange(policies.map((policy, policyIndex) => policyIndex === index ? { ...policy, ...patch } : policy))
  }

  function addPolicy() {
    onChange([...policies, { scope: defaultScope, scopeName: suggestedNames[defaultScope] ?? "", guidance: "" }])
  }

  function removePolicy(index: number) {
    onChange(policies.filter((_, policyIndex) => policyIndex !== index))
  }

  function suggestedScopeName(scope: AgentPolicyScope): string {
    return suggestedNames[scope] ?? ""
  }

  return (
    <section aria-labelledby="agent-policy-heading" className="flex flex-col gap-3 border-t border-border pt-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 id="agent-policy-heading" className="text-sm font-semibold">{title}</h2>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
        <Button type="button" size="sm" variant="outline" onClick={addPolicy}>
          <Plus /> Add policy
        </Button>
      </div>

      {policies.length === 0 && (
        <p className="border border-dashed border-border p-3 text-xs text-muted-foreground">No policies defined here.</p>
      )}

      {policies.map((policy, index) => (
        <div key={index} className="flex flex-col gap-3 border border-border p-3">
          <div className="grid gap-3 sm:grid-cols-[9rem_minmax(0,1fr)_auto] sm:items-end">
            <Field>
              <FieldLabel htmlFor={`policy-scope-${index}`}>Scope</FieldLabel>
              <select
                id={`policy-scope-${index}`}
                className="h-9 w-full border border-input bg-background px-2 text-sm text-foreground"
                value={policy.scope}
                onChange={(event) => {
                  const scope = event.target.value as AgentPolicyScope
                  updatePolicy(index, { scope, scopeName: suggestedScopeName(scope) })
                }}
              >
                {scopes.map((scope) => <option key={scope.value} value={scope.value}>{scope.label}</option>)}
              </select>
            </Field>
            <Field>
              <FieldLabel htmlFor={`policy-scope-name-${index}`}>Applies to</FieldLabel>
              <Input
                id={`policy-scope-name-${index}`}
                value={policy.scopeName}
                placeholder={`Name this ${policy.scope} scope`}
                onChange={(event) => updatePolicy(index, { scopeName: event.target.value })}
              />
            </Field>
            <Button type="button" size="icon" variant="ghost" aria-label={`Remove policy ${index + 1}`} onClick={() => removePolicy(index)}>
              <Trash2 />
            </Button>
          </div>
          <Field>
            <FieldLabel htmlFor={`policy-guidance-${index}`}>Policy guidance</FieldLabel>
            <Textarea
              id={`policy-guidance-${index}`}
              className="min-h-16"
              value={policy.guidance}
              placeholder="Write the constraint or instruction in plain language..."
              onChange={(event) => updatePolicy(index, { guidance: event.target.value })}
            />
            <FieldDescription className="text-xs">This is agent-design guidance for the named scope, not a generated identifier or compiled runtime policy.</FieldDescription>
          </Field>
        </div>
      ))}
    </section>
  )
}
