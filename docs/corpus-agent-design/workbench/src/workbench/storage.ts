import { createSeedState } from "@/workbench/seed"
import type { WorkbenchState } from "@/workbench/types"

const DESIGN_STATE_ENDPOINT = "/__design-studio/state"
let saveQueue: Promise<void> = Promise.resolve()

export type LoadResult =
  | { ok: true; state: WorkbenchState; source: "saved" | "seed" }
  | { ok: false; reason: "invalid" | "unavailable" }

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string")
}

function hasValidPolicies(value: unknown): boolean {
  if (!isRecord(value) || !isStringArray(value.policies) || !Array.isArray(value.nodes)) return false
  return value.nodes.every((node) => (
      isRecord(node)
      && typeof node.id === "string"
      && typeof node.title === "string"
      && isStringArray(node.policies)
      && Array.isArray(node.capabilities)
      && node.capabilities.every((capability) => isRecord(capability) && typeof capability.id === "string" && typeof capability.title === "string" && isStringArray(capability.policies))
      && (node.activeSurface === null || (isRecord(node.activeSurface) && typeof node.activeSurface.id === "string" && isStringArray(node.activeSurface.policies)))
      && Array.isArray(node.operations)
      && node.operations.every((operation) => isRecord(operation) && typeof operation.id === "string" && isStringArray(operation.policies))
    ))
}

function isWorkbenchState(value: unknown): value is WorkbenchState {
  if (!isRecord(value) || value.version !== 10 || !Array.isArray(value.features) || value.features.length === 0) return false
  return value.features.every((feature) => (
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
      && typeof story.story === "string"
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
      && (story.status === "draft" || story.status === "approved" || story.status === "rejected")
      && typeof story.rejectionReason === "string"
    ))
  ))
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
    return isWorkbenchState(parsed)
      ? { ok: true, state: parsed, source: "saved" }
      : { ok: false, reason: "invalid" }
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
