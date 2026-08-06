import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import type { EvaluationActionPlan, EvaluationActionStep } from "@/workbench/types"

export function EvaluationActionPlanEditor({
  plan,
  actionOptions,
  surfaceOptions,
  allowAdaptiveMessages,
  disabled,
  onChange,
}: {
  plan: EvaluationActionPlan
  actionOptions: Array<{ behavior: string; label: string }>
  surfaceOptions: string[]
  allowAdaptiveMessages: boolean
  disabled: boolean
  onChange: (plan: EvaluationActionPlan) => void
}) {
  const updateStep = (index: number, step: EvaluationActionStep) => onChange({ ...plan, steps: plan.steps.map((item, itemIndex) => itemIndex === index ? step : item) })
  const removeStep = (index: number) => onChange({ ...plan, steps: plan.steps.filter((_, itemIndex) => itemIndex !== index) })
  const moveStep = (index: number, offset: -1 | 1) => {
    const target = index + offset
    if (target < 0 || target >= plan.steps.length) return
    const steps = [...plan.steps]
    ;[steps[index], steps[target]] = [steps[target], steps[index]]
    onChange({ ...plan, steps })
  }
  const addStep = (kind: EvaluationActionStep["kind"]) => {
    const id = `eval-step-${Date.now()}`
    const step: EvaluationActionStep = kind === "message"
      ? { id, kind, source: "adaptive-tester" }
      : kind === "suggested-action"
        ? { id, kind, behavior: actionOptions[0]?.behavior ?? "", action: actionOptions[0]?.label ?? "" }
        : kind === "surface-submit"
          ? { id, kind, surface: surfaceOptions[0] ?? "", inputIntent: "" }
          : { id, kind, label: "Product-state checkpoint", stateAssertions: [""] }
    const finalCheckpoint = plan.steps.at(-1)?.kind === "checkpoint" ? plan.steps.at(-1) : null
    const prefix = finalCheckpoint ? plan.steps.slice(0, -1) : plan.steps
    onChange({ ...plan, steps: finalCheckpoint ? [...prefix, step, finalCheckpoint] : [...prefix, step] })
  }

  return (
    <section className="studio-eval-subsection">
      <h3>Authored action plan</h3>
      <p>Ordered product-semantic interactions only. The implementation manifest resolves runtime identifiers and test-data adapters.</p>
      <PlanStringList title="Product-state preconditions" values={plan.preconditions} disabled={disabled} onChange={(preconditions) => onChange({ ...plan, preconditions })} />
      <div className="studio-eval-subsection-heading">
        <h3>Ordered steps</h3>
        <div className="flex flex-wrap gap-2">
          {allowAdaptiveMessages && <Button type="button" size="xs" variant="outline" disabled={disabled} onClick={() => addStep("message")}><Plus /> Adaptive message</Button>}
          <Button type="button" size="xs" variant="outline" disabled={disabled || actionOptions.length === 0} onClick={() => addStep("suggested-action")}><Plus /> Suggested action</Button>
          <Button type="button" size="xs" variant="outline" disabled={disabled || surfaceOptions.length === 0} onClick={() => addStep("surface-submit")}><Plus /> Surface submit</Button>
          <Button type="button" size="xs" variant="outline" disabled={disabled} onClick={() => addStep("checkpoint")}><Plus /> Checkpoint</Button>
        </div>
      </div>
      <div className="space-y-3">
        {plan.steps.map((step, index) => (
          <div key={`${step.id}-${index}`} className="rounded-md border border-border bg-background/60 p-3">
            <div className="mb-3 flex items-center justify-between gap-3">
              <strong className="text-xs uppercase tracking-[0.08em] text-muted-foreground">{index + 1}. {step.kind.replace("-", " ")}</strong>
              <div className="flex gap-1">
                <Button type="button" size="icon-xs" variant="ghost" aria-label={`Move step ${index + 1} up`} disabled={disabled || index === 0} onClick={() => moveStep(index, -1)}><ArrowUp /></Button>
                <Button type="button" size="icon-xs" variant="ghost" aria-label={`Move step ${index + 1} down`} disabled={disabled || index === plan.steps.length - 1} onClick={() => moveStep(index, 1)}><ArrowDown /></Button>
                <Button type="button" size="icon-xs" variant="ghost" aria-label={`Remove step ${index + 1}`} disabled={disabled} onClick={() => removeStep(index)}><Trash2 /></Button>
              </div>
            </div>
            <Field><FieldLabel htmlFor={`${step.id}-${index}-id`}>Stable step ID</FieldLabel><Input id={`${step.id}-${index}-id`} value={step.id} disabled={disabled} onChange={(event) => updateStep(index, { ...step, id: event.target.value })} /></Field>
            {step.kind === "message" && <Field><FieldLabel htmlFor={`${step.id}-${index}-source`}>Message source</FieldLabel><select id={`${step.id}-${index}-source`} className="studio-select" value={step.source} disabled={disabled} onChange={(event) => updateStep(index, { ...step, source: event.target.value as "authored-input" | "adaptive-tester" })}><option value="authored-input">Authored evaluation input</option>{allowAdaptiveMessages && <option value="adaptive-tester">Adaptive tester dialogue</option>}</select><FieldDescription>The evaluator controls when dialogue happens; the tester controls only adaptive message wording.</FieldDescription></Field>}
            {step.kind === "suggested-action" && <Field><FieldLabel htmlFor={`${step.id}-${index}-action`}>Suggested action</FieldLabel><select id={`${step.id}-${index}-action`} className="studio-select" value={`${step.behavior}\u0000${step.action}`} disabled={disabled} onChange={(event) => { const option = actionOptions.find((item) => `${item.behavior}\u0000${item.label}` === event.target.value); if (option) updateStep(index, { ...step, behavior: option.behavior, action: option.label }) }}>{actionOptions.map((option) => <option key={`${option.behavior}\u0000${option.label}`} value={`${option.behavior}\u0000${option.label}`}>{option.behavior} / {option.label}</option>)}</select></Field>}
            {step.kind === "surface-submit" && <><Field><FieldLabel htmlFor={`${step.id}-${index}-surface`}>Surface</FieldLabel><select id={`${step.id}-${index}-surface`} className="studio-select" value={step.surface} disabled={disabled} onChange={(event) => updateStep(index, { ...step, surface: event.target.value })}>{surfaceOptions.map((option) => <option key={option} value={option}>{option}</option>)}</select></Field><Field><FieldLabel htmlFor={`${step.id}-${index}-intent`}>Input intent</FieldLabel><Textarea id={`${step.id}-${index}-intent`} value={step.inputIntent} disabled={disabled} onChange={(event) => updateStep(index, { ...step, inputIntent: event.target.value })} /><FieldDescription>Describe valid, invalid, existing, unique, or otherwise meaningful test input without storing credentials or tokens.</FieldDescription></Field></>}
            {step.kind === "checkpoint" && <><Field><FieldLabel htmlFor={`${step.id}-${index}-label`}>Checkpoint label</FieldLabel><Input id={`${step.id}-${index}-label`} value={step.label} disabled={disabled} onChange={(event) => updateStep(index, { ...step, label: event.target.value })} /></Field><PlanStringList title="Product-state assertions" values={step.stateAssertions} disabled={disabled} onChange={(stateAssertions) => updateStep(index, { ...step, stateAssertions })} /></>}
          </div>
        ))}
      </div>
    </section>
  )
}

function PlanStringList({ title, values, disabled, onChange }: { title: string; values: string[]; disabled: boolean; onChange: (values: string[]) => void }) {
  return <div className="studio-eval-subsection"><div className="studio-eval-subsection-heading"><h3>{title}</h3><Button type="button" size="xs" variant="outline" disabled={disabled} onClick={() => onChange([...values, ""])}><Plus /> Add</Button></div>{values.length === 0 ? <p>No values defined.</p> : <div className="studio-string-list">{values.map((value, index) => <div key={index}><Textarea aria-label={`${title} ${index + 1}`} value={value} disabled={disabled} onChange={(event) => onChange(values.map((item, itemIndex) => itemIndex === index ? event.target.value : item))} /><Button type="button" size="icon-xs" variant="ghost" aria-label={`Remove ${title.toLowerCase()} ${index + 1}`} disabled={disabled} onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))}><Trash2 /></Button></div>)}</div>}</div>
}
