import type {
  BehaviorEvalCase,
  DesignFeature,
  DesignStory,
  EvalCoverageTag,
  FeatureConversationEvalScenario,
} from "@/workbench/types"

export const EVAL_COVERAGE: Array<{ id: EvalCoverageTag; label: string }> = [
  { id: "normal", label: "Normal" },
  { id: "boundary", label: "Boundary" },
  { id: "failure", label: "Failure" },
  { id: "privacy", label: "Privacy" },
  { id: "adversarial", label: "Adversarial" },
]

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
  for (const category of EVAL_COVERAGE) {
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
  const representativeStory = feature.stories.find((story) => story.title === scenario.expectations.startingBehavior) ?? feature.stories[0]
  if (representativeStory) issues.push(...expectationIssues(representativeStory, scenario, prefix, targetId))
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
