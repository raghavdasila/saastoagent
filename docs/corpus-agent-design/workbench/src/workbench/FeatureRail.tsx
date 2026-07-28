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
    <aside className="flex min-h-0 min-w-0 flex-col overflow-hidden border-b border-border bg-sidebar md:border-r md:border-b-0">
      <div className="flex shrink-0 gap-1 overflow-x-auto p-2 md:flex-col md:overflow-visible">
        {features.map((feature) => (
          <Button
            key={feature.id}
            aria-label={`${feature.name} ${feature.stories.length}`}
            variant={feature.id === selectedFeature.id ? "secondary" : "ghost"}
            className="justify-start"
            onClick={() => onSelectFeature(feature.id)}
          >
            {feature.name}
            <span className="ml-auto text-xs text-muted-foreground">{feature.stories.length}</span>
          </Button>
        ))}
      </div>

      <div className="flex min-h-0 flex-col border-t border-border p-2">
        <div className="mb-1 flex items-center justify-between gap-2 px-1">
          <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">User stories</p>
          <Button size="sm" variant="ghost" onClick={onAddStory}>
            <Plus data-icon="inline-start" /> Add story
          </Button>
        </div>
        <div className="grid max-h-28 min-h-0 grid-cols-2 gap-1 overflow-y-auto md:max-h-none md:flex md:flex-1 md:flex-col md:overflow-x-hidden">
          {selectedFeature.stories.map((story) => {
            const StatusIcon = statusIcon[story.status]
            return (
              <Button
                key={story.id}
                variant="ghost"
                className={cn("h-auto w-full justify-start py-2 text-left whitespace-normal", story.id === selectedStoryId && "bg-accent text-accent-foreground")}
                onClick={() => onSelectStory(story.id)}
              >
                <StatusIcon data-icon="inline-start" className={cn(story.status === "approved" && "text-emerald-600", story.status === "rejected" && "text-destructive")} />
                <span>{story.title}</span>
              </Button>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
