import { Check, CheckCircle2, ChevronLeft, CircleAlert, Plus, Trash2, X } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { EVAL_COVERAGE, getBehaviorEvalCaseIssues, getBehaviorEvalReadiness } from "@/workbench/evaluationReadiness"
import { EvaluationStatus } from "@/workbench/EvaluationStatus"
import { EvaluationActionPlanEditor } from "@/workbench/EvaluationActionPlanEditor"
import type { BehaviorEvalCase, DesignFeature, DesignStory, DeterministicExpectations } from "@/workbench/types"

function emptyExpectations(story: DesignStory): DeterministicExpectations {
  return {
    startingBehavior: story.title,
    finalBehavior: story.title,
    allowedFinalBehaviors: [],
    authentication: "unchanged",
    requiredOperations: [],
    allowedOperations: [],
    forbiddenOperations: [],
    requiredSurfaces: [],
    requiredSuggestedActions: [],
    forbiddenOutcomes: [],
  }
}

function newCase(story: DesignStory): BehaviorEvalCase {
  return {
    id: `behavior-eval-${Date.now()}`,
    title: "New eval case",
    enabled: true,
    blocking: true,
    coverage: ["normal"],
    input: "",
    referenceResponse: "",
    requiredCriteria: [],
    forbiddenCriteria: [],
    expectations: emptyExpectations(story),
    actionPlan: {
      preconditions: ["Describe the required product state before this behavior begins."],
      steps: [
        { id: `behavior-eval-${Date.now()}-opening`, kind: "message", source: "authored-input" },
        { id: `behavior-eval-${Date.now()}-final`, kind: "checkpoint", label: "Final product state", stateAssertions: ["Describe the product state that must be proven."] },
      ],
    },
  }
}

export function BehaviorEvalEditor({ feature, story, disabled, onChange }: {
  feature: DesignFeature
  story: DesignStory
  disabled: boolean
  onChange: (patch: Partial<DesignStory>) => void
}) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)
  const readiness = getBehaviorEvalReadiness(story, feature)
  const activeCase = activeIndex === null ? null : story.behaviorEvals[activeIndex]
  const covered = new Set(story.behaviorEvals.filter((item) => item.enabled).flatMap((item) => item.coverage))
  const featureOperations = feature.stories.flatMap((item) => item.operations.map((operation) => operation.name))
  const featureSurfaces = feature.stories.flatMap((item) => item.surfaces.map((surface) => surface.name))
  const featureActions = feature.stories.flatMap((item) => item.suggestedActions.map((action) => ({ behavior: item.title, label: action.label })))

  function updateCase(index: number, patch: Partial<BehaviorEvalCase>) {
    onChange({ behaviorEvals: story.behaviorEvals.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) })
  }

  function addCase() {
    const next = newCase(story)
    onChange({ behaviorEvals: [...story.behaviorEvals, next] })
    setActiveIndex(story.behaviorEvals.length)
  }

  return (
    <>
      <div className="studio-eval-summary" aria-label="Behavior eval coverage">
        <div>
          <strong>{readiness.isReady ? "Coverage complete" : `${readiness.issues.length} coverage issues`}</strong>
          <span>{story.behaviorEvals.length} cases · design definitions only</span>
        </div>
        <EvaluationStatus />
      </div>
      <div className="studio-coverage-strip">
        {EVAL_COVERAGE.map((category) => <span key={category.id} data-covered={covered.has(category.id)}>{covered.has(category.id) && <Check aria-hidden="true" />}{category.label}</span>)}
      </div>
      <div className="studio-inventory-toolbar">
        <span>Semantic criteria and product-state expectations</span>
        <Button type="button" size="sm" variant="outline" disabled={disabled} onClick={addCase}><Plus /> Add case</Button>
      </div>
      {story.behaviorEvals.length === 0 ? <p className="studio-empty-state">No behavior evals authored. Add a normal case, then cover each relevant boundary.</p> : (
        <div className="studio-eval-inventory" role="list" aria-label="Behavior evals">
          <div className="studio-eval-columns" aria-hidden="true"><span>Case</span><span>Coverage</span><span>Status</span><span>Result</span></div>
          {story.behaviorEvals.map((evalCase, index) => {
            const issues = getBehaviorEvalCaseIssues(story, evalCase, index, feature)
            return (
              <button key={evalCase.id || index} id={`behavior-eval-${index}`} type="button" className="studio-eval-row" onClick={() => setActiveIndex(index)}>
                <span className="studio-eval-name">{evalCase.title || `Eval case ${index + 1}`}<small>{evalCase.blocking ? "Blocking" : "Optional"}</small></span>
                <span className="studio-eval-coverage">{evalCase.coverage.map((tag) => tag[0].toUpperCase() + tag.slice(1)).join(" · ") || "No coverage"}</span>
                <span className={issues.length === 0 ? "studio-contract-ready" : "studio-contract-incomplete"}>{issues.length === 0 ? <CheckCircle2 /> : <CircleAlert />}{issues.length === 0 ? "Complete" : `${issues.length} issues`}</span>
                <EvaluationStatus compact definition={evalCase} evaluationId={evalCase.id} />
              </button>
            )
          })}
        </div>
      )}
      {activeCase && activeIndex !== null && (
        <div className="studio-eval-drawer" role="dialog" aria-modal="true" aria-label={activeCase.title || `Eval case ${activeIndex + 1}`}>
          <header className="studio-operation-drawer-header">
            <div className="min-w-0"><p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">Behavior eval</p><h2 className="truncate text-base font-semibold">{activeCase.title || `Eval case ${activeIndex + 1}`}</h2></div>
            <Button type="button" size="icon-sm" variant="ghost" aria-label="Close eval case" onClick={() => setActiveIndex(null)}><X /></Button>
          </header>
          <div className="studio-operation-drawer-content">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field><FieldLabel htmlFor={`eval-title-${activeIndex}`}>Case title</FieldLabel><Input id={`eval-title-${activeIndex}`} value={activeCase.title} disabled={disabled} onChange={(event) => updateCase(activeIndex, { title: event.target.value })} /></Field>
              <Field><FieldLabel htmlFor={`eval-id-${activeIndex}`}>Stable ID</FieldLabel><Input id={`eval-id-${activeIndex}`} value={activeCase.id} disabled={disabled} onChange={(event) => updateCase(activeIndex, { id: event.target.value })} /></Field>
            </div>
            <div className="studio-toggle-row">
              <label><input type="checkbox" checked={activeCase.enabled} disabled={disabled} onChange={(event) => updateCase(activeIndex, { enabled: event.target.checked })} /> Enabled</label>
              <label><input type="checkbox" checked={activeCase.blocking} disabled={disabled} onChange={(event) => updateCase(activeIndex, { blocking: event.target.checked })} /> Blocks implementation readiness</label>
              <EvaluationStatus compact definition={activeCase} evaluationId={activeCase.id} />
            </div>
            <fieldset><legend className="text-xs font-medium">Coverage</legend><div className="studio-association-list">{EVAL_COVERAGE.map((category) => { const active = activeCase.coverage.includes(category.id); return <button key={category.id} type="button" aria-pressed={active} disabled={disabled} onClick={() => updateCase(activeIndex, { coverage: active ? activeCase.coverage.filter((item) => item !== category.id) : [...activeCase.coverage, category.id] })}>{active && <Check />}{category.label}</button> })}</div></fieldset>
            <Field><FieldLabel htmlFor={`eval-input-${activeIndex}`}>User input</FieldLabel><Textarea id={`eval-input-${activeIndex}`} className="min-h-24" value={activeCase.input} disabled={disabled} onChange={(event) => updateCase(activeIndex, { input: event.target.value })} /></Field>
            <Field><FieldLabel htmlFor={`eval-reference-${activeIndex}`}>Reference response (optional)</FieldLabel><Textarea id={`eval-reference-${activeIndex}`} className="min-h-20" value={activeCase.referenceResponse} disabled={disabled} onChange={(event) => updateCase(activeIndex, { referenceResponse: event.target.value })} /><FieldDescription>Semantic direction for the judge. Wording is never matched exactly.</FieldDescription></Field>
            <StringList title="Required meaning" values={activeCase.requiredCriteria} disabled={disabled} onChange={(requiredCriteria) => updateCase(activeIndex, { requiredCriteria })} />
            <StringList title="Forbidden meaning" values={activeCase.forbiddenCriteria} disabled={disabled} onChange={(forbiddenCriteria) => updateCase(activeIndex, { forbiddenCriteria })} />
            <EvaluationActionPlanEditor plan={activeCase.actionPlan} actionOptions={featureActions} surfaceOptions={featureSurfaces} allowAdaptiveMessages={false} disabled={disabled} onChange={(actionPlan) => updateCase(activeIndex, { actionPlan })} />
            <div className="studio-eval-subsection"><h3>Runtime facts</h3><p>Product-semantic expectations only. The external runner resolves these through the implementation manifest.</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field><FieldLabel htmlFor={`eval-start-${activeIndex}`}>Starting behavior</FieldLabel><Input id={`eval-start-${activeIndex}`} value={activeCase.expectations.startingBehavior} disabled={disabled} onChange={(event) => updateCase(activeIndex, { expectations: { ...activeCase.expectations, startingBehavior: event.target.value } })} /></Field>
                <Field><FieldLabel htmlFor={`eval-final-${activeIndex}`}>Final behavior</FieldLabel><Input id={`eval-final-${activeIndex}`} value={activeCase.expectations.finalBehavior} disabled={disabled} onChange={(event) => updateCase(activeIndex, { expectations: { ...activeCase.expectations, finalBehavior: event.target.value } })} /></Field>
              </div>
              <Field><FieldLabel htmlFor={`eval-auth-${activeIndex}`}>Authentication state</FieldLabel><select id={`eval-auth-${activeIndex}`} className="studio-select" value={activeCase.expectations.authentication} disabled={disabled} onChange={(event) => updateCase(activeIndex, { expectations: { ...activeCase.expectations, authentication: event.target.value as DeterministicExpectations["authentication"] } })}><option value="unchanged">Unchanged</option><option value="public">Public</option><option value="authenticated">Authenticated</option></select></Field>
              <EvaluationAssociation title="Required Operations" options={featureOperations} selected={activeCase.expectations.requiredOperations} disabled={disabled} onChange={(requiredOperations) => updateCase(activeIndex, { expectations: { ...activeCase.expectations, requiredOperations } })} />
              <EvaluationAssociation title="Allowed Operations" options={featureOperations} selected={activeCase.expectations.allowedOperations} disabled={disabled} onChange={(allowedOperations) => updateCase(activeIndex, { expectations: { ...activeCase.expectations, allowedOperations } })} />
              <EvaluationAssociation title="Forbidden Operations" options={featureOperations} selected={activeCase.expectations.forbiddenOperations} disabled={disabled} onChange={(forbiddenOperations) => updateCase(activeIndex, { expectations: { ...activeCase.expectations, forbiddenOperations } })} />
              <EvaluationAssociation title="Required Surfaces" options={featureSurfaces} selected={activeCase.expectations.requiredSurfaces} disabled={disabled} onChange={(requiredSurfaces) => updateCase(activeIndex, { expectations: { ...activeCase.expectations, requiredSurfaces } })} />
              <EvaluationAssociation title="Required SuggestedActions" options={featureActions.map((item) => item.label)} selected={activeCase.expectations.requiredSuggestedActions} disabled={disabled} onChange={(requiredSuggestedActions) => updateCase(activeIndex, { expectations: { ...activeCase.expectations, requiredSuggestedActions } })} />
              <StringList title="Forbidden runtime outcomes" values={activeCase.expectations.forbiddenOutcomes} disabled={disabled} onChange={(forbiddenOutcomes) => updateCase(activeIndex, { expectations: { ...activeCase.expectations, forbiddenOutcomes } })} />
            </div>
          </div>
          <footer className="studio-operation-drawer-footer">
            <Button type="button" variant="ghost" className="text-destructive" disabled={disabled} onClick={() => { onChange({ behaviorEvals: story.behaviorEvals.filter((_, itemIndex) => itemIndex !== activeIndex) }); setActiveIndex(null) }}><Trash2 /> Remove case</Button>
            <Button type="button" onClick={() => setActiveIndex(null)}><ChevronLeft /> Done</Button>
          </footer>
        </div>
      )}
    </>
  )
}

export function StringList({ title, values, disabled, onChange }: { title: string; values: string[]; disabled: boolean; onChange: (values: string[]) => void }) {
  return <div className="studio-eval-subsection"><div className="studio-eval-subsection-heading"><h3>{title}</h3><Button type="button" size="xs" variant="outline" disabled={disabled} onClick={() => onChange([...values, ""])}><Plus /> Add</Button></div>{values.length === 0 ? <p>No criteria defined.</p> : <div className="studio-string-list">{values.map((value, index) => <div key={index}><Textarea aria-label={`${title} ${index + 1}`} value={value} disabled={disabled} onChange={(event) => onChange(values.map((item, itemIndex) => itemIndex === index ? event.target.value : item))} /><Button type="button" size="icon-xs" variant="ghost" aria-label={`Remove ${title.toLowerCase()} ${index + 1}`} disabled={disabled} onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))}><Trash2 /></Button></div>)}</div>}</div>
}

export function EvaluationAssociation({ title, options, selected, disabled, onChange }: { title: string; options: string[]; selected: string[]; disabled: boolean; onChange: (values: string[]) => void }) {
  return <fieldset><legend className="text-xs font-medium">{title}</legend>{options.length === 0 ? <p className="mt-2 text-xs text-muted-foreground">No matching design items exist.</p> : <div className="studio-association-list">{options.map((option) => { const active = selected.includes(option); return <button key={option} type="button" aria-pressed={active} disabled={disabled} onClick={() => onChange(active ? selected.filter((item) => item !== option) : [...selected, option])}>{active && <Check />}{option}</button> })}</div>}</fieldset>
}
