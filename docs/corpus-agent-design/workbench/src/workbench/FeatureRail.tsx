import { CheckCircle2, Circle, Plus, XCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
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
  onSelectFeature: (featureId: string) => void
  onSelectStory: (storyId: string) => void
  onAddStory: () => void
}

export function FeatureRail({ features, selectedFeatureId, selectedStoryId, onSelectFeature, onSelectStory, onAddStory }: FeatureRailProps) {
  const selectedFeature = features.find((feature) => feature.id === selectedFeatureId) ?? features[0]

  return (
    <aside className="flex min-h-0 min-w-0 flex-col overflow-hidden border-b border-border bg-background md:border-r md:border-b-0">
      <div className="flex shrink-0 overflow-x-auto border-b border-border p-1 md:flex-col md:overflow-visible">
        {features.map((feature) => (
          <Button
            key={feature.id}
            aria-label={`${feature.name} ${feature.stories.length}`}
            variant="ghost"
            className={cn(
              "h-7 min-w-28 justify-start rounded-none border-0 px-2 !text-[13px] font-normal focus-visible:bg-muted focus-visible:ring-0 md:min-w-0",
              feature.id === selectedFeature.id && "bg-muted/70 font-semibold text-foreground",
            )}
            onClick={() => onSelectFeature(feature.id)}
          >
            {feature.name}
            <span className="ml-auto text-[11px] font-normal text-muted-foreground tabular-nums">{feature.stories.length}</span>
          </Button>
        ))}
      </div>

      <div className="flex min-h-0 flex-col py-1">
        <div className="flex h-8 items-center justify-between gap-2 px-2">
          <p className="text-xs font-semibold text-muted-foreground">Stories</p>
          <Button aria-label="Add story" size="xs" variant="ghost" className="px-1.5 focus-visible:ring-1" onClick={onAddStory}>
            <Plus data-icon="inline-start" /> Add
          </Button>
        </div>
        <div className="grid max-h-28 min-h-0 grid-cols-2 overflow-y-auto px-1 md:max-h-none md:flex md:flex-1 md:flex-col md:overflow-x-hidden">
          {selectedFeature.stories.map((story) => {
            const StatusIcon = statusIcon[story.status]
            return (
              <Button
                key={story.id}
                variant="ghost"
                className={cn(
                  "h-auto min-h-8 w-full justify-start rounded-none border-0 border-l-2 border-transparent px-2 py-1 text-left !text-[13px] !leading-4 whitespace-normal focus-visible:border-l-ring focus-visible:bg-muted/50 focus-visible:ring-0",
                  story.id === selectedStoryId && "border-l-primary bg-muted/60 font-medium text-foreground",
                )}
                onClick={() => onSelectStory(story.id)}
              >
                <StatusIcon
                  data-icon="inline-start"
                  className={cn("size-3", story.status === "approved" && "text-emerald-600", story.status === "rejected" && "text-destructive")}
                  strokeWidth={1.8}
                />
                <span>{story.title}</span>
              </Button>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
