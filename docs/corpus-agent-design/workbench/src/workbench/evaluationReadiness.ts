import type {
  BehaviorEvalCase,
  DesignFeature,
  DesignStory,
  EvalCoverageTag,
  EvaluationActionPlan,
  FeatureConversationEvalScenario,
  ProductJourneyEval,
} from "@/workbench/types"

export const EVAL_COVERAGE: Array<{ id: EvalCoverageTag; label: string }> = [
  { id: "normal", label: "Normal" },
  { id: "state", label: "State" },
  { id: "boundary", label: "Boundary" },
  { id: "failure", label: "Failure" },
  { id: "privacy", label: "Privacy" },
  { id: "adversarial", label: "Adversarial" },
]

const REQUIRED_RISK_COVERAGE = EVAL_COVERAGE.filter((category) => category.id !== "state")

export interface EvaluationIssue {
  id: string
  message: string
  targetId: string
}

export interface EvaluationReadiness {
  issues: EvaluationIssue[]
  isReady: boolean
}

function blank(value: string): boolean {
  return value.trim().length === 0
}

function duplicateIds(values: string[]): Set<string> {
  const counts = new Map<string, number>()
  for (const value of values.map((item) => item.trim()).filter(Boolean)) {
    counts.set(value, (counts.get(value) ?? 0) + 1)
  }
  return new Set([...counts].filter(([, count]) => count > 1).map(([id]) => id))
}

function expectationIssues(
  story: DesignStory,
  evalCase: Pick<BehaviorEvalCase, "expectations">,
  prefix: string,
  targetId: string,
): EvaluationIssue[] {
  const issues: EvaluationIssue[] = []
  const operations = new Set(story.operations.map((item) => item.name))
  const surfaces = new Set(story.surfaces.map((item) => item.name))
  const actions = new Set(story.suggestedActions.map((item) => item.label))
  const check = (values: string[], available: Set<string>, kind: string) => {
    values.forEach((value, index) => {
      if (blank(value) || !available.has(value)) issues.push({ id: `${prefix}-${kind}-${index}`, message: `${kind} expectation references missing design item “${value || "empty"}”.`, targetId })
    })
  }
  if (blank(evalCase.expectations.startingBehavior)) issues.push({ id: `${prefix}-starting-behavior`, message: "Add the expected starting behavior.", targetId })
  if (blank(evalCase.expectations.finalBehavior)) issues.push({ id: `${prefix}-final-behavior`, message: "Add the expected final behavior.", targetId })
  check(evalCase.expectations.requiredOperations, operations, "Required Operation")
  check(evalCase.expectations.allowedOperations, operations, "Allowed Operation")
  check(evalCase.expectations.forbiddenOperations, operations, "Forbidden Operation")
  check(evalCase.expectations.requiredSurfaces, surfaces, "Required Surface")
  check(evalCase.expectations.requiredSuggestedActions, actions, "Required SuggestedAction")
  return issues
}

export function getBehaviorEvalCaseIssues(story: DesignStory, evalCase: BehaviorEvalCase, index = 0): EvaluationIssue[] {
  const prefix = `behavior-eval-${index}`
  const targetId = `behavior-eval-${index}`
  const issues: EvaluationIssue[] = []
  if (blank(evalCase.id)) issues.push({ id: `${prefix}-id`, message: `Eval case ${index + 1} needs a stable ID.`, targetId })
  if (blank(evalCase.title)) issues.push({ id: `${prefix}-title`, message: `Eval case ${index + 1} needs a title.`, targetId })
  if (evalCase.coverage.length === 0) issues.push({ id: `${prefix}-coverage`, message: `${evalCase.title || `Eval case ${index + 1}`} needs at least one coverage category.`, targetId })
  if (blank(evalCase.input)) issues.push({ id: `${prefix}-input`, message: `${evalCase.title || `Eval case ${index + 1}`} needs a user input.`, targetId })
  if (evalCase.requiredCriteria.every(blank) && evalCase.forbiddenCriteria.every(blank)) issues.push({ id: `${prefix}-criteria`, message: `${evalCase.title || `Eval case ${index + 1}`} needs required or forbidden semantic criteria.`, targetId })
  evalCase.requiredCriteria.forEach((item, criterionIndex) => { if (blank(item)) issues.push({ id: `${prefix}-required-${criterionIndex}`, message: `${evalCase.title || `Eval case ${index + 1}`} contains an empty required criterion.`, targetId }) })
  evalCase.forbiddenCriteria.forEach((item, criterionIndex) => { if (blank(item)) issues.push({ id: `${prefix}-forbidden-${criterionIndex}`, message: `${evalCase.title || `Eval case ${index + 1}`} contains an empty forbidden criterion.`, targetId }) })
  issues.push(...expectationIssues(story, evalCase, prefix, targetId))
  issues.push(...actionPlanIssues(evalCase.actionPlan, {
    prefix,
    targetId,
    actions: new Set(story.suggestedActions.map((item) => `${story.title}\u0000${item.label}`)),
    surfaces: new Set(story.surfaces.map((item) => item.name)),
    allowAdaptiveMessages: false,
  }))
  return issues
}

export function getBehaviorEvalReadiness(story: DesignStory): EvaluationReadiness {
  const issues = story.behaviorEvals.flatMap((evalCase, index) => getBehaviorEvalCaseIssues(story, evalCase, index))
  const duplicates = duplicateIds(story.behaviorEvals.map((item) => item.id))
  story.behaviorEvals.forEach((evalCase, index) => {
    if (duplicates.has(evalCase.id.trim())) issues.push({ id: `behavior-eval-${index}-duplicate-id`, message: `Eval ID “${evalCase.id}” is duplicated.`, targetId: `behavior-eval-${index}` })
  })
  const covered = new Set(story.behaviorEvals.filter((item) => item.enabled).flatMap((item) => item.coverage))
  const exemptions = new Map(story.evalExemptions.map((item) => [item.coverage, item.reason]))
  for (const category of REQUIRED_RISK_COVERAGE) {
    if (covered.has(category.id)) continue
    const reason = exemptions.get(category.id)
    if (!reason || blank(reason)) issues.push({ id: `behavior-eval-coverage-${category.id}`, message: `Cover ${category.label.toLowerCase()} behavior or record why it is not applicable.`, targetId: "behavior-evals-heading" })
  }
  if (!story.behaviorEvals.some((item) => item.enabled && item.coverage.includes("normal"))) issues.push({ id: "behavior-eval-normal-required", message: "Add at least one enabled normal-behavior eval.", targetId: "behavior-evals-heading" })
  return { issues, isReady: issues.length === 0 }
}

export function getConversationScenarioIssues(feature: DesignFeature, scenario: FeatureConversationEvalScenario, index = 0): EvaluationIssue[] {
  const prefix = `conversation-eval-${index}`
  const targetId = `conversation-eval-${index}`
  const issues: EvaluationIssue[] = []
  const requireText = (value: string, field: string, label: string) => { if (blank(value)) issues.push({ id: `${prefix}-${field}`, message: `${scenario.title || `Scenario ${index + 1}`} needs ${label}.`, targetId }) }
  requireText(scenario.id, "id", "a stable ID")
  requireText(scenario.title, "title", "a title")
  requireText(scenario.openingMessage, "opening", "an opening message")
  requireText(scenario.hiddenGoal, "goal", "a hidden tester goal")
  requireText(scenario.persona, "persona", "a tester persona")
  requireText(scenario.successCondition, "success", "a success condition")
  if (scenario.finalRequiredCriteria.every(blank) && scenario.finalForbiddenCriteria.every(blank)) issues.push({ id: `${prefix}-criteria`, message: `${scenario.title || `Scenario ${index + 1}`} needs final required or forbidden criteria.`, targetId })
  if (scenario.stoppingConditions.length === 0 || scenario.stoppingConditions.every(blank)) issues.push({ id: `${prefix}-stopping`, message: `${scenario.title || `Scenario ${index + 1}`} needs a stopping condition.`, targetId })
  if (!Number.isInteger(scenario.maxTurns) || scenario.maxTurns < 2 || scenario.maxTurns > 20) issues.push({ id: `${prefix}-max-turns`, message: `${scenario.title || `Scenario ${index + 1}`} must allow 2 to 20 turns.`, targetId })
  const behaviorNames = new Set(feature.stories.map((story) => story.title))
  const referencedBehaviors = [scenario.expectations.startingBehavior, scenario.expectations.finalBehavior, ...(scenario.expectations.allowedFinalBehaviors ?? [])]
  referencedBehaviors.forEach((behavior, behaviorIndex) => {
    if (!behaviorNames.has(behavior)) issues.push({ id: `${prefix}-behavior-${behaviorIndex}`, message: `Runtime expectation references missing behavior â€œ${behavior}â€.`, targetId })
  })
  const representativeStory = feature.stories[0]
  if (representativeStory) {
    issues.push(...expectationIssues({
      ...representativeStory,
      operations: feature.stories.flatMap((story) => story.operations),
      surfaces: feature.stories.flatMap((story) => story.surfaces),
      suggestedActions: feature.stories.flatMap((story) => story.suggestedActions),
    }, scenario, prefix, targetId))
  }
  issues.push(...actionPlanIssues(scenario.actionPlan, {
    prefix,
    targetId,
    actions: new Set(feature.stories.flatMap((story) => story.suggestedActions.map((item) => `${story.title}\u0000${item.label}`))),
    surfaces: new Set(feature.stories.flatMap((story) => story.surfaces.map((item) => item.name))),
    allowAdaptiveMessages: true,
  }))
  return issues
}

export function getFeatureConversationEvalReadiness(feature: DesignFeature): EvaluationReadiness {
  const issues = feature.conversationEvals.flatMap((scenario, index) => getConversationScenarioIssues(feature, scenario, index))
  const duplicates = duplicateIds(feature.conversationEvals.map((item) => item.id))
  feature.conversationEvals.forEach((scenario, index) => {
    if (duplicates.has(scenario.id.trim())) issues.push({ id: `conversation-eval-${index}-duplicate-id`, message: `Conversation eval ID “${scenario.id}” is duplicated.`, targetId: `conversation-eval-${index}` })
  })
  if (!feature.conversationEvals.some((item) => item.enabled)) issues.push({ id: "conversation-eval-required", message: "Add at least one enabled feature conversation eval.", targetId: "conversation-evals-heading" })
  return { issues, isReady: issues.length === 0 }
}

export function getProductJourneyIssues(feature: DesignFeature, journey: ProductJourneyEval, index = 0): EvaluationIssue[] {
  const prefix = `product-journey-${index}`
  const targetId = prefix
  const issues: EvaluationIssue[] = []
  const requireText = (value: string, field: string, label: string) => { if (blank(value)) issues.push({ id: `${prefix}-${field}`, message: `${journey.title || `Journey ${index + 1}`} needs ${label}.`, targetId }) }
  requireText(journey.id, "id", "a stable ID")
  requireText(journey.title, "title", "a title")
  requireText(journey.goal, "goal", "a product goal")
  requireText(journey.startingBehavior, "starting", "a starting behavior")
  requireText(journey.finalBehavior, "final", "a final behavior")
  if (journey.requiredOutcomes.length === 0 || journey.requiredOutcomes.every(blank)) issues.push({ id: `${prefix}-outcomes`, message: `${journey.title || `Journey ${index + 1}`} needs a required product outcome.`, targetId })
  if (journey.stateAssertions.length === 0 || journey.stateAssertions.every(blank)) issues.push({ id: `${prefix}-state`, message: `${journey.title || `Journey ${index + 1}`} needs a product-state assertion.`, targetId })
  if (journey.interaction !== "surface") requireText(journey.openingMessage, "opening", "an opening message")
  if (journey.interaction === "adaptive-conversation") {
    requireText(journey.testerPersona, "persona", "a tester persona")
    if (!Number.isInteger(journey.maxTurns) || journey.maxTurns < 2 || journey.maxTurns > 20) issues.push({ id: `${prefix}-turns`, message: `${journey.title || `Journey ${index + 1}`} must allow 2 to 20 turns.`, targetId })
  }
  const behaviorNames = new Set(feature.stories.map((story) => story.title))
  if (!behaviorNames.has(journey.startingBehavior)) issues.push({ id: `${prefix}-starting-missing`, message: `Starting behavior references a missing design item.`, targetId })
  return issues
}

function actionPlanIssues(
  plan: EvaluationActionPlan,
  options: {
    prefix: string
    targetId: string
    actions: Set<string>
    surfaces: Set<string>
    allowAdaptiveMessages: boolean
  },
): EvaluationIssue[] {
  const { prefix, targetId, actions, surfaces, allowAdaptiveMessages } = options
  const issues: EvaluationIssue[] = []
  if (plan.preconditions.length === 0) issues.push({ id: `${prefix}-preconditions`, message: "Add at least one product-state precondition.", targetId })
  plan.preconditions.forEach((value, index) => {
    if (blank(value)) issues.push({ id: `${prefix}-precondition-${index}`, message: "Action plan contains an empty precondition.", targetId })
  })
  if (plan.steps.length < 2) issues.push({ id: `${prefix}-steps`, message: "Action plan needs an authored message and a checkpoint.", targetId })
  if (plan.steps[0]?.kind !== "message" || plan.steps[0]?.source !== "authored-input") issues.push({ id: `${prefix}-first-step`, message: "Action plan must start with the authored evaluation input.", targetId })
  if (plan.steps.at(-1)?.kind !== "checkpoint") issues.push({ id: `${prefix}-last-step`, message: "Action plan must end with a deterministic checkpoint.", targetId })
  const duplicateStepIds = duplicateIds(plan.steps.map((step) => step.id))
  plan.steps.forEach((step, index) => {
    if (blank(step.id)) issues.push({ id: `${prefix}-step-${index}-id`, message: `Action step ${index + 1} needs a stable ID.`, targetId })
    if (duplicateStepIds.has(step.id.trim())) issues.push({ id: `${prefix}-step-${index}-duplicate`, message: `Action step ID “${step.id}” is duplicated.`, targetId })
    if (step.kind === "message" && step.source === "adaptive-tester" && !allowAdaptiveMessages) issues.push({ id: `${prefix}-step-${index}-adaptive`, message: "Behavior evals cannot delegate dialogue to the adaptive tester.", targetId })
    if (step.kind === "suggested-action" && (blank(step.behavior) || blank(step.action) || !actions.has(`${step.behavior}\u0000${step.action}`))) issues.push({ id: `${prefix}-step-${index}-action`, message: `Action step references missing SuggestedAction “${step.behavior || "empty"} / ${step.action || "empty"}”.`, targetId })
    if (step.kind === "surface-submit") {
      if (blank(step.surface) || !surfaces.has(step.surface)) issues.push({ id: `${prefix}-step-${index}-surface`, message: `Surface submission references missing Surface “${step.surface || "empty"}”.`, targetId })
      if (blank(step.inputIntent)) issues.push({ id: `${prefix}-step-${index}-intent`, message: "Surface submission needs a product-semantic input intent.", targetId })
    }
    if (step.kind === "checkpoint") {
      if (blank(step.label)) issues.push({ id: `${prefix}-step-${index}-label`, message: "Checkpoint needs a label.", targetId })
      if (step.stateAssertions.length === 0 || step.stateAssertions.every(blank)) issues.push({ id: `${prefix}-step-${index}-state`, message: "Checkpoint needs at least one product-state assertion.", targetId })
      step.stateAssertions.forEach((value, assertionIndex) => {
        if (blank(value)) issues.push({ id: `${prefix}-step-${index}-state-${assertionIndex}`, message: "Checkpoint contains an empty product-state assertion.", targetId })
      })
    }
  })
  return issues
}

export function getFeatureProductJourneyReadiness(feature: DesignFeature): EvaluationReadiness {
  const issues = feature.productJourneyEvals.flatMap((journey, index) => getProductJourneyIssues(feature, journey, index))
  const duplicates = duplicateIds(feature.productJourneyEvals.map((item) => item.id))
  feature.productJourneyEvals.forEach((journey, index) => {
    if (duplicates.has(journey.id.trim())) issues.push({ id: `product-journey-${index}-duplicate-id`, message: `Product journey ID “${journey.id}” is duplicated.`, targetId: `product-journey-${index}` })
  })
  return { issues, isReady: issues.length === 0 }
}
