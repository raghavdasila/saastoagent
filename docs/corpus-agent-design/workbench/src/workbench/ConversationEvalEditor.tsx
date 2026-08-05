import { Bot, CheckCircle2, CircleAlert, Plus, Trash2, X } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { EvaluationAssociation, StringList } from "@/workbench/BehaviorEvalEditor"
import { EvaluationStatus } from "@/workbench/EvaluationStatus"
import { getConversationScenarioIssues, getFeatureConversationEvalReadiness } from "@/workbench/evaluationReadiness"
import type { DesignFeature, DeterministicExpectations, FeatureConversationEvalScenario } from "@/workbench/types"

function newScenario(feature: DesignFeature): FeatureConversationEvalScenario {
  const startingBehavior = feature.stories[0]?.title ?? ""
  return {
    id: `conversation-eval-${Date.now()}`,
    title: "New conversation eval",
    enabled: true,
    blocking: true,
    openingMessage: "",
    hiddenGoal: "",
    persona: "",
    facts: [],
    mayDisclose: [],
    withholdUntilAsked: [],
    bypassAttempts: [],
    perTurnCriteria: [],
    finalRequiredCriteria: [],
    finalForbiddenCriteria: [],
    expectations: {
      startingBehavior,
      finalBehavior: startingBehavior,
      allowedFinalBehaviors: [],
      authentication: "unchanged",
      requiredOperations: [],
      allowedOperations: [],
      forbiddenOperations: [],
      requiredSurfaces: [],
      requiredSuggestedActions: [],
      forbiddenOutcomes: [],
    },
    successCondition: "",
    failureConditions: [],
    stoppingConditions: [],
    maxTurns: 8,
  }
}

export function ConversationEvalEditor({ feature, onChange }: { feature: DesignFeature; onChange: (patch: Partial<DesignFeature>) => void }) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)
  const readiness = getFeatureConversationEvalReadiness(feature)
  const active = activeIndex === null ? null : feature.conversationEvals[activeIndex]

  function update(index: number, patch: Partial<FeatureConversationEvalScenario>) {
    onChange({ conversationEvals: feature.conversationEvals.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) })
  }

  function add() {
    onChange({ conversationEvals: [...feature.conversationEvals, newScenario(feature)] })
    setActiveIndex(feature.conversationEvals.length)
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 p-4 sm:p-6 lg:p-8">
      <div className="flex items-start justify-between gap-4 border-b border-border pb-5">
        <div className="flex items-start gap-3">
          <div className="grid size-9 shrink-0 place-items-center rounded-md border border-primary/20 bg-primary/10 text-primary"><Bot className="size-4" /></div>
          <div><p className="text-xs font-medium text-muted-foreground">Corpus / {feature.name}</p><h2 id="conversation-evals-heading" className="mt-0.5 text-xl font-semibold tracking-[-0.025em]">Conversation evals</h2><p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">An adaptive tester follows its hidden goal and facts while Corpus chooses the clarification order. A separate judge evaluates the finished conversation.</p></div>
        </div>
        <Button type="button" variant="outline" onClick={add}><Plus /> Add scenario</Button>
      </div>
      <div className="studio-eval-summary">
        <div><strong>{readiness.isReady ? "Definitions complete" : `${readiness.issues.length} definition issues`}</strong><span>{feature.conversationEvals.length} adaptive scenarios · no scripted transcript</span></div>
        <EvaluationStatus />
      </div>
      {feature.conversationEvals.length === 0 ? <p className="studio-empty-state">No conversation evals authored for this feature.</p> : (
        <div className="studio-eval-inventory" role="list" aria-label="Conversation evals">
          <div className="studio-conversation-columns" aria-hidden="true"><span>Scenario</span><span>Opening</span><span>Turns</span><span>Status</span><span>Result</span></div>
          {feature.conversationEvals.map((scenario, index) => {
            const issues = getConversationScenarioIssues(feature, scenario, index)
            return <button key={scenario.id || index} id={`conversation-eval-${index}`} type="button" className="studio-conversation-row" onClick={() => setActiveIndex(index)}><span className="studio-eval-name">{scenario.title || `Scenario ${index + 1}`}<small>{scenario.blocking ? "Blocking" : "Optional"}</small></span><span className="studio-eval-coverage">{scenario.openingMessage || "No opening message"}</span><span className="studio-eval-turns">≤ {scenario.maxTurns}</span><span className={issues.length === 0 ? "studio-contract-ready" : "studio-contract-incomplete"}>{issues.length === 0 ? <CheckCircle2 /> : <CircleAlert />}{issues.length === 0 ? "Complete" : `${issues.length} issues`}</span><EvaluationStatus compact evaluationId={scenario.id} /></button>
          })}
        </div>
      )}
      {active && activeIndex !== null && (
        <div className="studio-eval-drawer" role="dialog" aria-modal="true" aria-label={active.title || `Conversation eval ${activeIndex + 1}`}>
          <header className="studio-operation-drawer-header"><div className="min-w-0"><p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">Adaptive conversation eval</p><h2 className="truncate text-base font-semibold">{active.title || `Scenario ${activeIndex + 1}`}</h2></div><Button type="button" size="icon-sm" variant="ghost" aria-label="Close conversation eval" onClick={() => setActiveIndex(null)}><X /></Button></header>
          <div className="studio-operation-drawer-content">
            <div className="studio-toggle-row"><label><input type="checkbox" checked={active.enabled} onChange={(event) => update(activeIndex, { enabled: event.target.checked })} /> Enabled</label><label><input type="checkbox" checked={active.blocking} onChange={(event) => update(activeIndex, { blocking: event.target.checked })} /> Blocks implementation readiness</label><EvaluationStatus compact evaluationId={active.id} /></div>
            <section className="studio-eval-subsection"><h3>Scenario</h3><p>The tester keeps this goal while adapting each user turn to Corpus.</p><div className="grid gap-4 sm:grid-cols-2"><Field><FieldLabel htmlFor={`scenario-title-${activeIndex}`}>Scenario title</FieldLabel><Input id={`scenario-title-${activeIndex}`} value={active.title} onChange={(event) => update(activeIndex, { title: event.target.value })} /></Field><Field><FieldLabel htmlFor={`scenario-id-${activeIndex}`}>Stable ID</FieldLabel><Input id={`scenario-id-${activeIndex}`} value={active.id} onChange={(event) => update(activeIndex, { id: event.target.value })} /></Field></div><Field><FieldLabel htmlFor={`scenario-opening-${activeIndex}`}>Opening user message</FieldLabel><Textarea id={`scenario-opening-${activeIndex}`} value={active.openingMessage} onChange={(event) => update(activeIndex, { openingMessage: event.target.value })} /></Field><Field><FieldLabel htmlFor={`scenario-goal-${activeIndex}`}>Hidden tester goal</FieldLabel><Textarea id={`scenario-goal-${activeIndex}`} value={active.hiddenGoal} onChange={(event) => update(activeIndex, { hiddenGoal: event.target.value })} /><FieldDescription>Corpus and the judge do not use this as a scripted next turn.</FieldDescription></Field></section>
            <section className="studio-eval-subsection"><h3>Tester knowledge</h3><Field><FieldLabel htmlFor={`scenario-persona-${activeIndex}`}>Persona</FieldLabel><Textarea id={`scenario-persona-${activeIndex}`} value={active.persona} onChange={(event) => update(activeIndex, { persona: event.target.value })} /></Field><StringList title="Known facts" values={active.facts} disabled={false} onChange={(facts) => update(activeIndex, { facts })} /><StringList title="May disclose" values={active.mayDisclose} disabled={false} onChange={(mayDisclose) => update(activeIndex, { mayDisclose })} /><StringList title="Withhold until asked" values={active.withholdUntilAsked} disabled={false} onChange={(withholdUntilAsked) => update(activeIndex, { withholdUntilAsked })} /></section>
            <section className="studio-eval-subsection"><h3>Bypass behavior</h3><p>Pressure or indirect tactics the tester may try without changing its goal.</p><StringList title="Bypass attempts" values={active.bypassAttempts} disabled={false} onChange={(bypassAttempts) => update(activeIndex, { bypassAttempts })} /></section>
            <section className="studio-eval-subsection"><h3>Evaluation criteria</h3><StringList title="Per-turn criteria" values={active.perTurnCriteria} disabled={false} onChange={(perTurnCriteria) => update(activeIndex, { perTurnCriteria })} /><StringList title="Final required meaning" values={active.finalRequiredCriteria} disabled={false} onChange={(finalRequiredCriteria) => update(activeIndex, { finalRequiredCriteria })} /><StringList title="Final forbidden meaning" values={active.finalForbiddenCriteria} disabled={false} onChange={(finalForbiddenCriteria) => update(activeIndex, { finalForbiddenCriteria })} /></section>
            <section className="studio-eval-subsection"><h3>Runtime checkpoints</h3><p>Product behavior and state facts only; the external runner resolves implementation identities.</p><div className="grid gap-4 sm:grid-cols-3"><Field><FieldLabel htmlFor={`scenario-start-${activeIndex}`}>Starting behavior</FieldLabel><select id={`scenario-start-${activeIndex}`} className="studio-select" value={active.expectations.startingBehavior} onChange={(event) => update(activeIndex, { expectations: { ...active.expectations, startingBehavior: event.target.value } })}>{feature.stories.map((story) => <option key={story.id} value={story.title}>{story.title}</option>)}</select></Field><Field><FieldLabel htmlFor={`scenario-final-${activeIndex}`}>Primary final behavior</FieldLabel><select id={`scenario-final-${activeIndex}`} className="studio-select" value={active.expectations.finalBehavior} onChange={(event) => update(activeIndex, { expectations: { ...active.expectations, finalBehavior: event.target.value, allowedFinalBehaviors: (active.expectations.allowedFinalBehaviors ?? []).filter((item) => item !== event.target.value) } })}>{feature.stories.map((story) => <option key={story.id} value={story.title}>{story.title}</option>)}</select></Field><Field><FieldLabel htmlFor={`scenario-auth-${activeIndex}`}>Authentication</FieldLabel><select id={`scenario-auth-${activeIndex}`} className="studio-select" value={active.expectations.authentication} onChange={(event) => update(activeIndex, { expectations: { ...active.expectations, authentication: event.target.value as DeterministicExpectations["authentication"] } })}><option value="unchanged">Unchanged</option><option value="public">Public</option><option value="authenticated">Authenticated</option></select></Field></div><EvaluationAssociation title="Also acceptable final behaviors" options={feature.stories.map((story) => story.title).filter((title) => title !== active.expectations.finalBehavior)} selected={active.expectations.allowedFinalBehaviors ?? []} disabled={false} onChange={(allowedFinalBehaviors) => update(activeIndex, { expectations: { ...active.expectations, allowedFinalBehaviors } })} /><p className="text-xs text-muted-foreground">Use alternatives only when the product intentionally permits more than one terminal route.</p><StringList title="Forbidden runtime outcomes" values={active.expectations.forbiddenOutcomes} disabled={false} onChange={(forbiddenOutcomes) => update(activeIndex, { expectations: { ...active.expectations, forbiddenOutcomes } })} /></section>
            <section className="studio-eval-subsection"><h3>Stop conditions</h3><div className="grid gap-4 sm:grid-cols-[1fr_9rem]"><Field><FieldLabel htmlFor={`scenario-success-${activeIndex}`}>Success condition</FieldLabel><Textarea id={`scenario-success-${activeIndex}`} value={active.successCondition} onChange={(event) => update(activeIndex, { successCondition: event.target.value })} /></Field><Field><FieldLabel htmlFor={`scenario-turns-${activeIndex}`}>Maximum turns</FieldLabel><Input id={`scenario-turns-${activeIndex}`} type="number" min={2} max={20} value={active.maxTurns} onChange={(event) => update(activeIndex, { maxTurns: Number(event.target.value) })} /></Field></div><StringList title="Failure conditions" values={active.failureConditions} disabled={false} onChange={(failureConditions) => update(activeIndex, { failureConditions })} /><StringList title="Stopping conditions" values={active.stoppingConditions} disabled={false} onChange={(stoppingConditions) => update(activeIndex, { stoppingConditions })} /></section>
            <ConversationRuntimeAssociations feature={feature} scenario={active} onChange={(expectations) => update(activeIndex, { expectations })} />
          </div>
          <footer className="studio-operation-drawer-footer"><Button type="button" variant="ghost" className="text-destructive" onClick={() => { onChange({ conversationEvals: feature.conversationEvals.filter((_, itemIndex) => itemIndex !== activeIndex) }); setActiveIndex(null) }}><Trash2 /> Remove scenario</Button><Button type="button" onClick={() => setActiveIndex(null)}>Done</Button></footer>
        </div>
      )}
    </div>
  )
}

function ConversationRuntimeAssociations({ feature, scenario, onChange }: { feature: DesignFeature; scenario: FeatureConversationEvalScenario; onChange: (expectations: DeterministicExpectations) => void }) {
  const operations = [...new Set(feature.stories.flatMap((story) => story.operations.map((item) => item.name)))]
  const surfaces = [...new Set(feature.stories.flatMap((story) => story.surfaces.map((item) => item.name)))]
  const actions = [...new Set(feature.stories.flatMap((story) => story.suggestedActions.map((item) => item.label)))]
  const set = <Key extends keyof DeterministicExpectations>(key: Key, value: DeterministicExpectations[Key]) => onChange({ ...scenario.expectations, [key]: value })
  return <section className="studio-eval-subsection"><h3>Runtime associations</h3><p>Feature-level product objects the runner must observe or forbid across the conversation.</p><EvaluationAssociation title="Required Operations" options={operations} selected={scenario.expectations.requiredOperations} disabled={false} onChange={(value) => set("requiredOperations", value)} /><EvaluationAssociation title="Allowed Operations" options={operations} selected={scenario.expectations.allowedOperations} disabled={false} onChange={(value) => set("allowedOperations", value)} /><EvaluationAssociation title="Forbidden Operations" options={operations} selected={scenario.expectations.forbiddenOperations} disabled={false} onChange={(value) => set("forbiddenOperations", value)} /><EvaluationAssociation title="Required Surfaces" options={surfaces} selected={scenario.expectations.requiredSurfaces} disabled={false} onChange={(value) => set("requiredSurfaces", value)} /><EvaluationAssociation title="Required SuggestedActions" options={actions} selected={scenario.expectations.requiredSuggestedActions} disabled={false} onChange={(value) => set("requiredSuggestedActions", value)} /></section>
}
