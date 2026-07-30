import { useEffect, useState } from "react"
import { MessageSquareText, ShieldCheck } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { AgentPolicyList } from "@/workbench/AgentPolicyList"
import { BehaviorDesignEditor } from "@/workbench/BehaviorDesignEditor"
import { FeatureRail } from "@/workbench/FeatureRail"
import { ReviewControls } from "@/workbench/ReviewControls"
import { StoryEditor } from "@/workbench/StoryEditor"
import { StudioHeader, type SaveStatus } from "@/workbench/StudioHeader"
import { SurfacePreview } from "@/workbench/SurfacePreview"
import {
  exportWorkbenchState,
  loadWorkbenchState,
  resetWorkbenchState,
  saveWorkbenchState,
  type LoadResult,
} from "@/workbench/storage"
import { STUDIO_CONFIG } from "@/workbench/studioConfig"
import { applyTheme, loadTheme, saveTheme, type Theme } from "@/workbench/theme"
import type { DesignFeature, DesignStory, WorkbenchState } from "@/workbench/types"

export default function App() {
  const [loaded, setLoaded] = useState<LoadResult | null>(null)
  const [selectedFeatureId, setSelectedFeatureId] = useState("")
  const [selectedStoryId, setSelectedStoryId] = useState("")
  const [selectedView, setSelectedView] = useState<"behavior" | "feature-prompt" | "feature-policy">("behavior")
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("saving")
  const [theme, setTheme] = useState<Theme>(loadTheme)
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  useEffect(() => {
    let active = true
    void loadWorkbenchState().then((result) => {
      if (!active) return
      setLoaded(result)
      if (result.ok) {
        setSelectedFeatureId(result.state.features[0]?.id ?? "")
        setSelectedStoryId(result.state.features[0]?.stories[0]?.id ?? "")
        setSaveStatus("saved")
      } else {
        setSaveStatus("error")
      }
    })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!loaded?.ok) return
    setSaveStatus("saving")
    const timeout = window.setTimeout(() => {
      void saveWorkbenchState(loaded.state)
        .then(() => setSaveStatus("saved"))
        .catch(() => setSaveStatus("error"))
    }, 250)
    return () => window.clearTimeout(timeout)
  }, [loaded])

  useEffect(() => {
    if (!mobileNavigationOpen) return
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileNavigationOpen(false)
    }
    window.addEventListener("keydown", closeOnEscape)
    return () => window.removeEventListener("keydown", closeOnEscape)
  }, [mobileNavigationOpen])

  if (loaded === null) {
    return (
      <main className="grid min-h-dvh place-items-center bg-background p-6 text-sm text-muted-foreground">
        <div className="text-center">
          <p className="font-semibold text-foreground">{STUDIO_CONFIG.productName}</p>
          <p className="mt-1">Loading {STUDIO_CONFIG.projectName} design state...</p>
        </div>
      </main>
    )
  }

  if (!loaded.ok) {
    return (
      <main className="grid min-h-dvh place-items-center bg-muted/30 p-6">
        <div role="alert" className="w-full max-w-md rounded-xl border border-destructive/30 bg-card p-6 shadow-[var(--studio-shadow-panel)]">
          <p className="text-xs font-semibold text-primary">{STUDIO_CONFIG.productName} · {STUDIO_CONFIG.projectName}</p>
          <h1 className="mt-2 text-lg font-semibold">The saved studio data is invalid.</h1>
          <p className="mt-2 text-sm text-muted-foreground">Corpus could not load a valid design-state.json. Replace the file with the current seed only if discarding its contents is intended.</p>
          <Button
            variant="destructive"
            className="mt-5"
            onClick={() => {
              void resetWorkbenchState().then((state) => {
                setLoaded({ ok: true, state, source: "seed" })
                setSelectedFeatureId(state.features[0].id)
                setSelectedStoryId(state.features[0].stories[0].id)
              }).catch(() => setSaveStatus("error"))
            }}
          >
            Replace file with seed
          </Button>
        </div>
      </main>
    )
  }

  const state = loaded.state
  const selectedFeature = state.features.find((feature) => feature.id === selectedFeatureId) ?? state.features[0]
  const selectedStory = selectedFeature.stories.find((story) => story.id === selectedStoryId) ?? selectedFeature.stories[0]

  function commit(nextState: WorkbenchState) {
    setLoaded({ ok: true, state: nextState, source: "saved" })
  }

  function updateStory(patch: Partial<DesignStory>, preserveReview = false) {
    const nextState: WorkbenchState = {
      ...state,
      features: state.features.map((feature) => feature.id !== selectedFeature.id ? feature : {
        ...feature,
        stories: feature.stories.map((story) => story.id !== selectedStory.id ? story : {
          ...story,
          ...patch,
          ...(!preserveReview && story.status !== "draft" ? { status: "draft" as const, rejectionReason: "" } : {}),
        }),
      }),
    }
    commit(nextState)
  }

  function updateFeature(patch: Partial<DesignFeature>) {
    commit({ ...state, features: state.features.map((feature) => feature.id === selectedFeature.id ? { ...feature, ...patch } : feature) })
  }

  function selectFeature(featureId: string) {
    const feature = state.features.find((item) => item.id === featureId)
    if (!feature) return
    setSelectedFeatureId(feature.id)
    setSelectedStoryId(feature.stories[0]?.id ?? "")
    setSelectedView("behavior")
  }

  function selectStory(storyId: string) {
    setSelectedStoryId(storyId)
    setSelectedView("behavior")
  }

  function addStory() {
    const story: DesignStory = {
      id: `story-${Date.now()}`,
      title: "New behavior",
      userIntent: "",
      agentIntent: "",
      expectedBehavior: "",
      messages: [],
      mockSurfacePath: null,
      nodePolicies: [],
      capabilities: [],
      surfaces: [],
      operations: [],
      suggestedActions: [],
      status: "draft",
      rejectionReason: "",
    }
    const nextState: WorkbenchState = {
      ...state,
      features: state.features.map((feature) => feature.id === selectedFeature.id
        ? { ...feature, stories: [...feature.stories, story] }
        : feature),
    }
    commit(nextState)
    setSelectedStoryId(story.id)
    setSelectedView("behavior")
    setMobileNavigationOpen(false)
  }

  function deleteSelectedStory() {
    if (selectedStory.status !== "draft" || selectedFeature.stories.length <= 1) return
    const selectedIndex = selectedFeature.stories.findIndex((story) => story.id === selectedStory.id)
    const remainingStories = selectedFeature.stories.filter((story) => story.id !== selectedStory.id)
    const nextStory = remainingStories[Math.min(selectedIndex, remainingStories.length - 1)]
    const nextState: WorkbenchState = {
      ...state,
      features: state.features.map((feature) => feature.id === selectedFeature.id
        ? { ...feature, stories: remainingStories }
        : feature),
    }
    commit(nextState)
    setSelectedStoryId(nextStory.id)
  }

  function toggleTheme() {
    const nextTheme = theme === "light" ? "dark" : "light"
    setTheme(nextTheme)
    try {
      saveTheme(nextTheme)
    } catch { /* Theme is a browser preference, not design state. */ }
  }

  return (
    <div className="studio-shell">
      <StudioHeader
        saveStatus={saveStatus}
        theme={theme}
        onToggleTheme={toggleTheme}
        onExport={() => exportWorkbenchState(state)}
        onOpenNavigation={() => setMobileNavigationOpen(true)}
      />

      <div className="studio-workspace">
        <FeatureRail
          features={state.features}
          selectedFeatureId={selectedFeature.id}
          selectedStoryId={selectedStory.id}
          selectedView={selectedView}
          mobileOpen={mobileNavigationOpen}
          onSelectFeature={selectFeature}
          onSelectStory={selectStory}
          onSelectFeaturePrompt={() => setSelectedView("feature-prompt")}
          onSelectFeaturePolicy={() => setSelectedView("feature-policy")}
          onAddStory={addStory}
          onCloseMobile={() => setMobileNavigationOpen(false)}
        />

        {selectedView === "feature-prompt" ? (
          <main className="studio-main overflow-y-auto">
            <div className="mx-auto flex max-w-4xl flex-col gap-5 p-4 sm:p-6 lg:p-8">
              <div className="flex items-start gap-3 border-b border-border pb-5">
                <div className="grid size-9 shrink-0 place-items-center rounded-md border border-primary/20 bg-primary/10 text-primary">
                  <MessageSquareText className="size-4" />
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">{STUDIO_CONFIG.projectName} / {selectedFeature.name}</p>
                  <h2 className="mt-0.5 text-xl font-semibold tracking-[-0.025em]">{STUDIO_CONFIG.views.featurePrompt.label}</h2>
                  <p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">{STUDIO_CONFIG.views.featurePrompt.description}</p>
                </div>
              </div>
              <div className="studio-object-card bg-card p-4 sm:p-5">
                <label className="text-xs font-medium" htmlFor="feature-agent-prompt">{selectedFeature.name} Feature prompt</label>
                <Textarea
                  id="feature-agent-prompt"
                  className="mt-2 min-h-56"
                  value={selectedFeature.prompt}
                  placeholder="Define the agent's role, purpose, vocabulary, and interaction posture throughout this feature..."
                  onChange={(event) => updateFeature({ prompt: event.target.value })}
                />
              </div>
            </div>
          </main>
        ) : selectedView === "feature-policy" ? (
          <main className="studio-main overflow-y-auto">
            <div className="mx-auto flex max-w-4xl flex-col gap-5 p-4 sm:p-6 lg:p-8">
              <div className="flex items-start gap-3 border-b border-border pb-5">
                <div className="grid size-9 shrink-0 place-items-center rounded-md border border-primary/20 bg-primary/10 text-primary">
                  <ShieldCheck className="size-4" />
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">{STUDIO_CONFIG.projectName} / {selectedFeature.name}</p>
                  <h2 className="mt-0.5 text-xl font-semibold tracking-[-0.025em]">{STUDIO_CONFIG.views.featurePolicy.label}</h2>
                  <p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">{STUDIO_CONFIG.views.featurePolicy.description}</p>
                </div>
              </div>
              <div className="studio-object-card bg-card p-4 sm:p-5">
                <AgentPolicyList
                  policies={selectedFeature.policies}
                  label={`${selectedFeature.name} Feature AgentPolicy`}
                  onChange={(policies) => updateFeature({ policies })}
                />
              </div>
            </div>
          </main>
        ) : (
          <main className="studio-main">
            <div className="studio-design-grid">
              <div data-editor-pane className="studio-editor-pane">
                <div data-editor-scroll className="studio-editor-scroll px-4 py-5 sm:px-5">
                  <StoryEditor story={selectedStory} disabled={selectedStory.status !== "draft"} onChange={updateStory} />
                  <BehaviorDesignEditor story={selectedStory} disabled={selectedStory.status !== "draft"} onChange={updateStory} />
                </div>
                <div className="studio-review-bar">
                  <ReviewControls
                    key={selectedStory.id}
                    story={selectedStory}
                    canDelete={selectedFeature.stories.length > 1}
                    onChange={updateStory}
                    onDelete={deleteSelectedStory}
                  />
                </div>
              </div>
              <div data-surface-pane className="studio-preview-pane">
                <SurfacePreview story={selectedStory} theme={theme} />
              </div>
            </div>
          </main>
        )}
      </div>
    </div>
  )
}
