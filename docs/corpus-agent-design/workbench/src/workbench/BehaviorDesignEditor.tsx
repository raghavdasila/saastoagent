import { Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { AgentPolicyList } from "@/workbench/AgentPolicyList"
import { StudioSection } from "@/workbench/StudioSection"
import type {
  CapabilityDesign,
  DesignStory,
  OperationDesign,
  SuggestedActionDesign,
  SurfaceDesign,
} from "@/workbench/types"

const splitNames = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean)

export function BehaviorDesignEditor({
  story,
  disabled,
  onChange,
}: {
  story: DesignStory
  disabled: boolean
  onChange: (patch: Partial<DesignStory>) => void
}) {
  function updateCapability(index: number, patch: Partial<CapabilityDesign>) {
    onChange({ capabilities: story.capabilities.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) })
  }

  function updateSurface(index: number, patch: Partial<SurfaceDesign>) {
    const previousName = story.surfaces[index].name
    const nextName = patch.name ?? previousName
    onChange({
      surfaces: story.surfaces.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item),
      capabilities: nextName === previousName ? story.capabilities : story.capabilities.map((capability) => ({
        ...capability,
        surfaceNames: capability.surfaceNames.map((name) => name === previousName ? nextName : name),
      })),
    })
  }

  function updateOperation(index: number, patch: Partial<OperationDesign>) {
    const previousName = story.operations[index].name
    const nextName = patch.name ?? previousName
    onChange({
      operations: story.operations.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item),
      suggestedActions: nextName === previousName ? story.suggestedActions : story.suggestedActions.map((action) => action.operationName === previousName ? { ...action, operationName: nextName } : action),
      capabilities: nextName === previousName ? story.capabilities : story.capabilities.map((capability) => ({
        ...capability,
        operationNames: capability.operationNames.map((name) => name === previousName ? nextName : name),
      })),
    })
  }

  function removeOperation(index: number) {
    const operationName = story.operations[index].name
    onChange({
      operations: story.operations.filter((_, itemIndex) => itemIndex !== index),
      suggestedActions: story.suggestedActions.filter((action) => action.operationName !== operationName),
      capabilities: story.capabilities.map((capability) => ({
        ...capability,
        operationNames: capability.operationNames.filter((name) => name !== operationName),
      })),
    })
  }

  function updateSuggestedAction(index: number, patch: Partial<SuggestedActionDesign>) {
    onChange({ suggestedActions: story.suggestedActions.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) })
  }

  return (
    <div className="border-t border-border">
      <StudioSection
        id="node-design-heading"
        title="Node design"
        description="This behavior is the feature Node. Define the guidance active at this location."
      >
        <AgentPolicyList label={`${story.title} Node AgentPolicy`} policies={story.nodePolicies} disabled={disabled} onChange={(nodePolicies) => onChange({ nodePolicies })} />
      </StudioSection>

      <StudioSection
        id="capabilities-heading"
        title="Capabilities"
        description="Group coherent Operations, Surfaces, and AgentPolicies available at this Node."
        action={
          <Button type="button" size="sm" variant="outline" disabled={disabled} onClick={() => onChange({ capabilities: [...story.capabilities, { name: "New capability", purpose: "", operationNames: [], surfaceNames: [], policies: [] }] })}>
            <Plus /> Add capability
          </Button>
        }
      >
        <div className="flex flex-col gap-3">
        {story.capabilities.length === 0 && <EmptyState>No capabilities defined for this Node.</EmptyState>}
        {story.capabilities.map((capability, index) => (
          <article key={index} className="studio-object-card">
            <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
              <Field>
                <FieldLabel htmlFor={`capability-name-${index}`}>Capability name</FieldLabel>
                <Input id={`capability-name-${index}`} value={capability.name} disabled={disabled} onChange={(event) => updateCapability(index, { name: event.target.value })} />
              </Field>
              <RemoveButton label={`Remove capability ${capability.name}`} disabled={disabled} onClick={() => onChange({ capabilities: story.capabilities.filter((_, itemIndex) => itemIndex !== index) })} />
            </div>
            <Field>
              <FieldLabel htmlFor={`capability-purpose-${index}`}>Purpose</FieldLabel>
              <Textarea id={`capability-purpose-${index}`} className="min-h-14" value={capability.purpose} disabled={disabled} onChange={(event) => updateCapability(index, { purpose: event.target.value })} />
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor={`capability-operations-${index}`}>Operations</FieldLabel>
                <Input id={`capability-operations-${index}`} value={capability.operationNames.join(", ")} disabled={disabled} placeholder="Operation names, comma separated" onChange={(event) => updateCapability(index, { operationNames: splitNames(event.target.value) })} />
              </Field>
              <Field>
                <FieldLabel htmlFor={`capability-surfaces-${index}`}>Surfaces</FieldLabel>
                <Input id={`capability-surfaces-${index}`} value={capability.surfaceNames.join(", ")} disabled={disabled} placeholder="Surface names, comma separated" onChange={(event) => updateCapability(index, { surfaceNames: splitNames(event.target.value) })} />
              </Field>
            </div>
            <AgentPolicyList label={`${capability.name} Capability AgentPolicy`} policies={capability.policies} disabled={disabled} onChange={(policies) => updateCapability(index, { policies })} />
          </article>
        ))}
        </div>
      </StudioSection>

      <StudioSection
        id="surfaces-heading"
        title="Surfaces"
        description="Define the structured product UI used by this Node."
        action={
          <Button type="button" size="sm" variant="outline" disabled={disabled} onClick={() => onChange({ surfaces: [...story.surfaces, { name: "New surface", purpose: "", policies: [] }] })}>
            <Plus /> Add surface
          </Button>
        }
      >
        <div className="flex flex-col gap-3">
        {story.surfaces.length === 0 && <EmptyState>No Surfaces defined for this Node.</EmptyState>}
        {story.surfaces.map((surface, index) => (
          <article key={index} className="studio-object-card">
            <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
              <Field>
                <FieldLabel htmlFor={`surface-name-${index}`}>Surface name</FieldLabel>
                <Input id={`surface-name-${index}`} value={surface.name} disabled={disabled} onChange={(event) => updateSurface(index, { name: event.target.value })} />
              </Field>
              <RemoveButton label={`Remove surface ${surface.name}`} disabled={disabled} onClick={() => onChange({
                surfaces: story.surfaces.filter((_, itemIndex) => itemIndex !== index),
                capabilities: story.capabilities.map((capability) => ({ ...capability, surfaceNames: capability.surfaceNames.filter((name) => name !== surface.name) })),
              })} />
            </div>
            <Field>
              <FieldLabel htmlFor={`surface-purpose-${index}`}>Purpose</FieldLabel>
              <Textarea id={`surface-purpose-${index}`} className="min-h-14" value={surface.purpose} disabled={disabled} onChange={(event) => updateSurface(index, { purpose: event.target.value })} />
            </Field>
            <AgentPolicyList label={`${surface.name} Surface AgentPolicy`} policies={surface.policies} disabled={disabled} onChange={(policies) => updateSurface(index, { policies })} />
          </article>
        ))}
        </div>
      </StudioSection>

      <StudioSection
        id="operations-heading"
        title="Operations"
        description="Define every authoritative action legal at this Node. Expand details when the contract needs refinement."
        action={
          <Button type="button" size="sm" variant="outline" disabled={disabled} onClick={() => onChange({ operations: [...story.operations, blankOperation()] })}>
            <Plus /> Add operation
          </Button>
        }
      >
        <div className="flex flex-col gap-3">
        {story.operations.length === 0 && <EmptyState>No Operations defined for this Node.</EmptyState>}
        {story.operations.map((operation, index) => (
          <article key={index} className="studio-object-card">
            <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
              <Field>
                <FieldLabel htmlFor={`operation-name-${index}`}>Operation name</FieldLabel>
                <Input id={`operation-name-${index}`} value={operation.name} disabled={disabled} onChange={(event) => updateOperation(index, { name: event.target.value })} />
              </Field>
              <RemoveButton label={`Remove operation ${operation.name}`} disabled={disabled} onClick={() => removeOperation(index)} />
            </div>
            <Field>
              <FieldLabel htmlFor={`operation-purpose-${index}`}>Intended effect</FieldLabel>
              <Textarea id={`operation-purpose-${index}`} className="min-h-14" value={operation.purpose} disabled={disabled} placeholder="What authoritative product action does this Operation perform?" onChange={(event) => updateOperation(index, { purpose: event.target.value })} />
            </Field>
            <AgentPolicyList label={`${operation.name} Operation AgentPolicy`} policies={operation.policies} disabled={disabled} onChange={(policies) => updateOperation(index, { policies })} />
            <details className="rounded-md border border-border bg-card px-3 py-2">
              <summary className="cursor-pointer text-xs font-medium text-muted-foreground marker:text-primary">Operation details</summary>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <DetailField id={`operation-inputs-${index}`} label="Inputs" value={operation.inputs} disabled={disabled} onChange={(inputs) => updateOperation(index, { inputs })} />
                <DetailField id={`operation-outcomes-${index}`} label="Outcomes" value={operation.outcomes} disabled={disabled} onChange={(outcomes) => updateOperation(index, { outcomes })} />
                <DetailField id={`operation-safety-${index}`} label="Safety and review" value={operation.safetyAndReview} disabled={disabled} onChange={(safetyAndReview) => updateOperation(index, { safetyAndReview })} />
                <DetailField id={`operation-recovery-${index}`} label="Recovery" value={operation.recovery} disabled={disabled} onChange={(recovery) => updateOperation(index, { recovery })} />
              </div>
            </details>
          </article>
        ))}
        </div>
      </StudioSection>

      <StudioSection
        id="suggested-actions-heading"
        title="Suggested actions"
        description="Optional chat invitations. Every SuggestedAction references a defined Operation."
        action={
          <Button type="button" size="sm" variant="outline" disabled={disabled || story.operations.length === 0} onClick={() => onChange({ suggestedActions: [...story.suggestedActions, { id: `suggested-action-${Date.now()}`, label: "", operationName: story.operations[0]?.name ?? "", visibility: "" }] })}>
            <Plus /> Add suggested action
          </Button>
        }
      >
        <div className="flex flex-col gap-3">
        {story.operations.length === 0 && <p className="text-xs text-muted-foreground">Define an Operation before adding a SuggestedAction.</p>}
        {story.suggestedActions.length === 0 && story.operations.length > 0 && <EmptyState>No SuggestedActions defined for this Node.</EmptyState>}
        {story.suggestedActions.map((action, index) => (
          <article key={action.id} className="studio-object-card grid sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] sm:items-end">
            <Field>
              <FieldLabel htmlFor={`suggested-action-label-${action.id}`}>Label</FieldLabel>
              <Input id={`suggested-action-label-${action.id}`} value={action.label} disabled={disabled} onChange={(event) => updateSuggestedAction(index, { label: event.target.value })} />
            </Field>
            <Field>
              <FieldLabel htmlFor={`suggested-action-operation-${action.id}`}>Operation</FieldLabel>
              <select id={`suggested-action-operation-${action.id}`} className="h-9 w-full rounded-md border border-input bg-[var(--studio-field)] px-2.5 text-[13px] text-foreground shadow-[var(--studio-shadow-panel)] outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/15" value={action.operationName} disabled={disabled} onChange={(event) => updateSuggestedAction(index, { operationName: event.target.value })}>
                <option value="">Select an Operation</option>
                {story.operations.map((operation, operationIndex) => <option key={`${operation.name}-${operationIndex}`} value={operation.name}>{operation.name}</option>)}
              </select>
            </Field>
            <RemoveButton label={`Remove suggested action ${index + 1}`} disabled={disabled} onClick={() => onChange({ suggestedActions: story.suggestedActions.filter((_, itemIndex) => itemIndex !== index) })} />
            <Field className="sm:col-span-2">
              <FieldLabel htmlFor={`suggested-action-visibility-${action.id}`}>Visibility details</FieldLabel>
              <Input id={`suggested-action-visibility-${action.id}`} value={action.visibility} disabled={disabled} placeholder="Optional condition for presenting this suggestion" onChange={(event) => updateSuggestedAction(index, { visibility: event.target.value })} />
              <FieldDescription className="text-xs">This controls presentation only; the referenced Operation remains the authority.</FieldDescription>
            </Field>
          </article>
        ))}
        </div>
      </StudioSection>
    </div>
  )
}

function blankOperation(): OperationDesign {
  return { name: "New operation", purpose: "", inputs: "", outcomes: "", safetyAndReview: "", recovery: "", policies: [] }
}

function EmptyState({ children }: { children: React.ReactNode }) {
  return <p className="studio-empty-state">{children}</p>
}

function RemoveButton({ label, disabled, onClick }: { label: string; disabled: boolean; onClick: () => void }) {
  return <Button type="button" size="icon" variant="ghost" aria-label={label} disabled={disabled} onClick={onClick}><Trash2 /></Button>
}

function DetailField({ id, label, value, disabled, onChange }: { id: string; label: string; value: string; disabled: boolean; onChange: (value: string) => void }) {
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Textarea id={id} className="min-h-14" value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} />
    </Field>
  )
}
