import { Skeleton } from "@/components/ui/skeleton"
import type { Theme } from "@/workbench/theme"
import type { DesignStory } from "@/workbench/types"

export function SurfacePreview({ story, theme }: { story: DesignStory; theme: Theme }) {
  return (
    <section aria-labelledby="mock-surface-heading" className="flex min-h-0 flex-col gap-3 lg:h-full">
      <div>
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Mock surface</p>
        <h2 id="mock-surface-heading" className="mt-1 text-base font-semibold">Surface preview</h2>
      </div>

      <div className="min-h-96 flex-1 overflow-hidden rounded-xl border border-border bg-muted/30 lg:min-h-0">
        {story.mockSurfacePath ? (
          <iframe
            className="h-full min-h-96 w-full border-0 bg-background lg:min-h-0"
            src={story.mockSurfacePath}
            title={`Mock surface: ${story.title}`}
            sandbox=""
            style={{ colorScheme: theme }}
          />
        ) : (
          <div className="flex h-full min-h-96 items-center justify-center p-6 lg:min-h-0">
            <div className="flex w-full max-w-sm flex-col gap-4 rounded-xl border border-border bg-card p-5">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-4/5" />
              <Skeleton className="mt-2 h-8 w-28 self-end" />
              <p className="text-center text-xs text-muted-foreground">No surface yet</p>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
