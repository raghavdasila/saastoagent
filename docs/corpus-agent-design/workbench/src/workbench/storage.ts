import { createSeedState } from "@/workbench/seed"
import type { DesignStory, WorkbenchState } from "@/workbench/types"

export const STORAGE_KEY = "corpus.feature-design-workbench.v6"
const UNUSED_V5_STORAGE_KEY = "corpus.feature-design-workbench.v5"
export const V4_STORAGE_KEY = "corpus.feature-design-workbench.v4"
export const V3_STORAGE_KEY = "corpus.feature-design-workbench.v3"
export const V2_STORAGE_KEY = "corpus.feature-design-workbench.v2"
export const LEGACY_STORAGE_KEY = "corpus.feature-design-workbench.v1"

type PreIntentStory = Omit<DesignStory, "userIntent" | "agentIntent">
type PreIntentFeature = { id: string; name: string; stories: PreIntentStory[] }
type PreActionStory = Omit<PreIntentStory, "actions">
type PreActionFeature = { id: string; name: string; stories: PreActionStory[] }

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
  messages: PreActionStory["messages"]
  mockSurfacePath: string | null
  status: PreActionStory["status"]
  rejectionReason: string
}

interface LegacyState {
  version: 1
  features: Array<{ id: string; name: string; stories: LegacyStory[] }>
}

interface V2State {
  version: 2
  features: PreActionFeature[]
}

interface V3State {
  version: 3
  features: PreActionFeature[]
}

interface V4State {
  version: 4
  features: PreIntentFeature[]
}

function hasValidBaseFeatures(candidate: { features?: unknown }): boolean {
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

function hasValidActionFeatures(candidate: { features?: unknown }): boolean {
  if (!hasValidBaseFeatures(candidate) || !Array.isArray(candidate.features)) return false
  return candidate.features.every((feature) => {
    const stories = (feature as Record<string, unknown>).stories
    return Array.isArray(stories) && stories.every((story) => {
      const actions = (story as Record<string, unknown>).actions
      return Array.isArray(actions) && actions.every((action) => {
        if (!action || typeof action !== "object") return false
        const actionCandidate = action as Record<string, unknown>
        return typeof actionCandidate.id === "string" && typeof actionCandidate.label === "string"
      })
    })
  })
}

function hasValidFeatures(candidate: { features?: unknown }): candidate is { features: WorkbenchState["features"] } {
  if (!hasValidActionFeatures(candidate) || !Array.isArray(candidate.features)) return false
  return candidate.features.every((feature) => {
    const stories = (feature as Record<string, unknown>).stories
    return Array.isArray(stories) && stories.every((story) => {
      const storyCandidate = story as Record<string, unknown>
      return typeof storyCandidate.userIntent === "string" && typeof storyCandidate.agentIntent === "string"
    })
  })
}

function isWorkbenchState(value: unknown): value is WorkbenchState {
  if (!value || typeof value !== "object") return false
  const candidate = value as Partial<WorkbenchState>
  return candidate.version === 6 && hasValidFeatures(candidate)
}

function isV4State(value: unknown): value is V4State {
  if (!value || typeof value !== "object") return false
  const candidate = value as Partial<V4State>
  return candidate.version === 4 && hasValidActionFeatures(candidate)
}

function isV3State(value: unknown): value is V3State {
  if (!value || typeof value !== "object") return false
  const candidate = value as Partial<V3State>
  return candidate.version === 3 && hasValidBaseFeatures(candidate)
}

function isV2State(value: unknown): value is V2State {
  if (!value || typeof value !== "object") return false
  const candidate = value as Partial<V2State>
  return candidate.version === 2 && hasValidBaseFeatures(candidate)
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

function withoutActions(story: DesignStory): PreActionStory {
  const { actions: _actions, userIntent: _userIntent, agentIntent: _agentIntent, ...preActionStory } = story
  return preActionStory
}

function migrateV2State(previous: V2State): V3State {
  const seed = createSeedState()
  const mergedFeatures = previous.features.map((feature) => {
    const seededFeature = seed.features.find((candidate) => candidate.id === feature.id)
    if (!seededFeature) return feature
    const existingIds = new Set(feature.stories.map((story) => story.id))
    return {
      ...feature,
      stories: [
        ...feature.stories,
        ...seededFeature.stories.filter((story) => !existingIds.has(story.id)).map(withoutActions),
      ],
    }
  })
  const existingFeatureIds = new Set(mergedFeatures.map((feature) => feature.id))
  return {
    version: 3,
    features: [
      ...mergedFeatures,
      ...seed.features
        .filter((feature) => !existingFeatureIds.has(feature.id))
        .map((feature) => ({ ...feature, stories: feature.stories.map(withoutActions) })),
    ],
  }
}

function migrateV3State(previous: V3State): V4State {
  const seed = createSeedState()
  return {
    version: 4,
    features: previous.features.map((feature) => {
      const seededFeature = seed.features.find((candidate) => candidate.id === feature.id)
      return {
        ...feature,
        stories: feature.stories.map((story) => {
          const seededStory = seededFeature?.stories.find((candidate) => candidate.id === story.id)
          return {
            ...story,
            actions: seededStory?.actions ?? [],
            mockSurfacePath: seededStory ? seededStory.mockSurfacePath : story.mockSurfacePath,
          }
        }),
      }
    }),
  }
}

function migrateV4State(previous: V4State): WorkbenchState {
  const seed = createSeedState()
  return {
    version: 6,
    features: previous.features.map((feature) => {
      const seededFeature = seed.features.find((candidate) => candidate.id === feature.id)
      return {
        ...feature,
        stories: feature.stories.map((story) => {
          const seededStory = seededFeature?.stories.find((candidate) => candidate.id === story.id)
          return {
            ...story,
            userIntent: seededStory?.userIntent ?? "",
            agentIntent: seededStory?.agentIntent ?? "",
          }
        }),
      }
    }),
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

  const version4Saved = localStorage.getItem(V4_STORAGE_KEY)
  if (version4Saved !== null) {
    try {
      const version4: unknown = JSON.parse(version4Saved)
      return isV4State(version4)
        ? { ok: true, state: migrateV4State(version4), source: "migrated" }
        : { ok: false }
    } catch {
      return { ok: false }
    }
  }

  const version3Saved = localStorage.getItem(V3_STORAGE_KEY)
  if (version3Saved !== null) {
    try {
      const version3: unknown = JSON.parse(version3Saved)
      return isV3State(version3)
        ? { ok: true, state: migrateV4State(migrateV3State(version3)), source: "migrated" }
        : { ok: false }
    } catch {
      return { ok: false }
    }
  }

  const version2Saved = localStorage.getItem(V2_STORAGE_KEY)
  if (version2Saved !== null) {
    try {
      const version2: unknown = JSON.parse(version2Saved)
      return isV2State(version2)
        ? { ok: true, state: migrateV4State(migrateV3State(migrateV2State(version2))), source: "migrated" }
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
      ? { ok: true, state: migrateV4State(migrateV3State(migrateV2State(migrateLegacyState(legacy)))), source: "migrated" }
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
  localStorage.removeItem(UNUSED_V5_STORAGE_KEY)
  localStorage.removeItem(V4_STORAGE_KEY)
  localStorage.removeItem(V3_STORAGE_KEY)
  localStorage.removeItem(V2_STORAGE_KEY)
  localStorage.removeItem(LEGACY_STORAGE_KEY)
  return createSeedState()
}
