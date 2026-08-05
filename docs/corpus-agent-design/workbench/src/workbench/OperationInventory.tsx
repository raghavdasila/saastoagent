import { useState } from "react"
import { AlertCircle, Check, CheckCircle2, Plus, Trash2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { AgentPolicyList } from "@/workbench/AgentPolicyList"
import { getStoryReadiness } from "@/workbench/readiness"
import type { DesignStory, OperationDesign } from "@/workbench/types"

export function OperationInventory({ story, disabled, onChange }: {
  story: DesignStory
  disabled: boolean
  onChange: (patch: Partial<DesignStory>) => void
}) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const readiness = getStoryReadiness(story)

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
    setSelectedIndex(null)
  }

  function addOperation() {
    const nextIndex = story.operations.length
    onChange({ operations: [...story.operations, blankOperation()] })
    setSelectedIndex(nextIndex)
  }

  const selectedOperation = selectedIndex === null ? null : story.operations[selectedIndex]

  return (
    <>
      <div className="studio-inventory-toolbar">
        <p>{story.operations.length === 0 ? "No authoritative actions defined." : `${story.operations.length} authoritative ${story.operations.length === 1 ? "action" : "actions"} available here.`}</p>
        <Button type="button" size="sm" variant="outline" disabled={disabled} onClick={addOperation}><Plus /> Add operation</Button>
      </div>

      {story.operations.length === 0 ? (
        <p className="studio-empty-state">A behavior may have no Operation when it only presents information. Add one when Corpus can perform an authoritative product action here.</p>
      ) : (
        <div className="studio-operation-inventory" role="list" aria-label="Operations">
          <div className="studio-operation-columns" aria-hidden="true">
            <span>Operation</span><span>Intended effect</span><span>Contract</span>
          </div>
          {story.operations.map((operation, index) => {
            const operationIssues = readiness.blockers.filter((issue) => issue.targetId === `operation-${index}`)
            return (
              <div key={`${operation.name}-${index}`} role="listitem">
                <button id={`operation-${index}`} type="button" className="studio-operation-row" onClick={() => setSelectedIndex(index)}>
                  <span className="studio-operation-name">{operation.name || `Operation ${index + 1}`}</span>
                  <span className="studio-operation-effect">{operation.purpose || "No intended effect defined"}</span>
                  <span className={operationIssues.length === 0 ? "studio-contract-ready" : "studio-contract-incomplete"}>
                    {operationIssues.length === 0 ? <CheckCircle2 aria-hidden="true" /> : <AlertCircle aria-hidden="true" />}
                    {operationIssues.length === 0 ? "Complete" : `${operationIssues.length} missing`}
                  </span>
                </button>
              </div>
            )
          })}
        </div>
      )}

      {selectedOperation && selectedIndex !== null && (
        <aside role="dialog" aria-modal="false" aria-labelledby="operation-drawer-heading" className="studio-operation-drawer">
          <header className="studio-operation-drawer-header">
            <div>
              <p className="text-xs font-medium text-muted-foreground">Operation contract</p>
              <h3 id="operation-drawer-heading" className="mt-1 text-lg font-semibold">{selectedOperation.name || `Operation ${selectedIndex + 1}`}</h3>
            </div>
            <Button type="button" size="icon" variant="ghost" aria-label="Close operation editor" onClick={() => setSelectedIndex(null)}><X /></Button>
          </header>
          <div className="studio-operation-drawer-content">
            <Field>
              <FieldLabel htmlFor={`operation-name-${selectedIndex}`}>Operation name</FieldLabel>
              <Input id={`operation-name-${selectedIndex}`} value={selectedOperation.name} disabled={disabled} onChange={(event) => updateOperation(selectedIndex, { name: event.target.value })} />
            </Field>
            <DetailField id={`operation-purpose-${selectedIndex}`} label="Intended effect" description="The authoritative product result, state change, navigation outcome, or observed response." value={selectedOperation.purpose} disabled={disabled} onChange={(purpose) => updateOperation(selectedIndex, { purpose })} />
            <DetailField id={`operation-inputs-${selectedIndex}`} label="Inputs and prerequisites" description="State what Corpus needs, or explicitly say that no input is required." value={selectedOperation.inputs} disabled={disabled} onChange={(inputs) => updateOperation(selectedIndex, { inputs })} />
            <DetailField id={`operation-outcomes-${selectedIndex}`} label="Observable outcomes" description="Identify success and material failure outcomes without claiming unavailable evidence." value={selectedOperation.outcomes} disabled={disabled} onChange={(outcomes) => updateOperation(selectedIndex, { outcomes })} />
            <DetailField id={`operation-safety-${selectedIndex}`} label="Safety and review" description="State review, privacy, authority, and irreversible-action boundaries, or explain why none apply." value={selectedOperation.safetyAndReview} disabled={disabled} onChange={(safetyAndReview) => updateOperation(selectedIndex, { safetyAndReview })} />
            <DetailField id={`operation-recovery-${selectedIndex}`} label="Failure and recovery" description="Keep failures visible and define the valid next action. Do not invent success or silent retry." value={selectedOperation.recovery} disabled={disabled} onChange={(recovery) => updateOperation(selectedIndex, { recovery })} />
            <AgentPolicyList label={`${selectedOperation.name || `Operation ${selectedIndex + 1}`} rules`} policies={selectedOperation.policies} disabled={disabled} onChange={(policies) => updateOperation(selectedIndex, { policies })} />
          </div>
          <footer className="studio-operation-drawer-footer">
            <Button type="button" variant="ghost" disabled={disabled} onClick={() => removeOperation(selectedIndex)}><Trash2 /> Remove operation</Button>
            <Button type="button" onClick={() => setSelectedIndex(null)}><Check /> Done</Button>
          </footer>
        </aside>
      )}
    </>
  )
}

function DetailField({ id, label, description, value, disabled, onChange }: {
  id: string
  label: string
  description: string
  value: string
  disabled: boolean
  onChange: (value: string) => void
}) {
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Textarea id={id} className="min-h-24" value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} />
      <FieldDescription className="text-xs">{description}</FieldDescription>
    </Field>
  )
}

function blankOperation(): OperationDesign {
  return { name: "New operation", purpose: "", inputs: "", outcomes: "", safetyAndReview: "", recovery: "", policies: [] }
}
