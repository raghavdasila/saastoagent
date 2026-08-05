import {
  AlertCircle,
  CheckCircle2,
  Circle,
  MessageSquareText,
  Plus,
  ShieldCheck,
  X,
  XCircle,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { STUDIO_CONFIG } from "@/workbench/studioConfig"
import { getStoryReadiness } from "@/workbench/readiness"
import type { DesignFeature, ReviewStatus } from "@/workbench/types"

const statusIcon: Record<ReviewStatus, typeof Circle> = {
  draft: Circle,
  approved: CheckCircle2,
  rejected: XCircle,
}

interface FeatureRailProps {
  features: DesignFeature[]
  selectedFeatureId: string
  selectedStoryId: string
  selectedView: "behavior" | "feature-prompt" | "feature-policy"
  mobileOpen: boolean
  onSelectFeature: (featureId: string) => void
  onSelectStory: (storyId: string) => void
  onSelectFeaturePrompt: () => void
  onSelectFeaturePolicy: () => void
  onAddStory: () => void
  onCloseMobile: () => void
}

export function FeatureRail({
  features,
  selectedFeatureId,
  selectedStoryId,
  selectedView,
  mobileOpen,
  onSelectFeature,
  onSelectStory,
  onSelectFeaturePrompt,
  onSelectFeaturePolicy,
  onAddStory,
  onCloseMobile,
}: FeatureRailProps) {
  const selectedFeature = features.find((feature) => feature.id === selectedFeatureId) ?? features[0]
  const featurePolicyCount = selectedFeature.policies.length

  function selectFeature(featureId: string) {
    onSelectFeature(featureId)
    onCloseMobile()
  }

  function selectStory(storyId: string) {
    onSelectStory(storyId)
    onCloseMobile()
  }

  function selectPolicies() {
    onSelectFeaturePolicy()
    onCloseMobile()
  }

  function selectPrompt() {
    onSelectFeaturePrompt()
    onCloseMobile()
  }

  return (
    <>
      <button
        type="button"
        className="studio-mobile-backdrop"
        data-open={mobileOpen}
        aria-label="Close project navigation"
        tabIndex={mobileOpen ? 0 : -1}
        onClick={onCloseMobile}
      />
      <aside className="studio-rail" data-open={mobileOpen} aria-label="Corpus project navigation">
        <div className="flex h-11 shrink-0 items-center justify-between border-b border-border px-3">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">Features</p>
            <p className="text-xs font-medium md:hidden">{STUDIO_CONFIG.projectName}</p>
          </div>
          <Button type="button" size="icon-xs" variant="ghost" className="md:hidden" aria-label="Close project navigation" onClick={onCloseMobile}>
            <X />
          </Button>
        </div>

        <nav aria-label="Features" className="shrink-0 border-b border-border p-2">
          <div className="space-y-0.5">
            {features.map((feature) => (
              <Button
                key={feature.id}
                aria-label={`${feature.name} ${feature.stories.length}`}
                variant="ghost"
                className={cn(
                  "h-9 w-full justify-start border border-transparent px-2.5 !text-[13px] font-normal focus-visible:ring-2",
                  feature.id === selectedFeature.id && "border-primary/15 bg-primary/10 font-medium text-foreground",
                )}
                onClick={() => selectFeature(feature.id)}
              >
                <span className="truncate">{feature.name}</span>
                <span className="ml-auto text-[11px] font-normal text-muted-foreground tabular-nums">{feature.stories.length}</span>
              </Button>
            ))}
          </div>
        </nav>

        <div className="shrink-0 border-b border-border p-2">
          <Button
            aria-label={STUDIO_CONFIG.featurePromptLabel}
            variant="ghost"
            className={cn(
              "h-9 w-full justify-start border border-transparent px-2.5 !text-[13px] font-normal focus-visible:ring-2",
              selectedView === "feature-prompt" && "border-primary/15 bg-primary/10 font-medium text-foreground",
            )}
            onClick={selectPrompt}
          >
            <MessageSquareText data-icon="inline-start" className={cn("size-3.5", selectedView === "feature-prompt" ? "text-primary" : "text-muted-foreground")} strokeWidth={1.8} />
            {STUDIO_CONFIG.featurePromptLabel}
          </Button>
          <Button
            aria-label={STUDIO_CONFIG.featurePolicyLabel}
            variant="ghost"
            className={cn(
              "h-9 w-full justify-start border border-transparent px-2.5 !text-[13px] font-normal focus-visible:ring-2",
              selectedView === "feature-policy" && "border-primary/15 bg-primary/10 font-medium text-foreground",
            )}
            onClick={selectPolicies}
          >
            <ShieldCheck data-icon="inline-start" className={cn("size-3.5", selectedView === "feature-policy" ? "text-primary" : "text-muted-foreground")} strokeWidth={1.8} />
            {STUDIO_CONFIG.featurePolicyLabel}
            <span className="ml-auto text-[11px] font-normal text-muted-foreground tabular-nums">{featurePolicyCount}</span>
          </Button>
        </div>

        <div className="flex min-h-0 flex-1 flex-col py-2">
          <div className="flex h-8 shrink-0 items-center justify-between gap-2 px-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">{STUDIO_CONFIG.behaviorCollectionLabel}</p>
            <Button aria-label="Add behavior" size="xs" variant="ghost" className="px-1.5" onClick={onAddStory}>
              <Plus data-icon="inline-start" /> Add
            </Button>
          </div>
          <div className="min-h-0 flex-1 space-y-0.5 overflow-y-auto px-2 pb-2">
            {selectedFeature.stories.map((story) => {
              const readiness = getStoryReadiness(story)
              const StatusIcon = statusIcon[story.status]
              const selected = selectedView === "behavior" && story.id === selectedStoryId
              const stateLabel = readiness.isReady ? story.status : `${readiness.blockers.length} blocking issues`
              return (
                <Button
                  key={story.id}
                  aria-label={`${story.title} · ${stateLabel}`}
                  variant="ghost"
                  className={cn(
                    "h-auto min-h-9 w-full justify-start border border-transparent px-2.5 py-1.5 text-left !text-[13px] !leading-4 whitespace-normal focus-visible:ring-2",
                    selected && "border-primary/15 bg-primary/10 font-medium text-foreground",
                  )}
                  onClick={() => selectStory(story.id)}
                >
                  {readiness.isReady ? <StatusIcon
                    data-icon="inline-start"
                    className={cn(
                      "size-3.5",
                      story.status === "draft" && (selected ? "text-primary" : "text-muted-foreground"),
                      story.status === "approved" && "text-[var(--studio-success)]",
                      story.status === "rejected" && "text-destructive",
                    )}
                    strokeWidth={1.8}
                  /> : <AlertCircle data-icon="inline-start" className="size-3.5 text-[var(--studio-warning)]" strokeWidth={1.8} />}
                  <span className="min-w-0 flex-1">{story.title}</span>
                  {!readiness.isReady && <span className="studio-rail-issue-count" aria-hidden="true">{readiness.blockers.length}</span>}
                </Button>
              )
            })}
          </div>
        </div>

        <div className="shrink-0 border-t border-border px-3 py-2 text-[11px] text-muted-foreground">
          {selectedFeature.name} · {selectedFeature.stories.length} behaviors
        </div>
      </aside>
    </>
  )
}
