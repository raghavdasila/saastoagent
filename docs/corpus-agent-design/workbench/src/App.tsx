import { useEffect, useState } from "react"
import { FlaskConical, Moon, Save, Sun } from "lucide-react"

import { Button } from "@/components/ui/button"
import { FeatureRail } from "@/workbench/FeatureRail"
import { MockActionEditor } from "@/workbench/MockActionEditor"
import { PolicyScopeEditor } from "@/workbench/PolicyScopeEditor"
import { ReviewControls } from "@/workbench/ReviewControls"
import { StoryEditor } from "@/workbench/StoryEditor"
import { SurfacePreview } from "@/workbench/SurfacePreview"
import { loadWorkbenchState, resetWorkbenchState, saveWorkbenchState, type LoadResult } from "@/workbench/storage"
import { applyTheme, loadTheme, saveTheme, type Theme } from "@/workbench/theme"
import type { DesignFeature, DesignStory, WorkbenchState } from "@/workbench/types"

type SaveStatus = "saving" | "saved" | "error"

export default function App() {
  const [loaded, setLoaded] = useState<LoadResult | null>(null)
  const [selectedFeatureId, setSelectedFeatureId] = useState("")
  const [selectedStoryId, setSelectedStoryId] = useState("")
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("saving")
  const [theme, setTheme] = useState<Theme>(loadTheme)

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

  if (loaded === null) {
    return <main className="grid min-h-dvh place-items-center bg-muted/30 p-6 text-sm text-muted-foreground">Loading design-state.json...</main>
  }

  if (!loaded.ok) {
    return (
      <main className="grid min-h-dvh place-items-center bg-muted/30 p-6">
        <div role="alert" className="w-full max-w-md rounded-xl border border-destructive/30 bg-card p-6 shadow-sm">
          <h1 className="text-lg font-semibold">The saved workbench data is invalid.</h1>
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
  }

  function addStory() {
    const story: DesignStory = {
      id: `story-${Date.now()}`,
      title: "New user story",
      userIntent: "",
      agentIntent: "",
      story: "",
      messages: [],
      actions: [],
      mockSurfacePath: null,
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
    <div className="grid h-dvh overflow-hidden grid-rows-[auto_minmax(0,1fr)] bg-background">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-3 py-2 sm:px-4">
        <div className="flex min-w-0 items-center gap-2.5">
          <FlaskConical className="size-5 shrink-0 text-primary" />
          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold tracking-tight">Corpus agent design</h1>
            <p className="text-xs text-muted-foreground">Behavior sections 0–4 · review workspace</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={saveStatus === "error" ? "flex items-center gap-1.5 text-sm text-destructive" : "flex items-center gap-1.5 text-sm text-muted-foreground"} role={saveStatus === "error" ? "alert" : undefined}>
            <Save /> {saveStatus === "error" ? "File not saved" : saveStatus === "saving" ? "Saving file..." : "Saved to file"}
          </div>
          <Button size="icon" variant="ghost" aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`} onClick={toggleTheme}>
            {theme === "light" ? <Moon /> : <Sun />}
          </Button>
        </div>
      </header>

      <div className="grid min-h-0 overflow-hidden grid-rows-[auto_minmax(0,1fr)] md:grid-cols-[220px_minmax(0,1fr)] md:grid-rows-1">
        <FeatureRail
          features={state.features}
          selectedFeatureId={selectedFeature.id}
          selectedStoryId={selectedStory.id}
          onSelectFeature={selectFeature}
          onSelectStory={setSelectedStoryId}
          onAddStory={addStory}
        />

        <main className="min-h-0 min-w-0 overflow-y-auto lg:overflow-hidden">
          <div className="mx-auto grid min-h-0 max-w-[1480px] lg:h-full lg:grid-cols-[minmax(360px,0.85fr)_minmax(440px,1.15fr)]">
            <div data-editor-pane className="min-w-0 lg:grid lg:min-h-0 lg:grid-rows-[minmax(0,1fr)_auto]">
              <div data-editor-scroll className="flex min-w-0 flex-col gap-4 p-3 lg:min-h-0 lg:overflow-y-auto lg:p-4">
                <StoryEditor story={selectedStory} disabled={selectedStory.status !== "draft"} onChange={updateStory} />
                <div className="border-t border-border pt-4">
                  <MockActionEditor actions={selectedStory.actions} disabled={selectedStory.status !== "draft"} onChange={(actions) => updateStory({ actions })} />
                </div>
                <PolicyScopeEditor policies={selectedFeature.policies} onChange={(policies) => updateFeature({ policies })} />
              </div>
              <div className="border-t border-border p-3">
                <ReviewControls
                  key={selectedStory.id}
                  story={selectedStory}
                  canDelete={selectedFeature.stories.length > 1}
                  onChange={updateStory}
                  onDelete={deleteSelectedStory}
                />
              </div>
            </div>
            <div data-surface-pane className="min-h-0 border-t border-border p-3 lg:border-t-0 lg:border-l lg:p-4">
              <SurfacePreview story={selectedStory} feature={selectedFeature} theme={theme} />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
