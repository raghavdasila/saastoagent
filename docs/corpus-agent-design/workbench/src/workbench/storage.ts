import { createSeedState } from "@/workbench/seed"
import { STUDIO_CONFIG } from "@/workbench/studioConfig"
import type { WorkbenchState } from "@/workbench/types"

const DESIGN_STATE_ENDPOINT = "/__design-studio/state"
let saveQueue: Promise<void> = Promise.resolve()

export type LoadResult =
  | { ok: true; state: WorkbenchState; source: "saved" | "seed" }
  | { ok: false; reason: "invalid" | "unavailable" }

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function hasValidPolicies(value: unknown): boolean {
  return Array.isArray(value) && value.every((policy) => typeof policy === "string")
}

function hasValidCapabilities(value: unknown): boolean {
  return Array.isArray(value) && value.every((capability) => (
    isRecord(capability)
    && typeof capability.name === "string"
    && typeof capability.purpose === "string"
    && Array.isArray(capability.operationNames)
    && capability.operationNames.every((name) => typeof name === "string")
    && Array.isArray(capability.surfaceNames)
    && capability.surfaceNames.every((name) => typeof name === "string")
    && hasValidPolicies(capability.policies)
  ))
}

function hasValidSurfaces(value: unknown): boolean {
  return Array.isArray(value) && value.every((surface) => (
    isRecord(surface)
    && typeof surface.name === "string"
    && typeof surface.purpose === "string"
    && hasValidPolicies(surface.policies)
  ))
}

function hasValidOperations(value: unknown): boolean {
  return Array.isArray(value) && value.every((operation) => (
    isRecord(operation)
    && typeof operation.name === "string"
    && typeof operation.purpose === "string"
    && typeof operation.inputs === "string"
    && typeof operation.outcomes === "string"
    && typeof operation.safetyAndReview === "string"
    && typeof operation.recovery === "string"
    && hasValidPolicies(operation.policies)
  ))
}

function hasValidSuggestedActions(value: unknown): boolean {
  return Array.isArray(value) && value.every((action) => (
    isRecord(action)
    && typeof action.id === "string"
    && typeof action.label === "string"
    && typeof action.operationName === "string"
    && typeof action.visibility === "string"
  ))
}

const COVERAGE_TAGS = new Set(["normal", "boundary", "failure", "privacy", "adversarial"])

function hasValidExpectations(value: unknown): boolean {
  return isRecord(value)
    && typeof value.startingBehavior === "string"
    && typeof value.finalBehavior === "string"
    && (value.allowedFinalBehaviors === undefined || (Array.isArray(value.allowedFinalBehaviors) && value.allowedFinalBehaviors.every((item) => typeof item === "string")))
    && (value.authentication === "public" || value.authentication === "authenticated" || value.authentication === "unchanged")
    && ["requiredOperations", "allowedOperations", "forbiddenOperations", "requiredSurfaces", "requiredSuggestedActions", "forbiddenOutcomes"].every((field) => Array.isArray(value[field]) && value[field].every((item) => typeof item === "string"))
}

function hasValidBehaviorEvals(value: unknown): boolean {
  return Array.isArray(value) && value.every((evalCase) => (
    isRecord(evalCase)
    && typeof evalCase.id === "string"
    && typeof evalCase.title === "string"
    && typeof evalCase.enabled === "boolean"
    && typeof evalCase.blocking === "boolean"
    && Array.isArray(evalCase.coverage)
    && evalCase.coverage.every((tag) => typeof tag === "string" && COVERAGE_TAGS.has(tag))
    && typeof evalCase.input === "string"
    && typeof evalCase.referenceResponse === "string"
    && hasValidPolicies(evalCase.requiredCriteria)
    && hasValidPolicies(evalCase.forbiddenCriteria)
    && hasValidExpectations(evalCase.expectations)
  ))
}

function hasValidEvalExemptions(value: unknown): boolean {
  return Array.isArray(value) && value.every((item) => isRecord(item) && typeof item.coverage === "string" && COVERAGE_TAGS.has(item.coverage) && typeof item.reason === "string")
}

function hasValidConversationEvals(value: unknown): boolean {
  return Array.isArray(value) && value.every((scenario) => (
    isRecord(scenario)
    && typeof scenario.id === "string"
    && typeof scenario.title === "string"
    && typeof scenario.enabled === "boolean"
    && typeof scenario.blocking === "boolean"
    && typeof scenario.openingMessage === "string"
    && typeof scenario.hiddenGoal === "string"
    && typeof scenario.persona === "string"
    && hasValidPolicies(scenario.facts)
    && hasValidPolicies(scenario.mayDisclose)
    && hasValidPolicies(scenario.withholdUntilAsked)
    && hasValidPolicies(scenario.bypassAttempts)
    && hasValidPolicies(scenario.perTurnCriteria)
    && hasValidPolicies(scenario.finalRequiredCriteria)
    && hasValidPolicies(scenario.finalForbiddenCriteria)
    && hasValidExpectations(scenario.expectations)
    && typeof scenario.successCondition === "string"
    && hasValidPolicies(scenario.failureConditions)
    && hasValidPolicies(scenario.stoppingConditions)
    && typeof scenario.maxTurns === "number"
  ))
}

function hasValidFeatureData(value: unknown): boolean {
  if (!Array.isArray(value) || value.length === 0) return false
  return value.every((feature) => (
    isRecord(feature)
    && typeof feature.id === "string"
    && typeof feature.name === "string"
    && typeof feature.prompt === "string"
    && hasValidPolicies(feature.policies)
    && hasValidConversationEvals(feature.conversationEvals)
    && Array.isArray(feature.stories)
    && feature.stories.length > 0
    && feature.stories.every((story) => (
      isRecord(story)
      && typeof story.id === "string"
      && typeof story.title === "string"
      && typeof story.userIntent === "string"
      && typeof story.agentIntent === "string"
      && typeof story.expectedBehavior === "string"
      && Array.isArray(story.messages)
      && story.messages.every((message) => (
        isRecord(message)
        && typeof message.id === "string"
        && (message.actor === "Corpus" || message.actor === "Owner")
        && typeof message.content === "string"
      ))
      && (story.mockSurfacePath === null || typeof story.mockSurfacePath === "string")
      && hasValidPolicies(story.nodePolicies)
      && hasValidCapabilities(story.capabilities)
      && hasValidSurfaces(story.surfaces)
      && hasValidOperations(story.operations)
      && hasValidSuggestedActions(story.suggestedActions)
      && hasValidBehaviorEvals(story.behaviorEvals)
      && hasValidEvalExemptions(story.evalExemptions)
      && (story.status === "draft" || story.status === "approved" || story.status === "rejected")
      && typeof story.rejectionReason === "string"
    ))
  ))
}

function isWorkbenchState(value: unknown): value is WorkbenchState {
  return isRecord(value)
    && hasValidFeatureData(value.features)
}

export async function loadWorkbenchState(): Promise<LoadResult> {
  try {
    const response = await fetch(DESIGN_STATE_ENDPOINT, { headers: { Accept: "application/json" } })
    if (response.status === 404) {
      const state = createSeedState()
      await saveWorkbenchState(state)
      return { ok: true, state, source: "seed" }
    }
    if (!response.ok) return { ok: false, reason: "unavailable" }

    const parsed: unknown = await response.json()
    if (!isWorkbenchState(parsed)) return { ok: false, reason: "invalid" }
    return { ok: true, state: parsed, source: "saved" }
  } catch {
    return { ok: false, reason: "unavailable" }
  }
}

export function saveWorkbenchState(state: WorkbenchState): Promise<void> {
  const request = saveQueue.then(async () => {
    const response = await fetch(DESIGN_STATE_ENDPOINT, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    })
    if (!response.ok) throw new Error(`Design-state save failed with HTTP ${response.status}`)
  })
  saveQueue = request.catch(() => undefined)
  return request
}

export async function resetWorkbenchState(): Promise<WorkbenchState> {
  const state = createSeedState()
  await saveWorkbenchState(state)
  return state
}

export function exportWorkbenchState(state: WorkbenchState): void {
  const blob = new Blob([`${JSON.stringify(state, null, 2)}\n`], { type: "application/json" })
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = objectUrl
  anchor.download = STUDIO_CONFIG.exportFilename
  anchor.hidden = true
  document.body.append(anchor)
  anchor.click()
  anchor.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0)
}
