import { createSeedState } from "@/workbench/seed"
import type { AgentPolicyScope, WorkbenchState } from "@/workbench/types"

const DESIGN_STATE_ENDPOINT = "/__design-studio/state"
let saveQueue: Promise<void> = Promise.resolve()

export type LoadResult =
  | { ok: true; state: WorkbenchState; source: "saved" | "seed" }
  | { ok: false; reason: "invalid" | "unavailable" }

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

const POLICY_SCOPES = new Set<AgentPolicyScope>([
  "feature",
  "behavior",
  "node",
  "capability",
  "surface",
  "action",
  "operation",
  "other",
])

function hasValidPolicies(value: unknown): boolean {
  return Array.isArray(value) && value.every((policy) => (
    isRecord(policy)
    && typeof policy.scope === "string"
    && POLICY_SCOPES.has(policy.scope as AgentPolicyScope)
    && typeof policy.scopeName === "string"
    && typeof policy.guidance === "string"
  ))
}

function hasValidFeatureData(value: unknown): boolean {
  if (!Array.isArray(value) || value.length === 0) return false
  return value.every((feature) => (
    isRecord(feature)
    && typeof feature.id === "string"
    && typeof feature.name === "string"
    && hasValidPolicies(feature.policies)
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
      && Array.isArray(story.actions)
      && story.actions.every((action) => isRecord(action) && typeof action.id === "string" && typeof action.label === "string")
      && (story.mockSurfacePath === null || typeof story.mockSurfacePath === "string")
      && hasValidPolicies(story.policies)
      && (story.status === "draft" || story.status === "approved" || story.status === "rejected")
      && typeof story.rejectionReason === "string"
    ))
  ))
}

function isWorkbenchState(value: unknown): value is WorkbenchState {
  return isRecord(value)
    && value.version === 13
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
