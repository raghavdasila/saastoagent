import { Check, ChevronDown, Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { AgentPolicyList } from "@/workbench/AgentPolicyList"
import { OperationInventory } from "@/workbench/OperationInventory"
import { StudioSection } from "@/workbench/StudioSection"
import type { CapabilityDesign, DesignStory, SuggestedActionDesign, SurfaceDesign } from "@/workbench/types"

export function BehaviorDesignEditor({ story, disabled, onChange }: {
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

  function removeSurface(index: number) {
    const surfaceName = story.surfaces[index].name
    onChange({
      surfaces: story.surfaces.filter((_, itemIndex) => itemIndex !== index),
      capabilities: story.capabilities.map((capability) => ({
        ...capability,
        surfaceNames: capability.surfaceNames.filter((name) => name !== surfaceName),
      })),
    })
  }

  function updateSuggestedAction(index: number, patch: Partial<SuggestedActionDesign>) {
    onChange({ suggestedActions: story.suggestedActions.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) })
  }

  return (
    <div className="border-t border-border">
      <StudioSection id="node-design-heading" title="Behavior rules" description="Guidance active whenever this behavior is the current product location.">
        <div id="node-rules">
          <AgentPolicyList label={`${story.title} rules`} policies={story.nodePolicies} disabled={disabled} onChange={(nodePolicies) => onChange({ nodePolicies })} />
        </div>
      </StudioSection>

      <StudioSection
        id="capabilities-heading"
        title="Capabilities"
        description="Group coherent Operations and Surfaces available in this behavior."
        action={<Button type="button" size="sm" variant="outline" disabled={disabled} onClick={() => onChange({ capabilities: [...story.capabilities, { name: "New capability", purpose: "", operationNames: [], surfaceNames: [], policies: [] }] })}><Plus /> Add capability</Button>}
      >
        {story.capabilities.length === 0 ? <p className="studio-empty-state">No capabilities defined for this behavior.</p> : (
          <div className="studio-outline-list">
            {story.capabilities.map((capability, index) => (
              <details key={index} id={`capability-${index}`} className="studio-outline-row">
                <summary>
                  <ChevronDown aria-hidden="true" />
                  <span className="studio-outline-title">{capability.name || `Capability ${index + 1}`}</span>
                  <span className="studio-outline-purpose">{capability.purpose || "No purpose defined"}</span>
                  <span className="studio-outline-meta">{capability.operationNames.length} operations · {capability.surfaceNames.length} surfaces</span>
                </summary>
                <div className="studio-outline-content">
                  <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
                    <Field><FieldLabel htmlFor={`capability-name-${index}`}>Capability name</FieldLabel><Input id={`capability-name-${index}`} value={capability.name} disabled={disabled} onChange={(event) => updateCapability(index, { name: event.target.value })} /></Field>
                    <RemoveButton label={`Remove capability ${capability.name}`} disabled={disabled} onClick={() => onChange({ capabilities: story.capabilities.filter((_, itemIndex) => itemIndex !== index) })} />
                  </div>
                  <Field><FieldLabel htmlFor={`capability-purpose-${index}`}>Purpose</FieldLabel><Textarea id={`capability-purpose-${index}`} className="min-h-16" value={capability.purpose} disabled={disabled} onChange={(event) => updateCapability(index, { purpose: event.target.value })} /></Field>
                  <AssociationPicker label="Operations" emptyText="Define an Operation before associating one." options={story.operations.map((item) => item.name)} selected={capability.operationNames} disabled={disabled} onChange={(operationNames) => updateCapability(index, { operationNames })} />
                  <AssociationPicker label="Surfaces" emptyText="Define a Surface before associating one." options={story.surfaces.map((item) => item.name)} selected={capability.surfaceNames} disabled={disabled} onChange={(surfaceNames) => updateCapability(index, { surfaceNames })} />
                  <AgentPolicyList label={`${capability.name || `Capability ${index + 1}`} rules`} policies={capability.policies} disabled={disabled} onChange={(policies) => updateCapability(index, { policies })} />
                </div>
              </details>
            ))}
          </div>
        )}
      </StudioSection>

      <StudioSection
        id="surfaces-heading"
        title="Surfaces"
        description="Describe structured product UI used by this behavior."
        action={<Button type="button" size="sm" variant="outline" disabled={disabled} onClick={() => onChange({ surfaces: [...story.surfaces, { name: "New surface", purpose: "", policies: [] }] })}><Plus /> Add surface</Button>}
      >
        {story.surfaces.length === 0 ? <p className="studio-empty-state">No Surface is needed when the behavior is clearer through chat or an Operation alone.</p> : (
          <div className="studio-outline-list">
            {story.surfaces.map((surface, index) => (
              <details key={index} id={`surface-${index}`} className="studio-outline-row">
                <summary>
                  <ChevronDown aria-hidden="true" />
                  <span className="studio-outline-title">{surface.name || `Surface ${index + 1}`}</span>
                  <span className="studio-outline-purpose">{surface.purpose || "No purpose defined"}</span>
                  <span className="studio-outline-meta">{surface.policies.length} rules</span>
                </summary>
                <div className="studio-outline-content">
                  <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
                    <Field><FieldLabel htmlFor={`surface-name-${index}`}>Surface name</FieldLabel><Input id={`surface-name-${index}`} value={surface.name} disabled={disabled} onChange={(event) => updateSurface(index, { name: event.target.value })} /></Field>
                    <RemoveButton label={`Remove surface ${surface.name}`} disabled={disabled} onClick={() => removeSurface(index)} />
                  </div>
                  <Field><FieldLabel htmlFor={`surface-purpose-${index}`}>Purpose</FieldLabel><Textarea id={`surface-purpose-${index}`} className="min-h-16" value={surface.purpose} disabled={disabled} onChange={(event) => updateSurface(index, { purpose: event.target.value })} /></Field>
                  <AgentPolicyList label={`${surface.name || `Surface ${index + 1}`} rules`} policies={surface.policies} disabled={disabled} onChange={(policies) => updateSurface(index, { policies })} />
                </div>
              </details>
            ))}
          </div>
        )}
      </StudioSection>

      <StudioSection id="operations-heading" title="Operations" description="Review every authoritative product action legal in this behavior.">
        <OperationInventory story={story} disabled={disabled} onChange={onChange} />
      </StudioSection>

      <StudioSection
        id="suggested-actions-heading"
        title="Suggested actions"
        description="Optional chat invitations. Each suggestion references an Operation; it does not create authority."
        action={<Button type="button" size="sm" variant="outline" disabled={disabled || story.operations.length === 0} onClick={() => onChange({ suggestedActions: [...story.suggestedActions, { id: `suggested-action-${Date.now()}`, label: "", operationName: story.operations[0]?.name ?? "", visibility: "" }] })}><Plus /> Add suggested action</Button>}
      >
        {story.operations.length === 0 && <p className="text-xs text-muted-foreground">Define an Operation before adding a SuggestedAction.</p>}
        {story.suggestedActions.length === 0 && story.operations.length > 0 && <p className="studio-empty-state">No SuggestedActions defined for this behavior.</p>}
        {story.suggestedActions.length > 0 && (
          <div className="studio-outline-list">
            {story.suggestedActions.map((action, index) => (
              <div key={action.id} id={`suggested-action-${index}`} className="studio-outline-content border-b border-border py-4 last:border-b-0">
                <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] sm:items-end">
                  <Field><FieldLabel htmlFor={`suggested-action-label-${action.id}`}>Label</FieldLabel><Input id={`suggested-action-label-${action.id}`} value={action.label} disabled={disabled} onChange={(event) => updateSuggestedAction(index, { label: event.target.value })} /></Field>
                  <Field><FieldLabel htmlFor={`suggested-action-operation-${action.id}`}>Operation</FieldLabel><select id={`suggested-action-operation-${action.id}`} className="h-9 w-full rounded-md border border-input bg-[var(--studio-field)] px-2.5 text-[13px] text-foreground outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/15" value={action.operationName} disabled={disabled} onChange={(event) => updateSuggestedAction(index, { operationName: event.target.value })}><option value="">Select an Operation</option>{story.operations.map((operation, operationIndex) => <option key={`${operation.name}-${operationIndex}`} value={operation.name}>{operation.name}</option>)}</select></Field>
                  <RemoveButton label={`Remove suggested action ${index + 1}`} disabled={disabled} onClick={() => onChange({ suggestedActions: story.suggestedActions.filter((_, itemIndex) => itemIndex !== index) })} />
                  <Field className="sm:col-span-2"><FieldLabel htmlFor={`suggested-action-visibility-${action.id}`}>Visibility details</FieldLabel><Input id={`suggested-action-visibility-${action.id}`} value={action.visibility} disabled={disabled} placeholder="Optional condition for presenting this suggestion" onChange={(event) => updateSuggestedAction(index, { visibility: event.target.value })} /><FieldDescription className="text-xs">Presentation only; the referenced Operation remains the authority.</FieldDescription></Field>
                </div>
              </div>
            ))}
          </div>
        )}
      </StudioSection>
    </div>
  )
}

function AssociationPicker({ label, emptyText, options, selected, disabled, onChange }: { label: string; emptyText: string; options: string[]; selected: string[]; disabled: boolean; onChange: (selected: string[]) => void }) {
  function toggle(option: string) {
    onChange(selected.includes(option) ? selected.filter((item) => item !== option) : [...selected, option])
  }
  return (
    <fieldset>
      <legend className="text-xs font-medium">{label}</legend>
      {options.length === 0 ? <p className="mt-2 text-xs text-muted-foreground">{emptyText}</p> : (
        <div className="studio-association-list">
          {options.map((option, index) => {
            const active = selected.includes(option)
            return <button key={`${option}-${index}`} type="button" aria-pressed={active} disabled={disabled} onClick={() => toggle(option)}>{active && <Check aria-hidden="true" />}{option || `Unnamed ${label.slice(0, -1)}`}</button>
          })}
        </div>
      )}
    </fieldset>
  )
}

function RemoveButton({ label, disabled, onClick }: { label: string; disabled: boolean; onClick: () => void }) {
  return <Button type="button" size="icon" variant="ghost" aria-label={label} disabled={disabled} onClick={onClick}><Trash2 /></Button>
}
