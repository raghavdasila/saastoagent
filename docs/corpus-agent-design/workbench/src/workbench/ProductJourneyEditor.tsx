import { CheckCircle2, CircleAlert, Plus, Route, Trash2, X } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { StringList } from "@/workbench/BehaviorEvalEditor"
import { EvaluationStatus } from "@/workbench/EvaluationStatus"
import { getFeatureProductJourneyReadiness, getProductJourneyIssues } from "@/workbench/evaluationReadiness"
import type { DesignFeature, ProductJourneyEval } from "@/workbench/types"

function newJourney(feature: DesignFeature): ProductJourneyEval {
  const behavior = feature.stories[0]?.title ?? ""
  return {
    id: `product-journey-${Date.now()}`,
    title: "New product journey",
    enabled: true,
    blocking: true,
    interaction: "surface",
    startingBehavior: behavior,
    startingAuthentication: "public",
    goal: "",
    preconditions: [],
    openingMessage: "",
    testerPersona: "",
    testerFacts: [],
    withholdUntilAsked: [],
    requiredOutcomes: [],
    forbiddenOutcomes: [],
    finalBehavior: behavior,
    finalAuthentication: "unchanged",
    stateAssertions: [],
    maxTurns: 0,
  }
}

export function ProductJourneyEditor({ feature, onChange }: { feature: DesignFeature; onChange: (patch: Partial<DesignFeature>) => void }) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)
  const readiness = getFeatureProductJourneyReadiness(feature)
  const active = activeIndex === null ? null : feature.productJourneyEvals[activeIndex]
  const update = (index: number, patch: Partial<ProductJourneyEval>) => onChange({ productJourneyEvals: feature.productJourneyEvals.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) })

  function add() {
    onChange({ productJourneyEvals: [...feature.productJourneyEvals, newJourney(feature)] })
    setActiveIndex(feature.productJourneyEvals.length)
  }

  return <div className="mx-auto flex max-w-5xl flex-col gap-5 p-4 sm:p-6 lg:p-8">
    <div className="flex items-start justify-between gap-4 border-b border-border pb-5">
      <div className="flex items-start gap-3"><div className="grid size-9 shrink-0 place-items-center rounded-md border border-primary/20 bg-primary/10 text-primary"><Route className="size-4" /></div><div><p className="text-xs font-medium text-muted-foreground">Corpus / {feature.name}</p><h2 id="product-journeys-heading" className="mt-0.5 text-xl font-semibold tracking-[-0.025em]">Product journeys</h2><p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">Prove that Corpus reaches observable product and owner-state outcomes. Runtime selectors, credentials, mailbox access, and database mappings remain outside Studio.</p></div></div>
      <Button type="button" variant="outline" onClick={add}><Plus /> Add journey</Button>
    </div>
    <div className="studio-eval-summary"><div><strong>{readiness.isReady ? "Definitions complete" : `${readiness.issues.length} definition issues`}</strong><span>{feature.productJourneyEvals.length} end-to-end product journeys</span></div><EvaluationStatus /></div>
    {feature.productJourneyEvals.length === 0 ? <p className="studio-empty-state">No product journeys authored for this feature.</p> : <div className="studio-eval-inventory" role="list" aria-label="Product journeys">
      <div className="studio-conversation-columns" aria-hidden="true"><span>Journey</span><span>Product goal</span><span>Shape</span><span>Status</span><span>Result</span></div>
      {feature.productJourneyEvals.map((journey, index) => { const issues = getProductJourneyIssues(feature, journey, index); return <button key={journey.id || index} id={`product-journey-${index}`} type="button" className="studio-conversation-row" onClick={() => setActiveIndex(index)}><span className="studio-eval-name">{journey.title || `Journey ${index + 1}`}<small>{journey.blocking ? "Blocking" : "Optional"}</small></span><span className="studio-eval-coverage">{journey.goal || "No product goal"}</span><span className="studio-eval-turns">{journey.interaction.replace("-", " ")}</span><span className={issues.length === 0 ? "studio-contract-ready" : "studio-contract-incomplete"}>{issues.length === 0 ? <CheckCircle2 /> : <CircleAlert />}{issues.length === 0 ? "Complete" : `${issues.length} issues`}</span><EvaluationStatus compact evaluationId={journey.id} /></button> })}
    </div>}
    {active && activeIndex !== null && <div className="studio-eval-drawer" role="dialog" aria-modal="true" aria-label={active.title || `Product journey ${activeIndex + 1}`}>
      <header className="studio-operation-drawer-header"><div className="min-w-0"><p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">Product journey</p><h2 className="truncate text-base font-semibold">{active.title || `Journey ${activeIndex + 1}`}</h2></div><Button type="button" size="icon-sm" variant="ghost" aria-label="Close product journey" onClick={() => setActiveIndex(null)}><X /></Button></header>
      <div className="studio-operation-drawer-content">
        <div className="studio-toggle-row"><label><input type="checkbox" checked={active.enabled} onChange={(event) => update(activeIndex, { enabled: event.target.checked })} /> Enabled</label><label><input type="checkbox" checked={active.blocking} onChange={(event) => update(activeIndex, { blocking: event.target.checked })} /> Blocks implementation readiness</label><EvaluationStatus compact evaluationId={active.id} /></div>
        <section className="studio-eval-subsection"><h3>Journey definition</h3><div className="grid gap-4 sm:grid-cols-2"><Field><FieldLabel htmlFor={`journey-title-${activeIndex}`}>Journey title</FieldLabel><Input id={`journey-title-${activeIndex}`} value={active.title} onChange={(event) => update(activeIndex, { title: event.target.value })} /></Field><Field><FieldLabel htmlFor={`journey-id-${activeIndex}`}>Stable ID</FieldLabel><Input id={`journey-id-${activeIndex}`} value={active.id} onChange={(event) => update(activeIndex, { id: event.target.value })} /></Field></div><Field><FieldLabel htmlFor={`journey-goal-${activeIndex}`}>Product goal</FieldLabel><Textarea id={`journey-goal-${activeIndex}`} value={active.goal} onChange={(event) => update(activeIndex, { goal: event.target.value })} /><FieldDescription>Describe the owner-visible outcome, not runner steps or technical state.</FieldDescription></Field><Field><FieldLabel htmlFor={`journey-shape-${activeIndex}`}>Interaction shape</FieldLabel><select id={`journey-shape-${activeIndex}`} className="studio-select" value={active.interaction} onChange={(event) => update(activeIndex, { interaction: event.target.value as ProductJourneyEval["interaction"], maxTurns: event.target.value === "adaptive-conversation" ? Math.max(active.maxTurns, 8) : 0 })}><option value="surface">Product surface</option><option value="single-message">Single message</option><option value="adaptive-conversation">Adaptive conversation</option></select></Field><StringList title="Preconditions" values={active.preconditions} disabled={false} onChange={(preconditions) => update(activeIndex, { preconditions })} /></section>
        {active.interaction !== "surface" && <section className="studio-eval-subsection"><h3>Tester</h3><Field><FieldLabel htmlFor={`journey-opening-${activeIndex}`}>Opening message</FieldLabel><Textarea id={`journey-opening-${activeIndex}`} value={active.openingMessage} onChange={(event) => update(activeIndex, { openingMessage: event.target.value })} /></Field>{active.interaction === "adaptive-conversation" && <><Field><FieldLabel htmlFor={`journey-persona-${activeIndex}`}>Tester persona</FieldLabel><Textarea id={`journey-persona-${activeIndex}`} value={active.testerPersona} onChange={(event) => update(activeIndex, { testerPersona: event.target.value })} /></Field><StringList title="Tester facts" values={active.testerFacts} disabled={false} onChange={(testerFacts) => update(activeIndex, { testerFacts })} /><StringList title="Withhold until asked" values={active.withholdUntilAsked} disabled={false} onChange={(withholdUntilAsked) => update(activeIndex, { withholdUntilAsked })} /><Field><FieldLabel htmlFor={`journey-turns-${activeIndex}`}>Maximum turns</FieldLabel><Input id={`journey-turns-${activeIndex}`} type="number" min={2} max={20} value={active.maxTurns} onChange={(event) => update(activeIndex, { maxTurns: Number(event.target.value) })} /></Field></>}</section>}
        <section className="studio-eval-subsection"><h3>Starting and final state</h3><div className="grid gap-4 sm:grid-cols-2"><BehaviorField id={`journey-start-${activeIndex}`} label="Starting behavior" feature={feature} value={active.startingBehavior} onChange={(startingBehavior) => update(activeIndex, { startingBehavior })} /><Field><FieldLabel htmlFor={`journey-start-auth-${activeIndex}`}>Starting authentication</FieldLabel><select id={`journey-start-auth-${activeIndex}`} className="studio-select" value={active.startingAuthentication} onChange={(event) => update(activeIndex, { startingAuthentication: event.target.value as ProductJourneyEval["startingAuthentication"] })}><option value="public">Public</option><option value="authenticated">Authenticated</option></select></Field><BehaviorField id={`journey-final-${activeIndex}`} label="Final behavior" feature={feature} value={active.finalBehavior} onChange={(finalBehavior) => update(activeIndex, { finalBehavior })} /><Field><FieldLabel htmlFor={`journey-final-auth-${activeIndex}`}>Final authentication</FieldLabel><select id={`journey-final-auth-${activeIndex}`} className="studio-select" value={active.finalAuthentication} onChange={(event) => update(activeIndex, { finalAuthentication: event.target.value as ProductJourneyEval["finalAuthentication"] })}><option value="unchanged">Unchanged</option><option value="public">Public</option><option value="authenticated">Authenticated</option></select></Field></div></section>
        <section className="studio-eval-subsection"><h3>Product proof</h3><StringList title="Required outcomes" values={active.requiredOutcomes} disabled={false} onChange={(requiredOutcomes) => update(activeIndex, { requiredOutcomes })} /><StringList title="Forbidden outcomes" values={active.forbiddenOutcomes} disabled={false} onChange={(forbiddenOutcomes) => update(activeIndex, { forbiddenOutcomes })} /><StringList title="Product-state assertions" values={active.stateAssertions} disabled={false} onChange={(stateAssertions) => update(activeIndex, { stateAssertions })} /></section>
      </div>
      <footer className="studio-operation-drawer-footer"><Button type="button" variant="ghost" className="text-destructive" onClick={() => { onChange({ productJourneyEvals: feature.productJourneyEvals.filter((_, itemIndex) => itemIndex !== activeIndex) }); setActiveIndex(null) }}><Trash2 /> Remove journey</Button><Button type="button" onClick={() => setActiveIndex(null)}>Done</Button></footer>
    </div>}
  </div>
}

function BehaviorField({ id, label, feature, value, onChange }: { id: string; label: string; feature: DesignFeature; value: string; onChange: (value: string) => void }) {
  return <Field><FieldLabel htmlFor={id}>{label}</FieldLabel><select id={id} className="studio-select" value={value} onChange={(event) => onChange(event.target.value)}>{feature.stories.map((story) => <option key={story.id} value={story.title}>{story.title}</option>)}</select></Field>
}
