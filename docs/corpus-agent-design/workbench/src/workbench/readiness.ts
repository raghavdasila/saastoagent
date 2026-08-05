import type { DesignStory } from "@/workbench/types"

export type ReadinessSection = "behavior" | "capabilities" | "surfaces" | "operations" | "suggested-actions" | "rules" | "preview"
export type ReadinessSeverity = "blocking" | "warning"

export interface ReadinessIssue {
  id: string
  severity: ReadinessSeverity
  section: ReadinessSection
  message: string
  targetId?: string
}
export interface StoryReadiness {
  issues: ReadinessIssue[]
  blockers: ReadinessIssue[]
  warnings: ReadinessIssue[]
  isReady: boolean
}

function missing(value: string): boolean {
  return value.trim().length === 0
}

function duplicateNames(values: string[]): Set<string> {
  const counts = new Map<string, number>()
  for (const value of values.map((item) => item.trim()).filter(Boolean)) {
    const key = value.toLocaleLowerCase()
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return new Set([...counts].filter(([, count]) => count > 1).map(([name]) => name))
}

export function getStoryReadiness(story: DesignStory): StoryReadiness {
  const issues: ReadinessIssue[] = []
  const block = (id: string, section: ReadinessSection, message: string, targetId?: string) => {
    issues.push({ id, severity: "blocking", section, message, targetId })
  }
  const warn = (id: string, section: ReadinessSection, message: string, targetId?: string) => {
    issues.push({ id, severity: "warning", section, message, targetId })
  }

  if (missing(story.title)) block("behavior-title", "behavior", "Add a behavior title.", "story-title")
  if (missing(story.userIntent)) block("behavior-user-intent", "behavior", "Describe the user intent.", "user-intent")
  if (missing(story.agentIntent)) block("behavior-agent-intent", "behavior", "Describe the outcome Corpus is responsible for.", "agent-intent")
  if (missing(story.expectedBehavior)) block("behavior-expected", "behavior", "Describe the observable behavior and completion state.", "expected-behavior")

  const capabilityNames = story.capabilities.map((item) => item.name)
  const surfaceNames = story.surfaces.map((item) => item.name)
  const operationNames = story.operations.map((item) => item.name)
  const duplicateCapabilities = duplicateNames(capabilityNames)
  const duplicateSurfaces = duplicateNames(surfaceNames)
  const duplicateOperations = duplicateNames(operationNames)
  const availableSurfaces = new Set(surfaceNames.map((name) => name.trim()))
  const availableOperations = new Set(operationNames.map((name) => name.trim()))

  story.capabilities.forEach((capability, index) => {
    const targetId = `capability-${index}`
    if (missing(capability.name)) block(`capability-${index}-name`, "capabilities", `Capability ${index + 1} needs a name.`, targetId)
    if (missing(capability.purpose)) block(`capability-${index}-purpose`, "capabilities", `${capability.name || `Capability ${index + 1}`} needs a purpose.`, targetId)
    if (duplicateCapabilities.has(capability.name.trim().toLocaleLowerCase())) block(`capability-${index}-duplicate`, "capabilities", `Capability name “${capability.name.trim()}” is duplicated.`, targetId)
    for (const operationName of capability.operationNames) {
      if (!availableOperations.has(operationName.trim())) block(`capability-${index}-operation-${operationName}`, "capabilities", `${capability.name || `Capability ${index + 1}`} references missing Operation “${operationName}”.`, targetId)
    }
    for (const surfaceName of capability.surfaceNames) {
      if (!availableSurfaces.has(surfaceName.trim())) block(`capability-${index}-surface-${surfaceName}`, "capabilities", `${capability.name || `Capability ${index + 1}`} references missing Surface “${surfaceName}”.`, targetId)
    }
    capability.policies.forEach((policy, policyIndex) => {
      if (missing(policy)) block(`capability-${index}-policy-${policyIndex}`, "rules", `${capability.name || `Capability ${index + 1}`} contains an empty rule.`, targetId)
    })
  })

  story.surfaces.forEach((surface, index) => {
    const targetId = `surface-${index}`
    if (missing(surface.name)) block(`surface-${index}-name`, "surfaces", `Surface ${index + 1} needs a name.`, targetId)
    if (missing(surface.purpose)) block(`surface-${index}-purpose`, "surfaces", `${surface.name || `Surface ${index + 1}`} needs a purpose.`, targetId)
    if (duplicateSurfaces.has(surface.name.trim().toLocaleLowerCase())) block(`surface-${index}-duplicate`, "surfaces", `Surface name “${surface.name.trim()}” is duplicated.`, targetId)
    surface.policies.forEach((policy, policyIndex) => {
      if (missing(policy)) block(`surface-${index}-policy-${policyIndex}`, "rules", `${surface.name || `Surface ${index + 1}`} contains an empty rule.`, targetId)
    })
  })

  story.operations.forEach((operation, index) => {
    const label = operation.name.trim() || `Operation ${index + 1}`
    const targetId = `operation-${index}`
    if (missing(operation.name)) block(`operation-${index}-name`, "operations", `Operation ${index + 1} needs a name.`, targetId)
    if (duplicateOperations.has(operation.name.trim().toLocaleLowerCase())) block(`operation-${index}-duplicate`, "operations", `Operation name “${operation.name.trim()}” is duplicated.`, targetId)
    if (missing(operation.purpose)) block(`operation-${index}-purpose`, "operations", `${label} needs an intended effect.`, targetId)
    if (missing(operation.inputs)) block(`operation-${index}-inputs`, "operations", `${label} needs inputs or an explicit “No input required” statement.`, targetId)
    if (missing(operation.outcomes)) block(`operation-${index}-outcomes`, "operations", `${label} needs observable success and failure outcomes.`, targetId)
    if (missing(operation.safetyAndReview)) block(`operation-${index}-safety`, "operations", `${label} needs safety and review guidance or an explicit rationale that none is required.`, targetId)
    if (missing(operation.recovery)) block(`operation-${index}-recovery`, "operations", `${label} needs failure recovery or an explicit fail-visible statement.`, targetId)
    operation.policies.forEach((policy, policyIndex) => {
      if (missing(policy)) block(`operation-${index}-policy-${policyIndex}`, "rules", `${label} contains an empty rule.`, targetId)
    })
  })

  story.suggestedActions.forEach((action, index) => {
    const targetId = `suggested-action-${index}`
    if (missing(action.label)) block(`suggested-action-${index}-label`, "suggested-actions", `Suggested action ${index + 1} needs a user-facing label.`, targetId)
    if (missing(action.operationName) || !availableOperations.has(action.operationName.trim())) block(`suggested-action-${index}-operation`, "suggested-actions", `${action.label || `Suggested action ${index + 1}`} must reference a defined Operation.`, targetId)
  })

  story.nodePolicies.forEach((policy, index) => {
    if (missing(policy)) block(`node-policy-${index}`, "rules", "The behavior contains an empty rule.", "node-rules")
  })
  story.messages.forEach((message, index) => {
    if (missing(message.content)) block(`message-${index}`, "preview", `Chat message ${index + 1} is empty.`, "interaction-preview")
  })
  if (story.messages.length === 0 && story.mockSurfacePath === null) {
    warn("preview-missing", "preview", "No interaction preview is defined. This is valid when a preview would not improve review.", "interaction-preview")
  }

  const blockers = issues.filter((issue) => issue.severity === "blocking")
  const warnings = issues.filter((issue) => issue.severity === "warning")
  return { issues, blockers, warnings, isReady: blockers.length === 0 }
}
