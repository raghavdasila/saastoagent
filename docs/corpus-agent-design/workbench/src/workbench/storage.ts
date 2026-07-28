import { createSeedState } from "@/workbench/seed"
import type { WorkbenchState } from "@/workbench/types"

export const STORAGE_KEY = "corpus.feature-design-workbench.v3"
export const V2_STORAGE_KEY = "corpus.feature-design-workbench.v2"
export const LEGACY_STORAGE_KEY = "corpus.feature-design-workbench.v1"

export type LoadResult =
  | { ok: true; state: WorkbenchState; source: "saved" | "seed" | "migrated" }
  | { ok: false }

interface LegacyStory {
  id: string
  title: string
  situation: string
  userNeed: string
  expectedBehavior: string
  outcome: string
  messages: WorkbenchState["features"][number]["stories"][number]["messages"]
  mockSurfacePath: string | null
  status: WorkbenchState["features"][number]["stories"][number]["status"]
  rejectionReason: string
}

interface LegacyState {
  version: 1
  features: Array<{ id: string; name: string; stories: LegacyStory[] }>
}

interface V2State {
  version: 2
  features: WorkbenchState["features"]
}

function hasValidFeatures(candidate: { features?: unknown }): candidate is { features: WorkbenchState["features"] } {
  if (!Array.isArray(candidate.features) || candidate.features.length === 0) return false

  return candidate.features.every((feature: unknown) => {
    if (!feature || typeof feature !== "object") return false
    const featureCandidate = feature as Record<string, unknown>
    if (
      typeof featureCandidate.id !== "string" ||
      typeof featureCandidate.name !== "string" ||
      !Array.isArray(featureCandidate.stories) ||
      featureCandidate.stories.length === 0
    ) return false

    return featureCandidate.stories.every((story: unknown) => {
      if (!story || typeof story !== "object") return false
      const storyCandidate = story as Record<string, unknown>
      if (!Array.isArray(storyCandidate.messages)) return false
      return (
        typeof storyCandidate.id === "string" &&
        typeof storyCandidate.title === "string" &&
        typeof storyCandidate.story === "string" &&
        storyCandidate.messages.every((message: unknown) => {
          if (!message || typeof message !== "object") return false
          const messageCandidate = message as Record<string, unknown>
          return (
            typeof messageCandidate.id === "string" &&
            (messageCandidate.actor === "Corpus" || messageCandidate.actor === "Owner") &&
            typeof messageCandidate.content === "string"
          )
        }) &&
        (storyCandidate.mockSurfacePath === null || typeof storyCandidate.mockSurfacePath === "string") &&
        (storyCandidate.status === "draft" || storyCandidate.status === "approved" || storyCandidate.status === "rejected") &&
        typeof storyCandidate.rejectionReason === "string"
      )
    })
  })
}

function isWorkbenchState(value: unknown): value is WorkbenchState {
  if (!value || typeof value !== "object") return false
  const candidate = value as Partial<WorkbenchState>
  return candidate.version === 3 && hasValidFeatures(candidate)
}

function isV2State(value: unknown): value is V2State {
  if (!value || typeof value !== "object") return false
  const candidate = value as Partial<V2State>
  return candidate.version === 2 && hasValidFeatures(candidate)
}

function isLegacyState(value: unknown): value is LegacyState {
  if (!value || typeof value !== "object") return false
  const candidate = value as Partial<LegacyState>
  if (candidate.version !== 1 || !Array.isArray(candidate.features) || candidate.features.length === 0) return false

  return candidate.features.every(
    (feature) =>
      feature &&
      typeof feature.id === "string" &&
      typeof feature.name === "string" &&
      Array.isArray(feature.stories) &&
      feature.stories.length > 0 &&
      feature.stories.every(
        (story) =>
          story &&
          typeof story.id === "string" &&
          typeof story.title === "string" &&
          typeof story.situation === "string" &&
          typeof story.userNeed === "string" &&
          typeof story.expectedBehavior === "string" &&
          typeof story.outcome === "string" &&
          Array.isArray(story.messages) &&
          story.messages.every(
            (message) =>
              message &&
              typeof message.id === "string" &&
              (message.actor === "Corpus" || message.actor === "Owner") &&
              typeof message.content === "string"
          ) &&
          (story.mockSurfacePath === null || typeof story.mockSurfacePath === "string") &&
          (story.status === "draft" || story.status === "approved" || story.status === "rejected") &&
          typeof story.rejectionReason === "string"
      )
  )
}

function migrateLegacyState(legacy: LegacyState): V2State {
  return {
    version: 2,
    features: legacy.features.map((feature) => ({
      ...feature,
      stories: feature.stories.map(({ situation, userNeed, expectedBehavior, outcome, ...story }) => ({
        ...story,
        story: [situation, userNeed, expectedBehavior, outcome].filter(Boolean).join("\n\n"),
      })),
    })),
  }
}

function migrateV2State(previous: V2State): WorkbenchState {
  const seed = createSeedState()
  const mergedFeatures = previous.features.map((feature) => {
    const seededFeature = seed.features.find((candidate) => candidate.id === feature.id)
    if (!seededFeature) return feature
    const existingIds = new Set(feature.stories.map((story) => story.id))
    return {
      ...feature,
      stories: [...feature.stories, ...seededFeature.stories.filter((story) => !existingIds.has(story.id))],
    }
  })
  const existingFeatureIds = new Set(mergedFeatures.map((feature) => feature.id))
  return {
    version: 3,
    features: [...mergedFeatures, ...seed.features.filter((feature) => !existingFeatureIds.has(feature.id))],
  }
}

function parseSavedState(saved: string): LoadResult {
  try {
    const parsed: unknown = JSON.parse(saved)
    return isWorkbenchState(parsed) ? { ok: true, state: parsed, source: "saved" } : { ok: false }
  } catch {
    return { ok: false }
  }
}

export function loadWorkbenchState(): LoadResult {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved !== null) return parseSavedState(saved)

  const version2Saved = localStorage.getItem(V2_STORAGE_KEY)
  if (version2Saved !== null) {
    try {
      const version2: unknown = JSON.parse(version2Saved)
      return isV2State(version2)
        ? { ok: true, state: migrateV2State(version2), source: "migrated" }
        : { ok: false }
    } catch {
      return { ok: false }
    }
  }

  const legacySaved = localStorage.getItem(LEGACY_STORAGE_KEY)
  if (legacySaved === null) return { ok: true, state: createSeedState(), source: "seed" }
  try {
    const legacy: unknown = JSON.parse(legacySaved)
    return isLegacyState(legacy)
      ? { ok: true, state: migrateV2State(migrateLegacyState(legacy)), source: "migrated" }
      : { ok: false }
  } catch {
    return { ok: false }
  }
}

export function saveWorkbenchState(state: WorkbenchState): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

export function resetWorkbenchState(): WorkbenchState {
  localStorage.removeItem(STORAGE_KEY)
  localStorage.removeItem(V2_STORAGE_KEY)
  localStorage.removeItem(LEGACY_STORAGE_KEY)
  return createSeedState()
}
