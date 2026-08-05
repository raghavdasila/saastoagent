import { useEffect, useState } from "react"
import { ListChecks, MessageSquareText, PanelsTopLeft, ShieldCheck } from "lucide-react"

import { cn } from "@/lib/utils"
import type { StoryReadiness } from "@/workbench/readiness"
import { ReadinessPanel } from "@/workbench/ReadinessPanel"
import { SurfacePreview } from "@/workbench/SurfacePreview"
import type { Theme } from "@/workbench/theme"
import type { DesignStory } from "@/workbench/types"

type ReviewTab = "surface" | "chat" | "readiness" | "rules"

export function ReviewPanel({ story, readiness, theme, onNavigate }: {
  story: DesignStory
  readiness: StoryReadiness
  theme: Theme
  onNavigate: (targetId: string) => void
}) {
  const [activeTab, setActiveTab] = useState<ReviewTab>(story.mockSurfacePath ? "surface" : "chat")

  useEffect(() => {
    setActiveTab(story.mockSurfacePath ? "surface" : "chat")
  }, [story.id, story.mockSurfacePath])

  const tabs: Array<{ id: ReviewTab; label: string; icon: typeof PanelsTopLeft; count?: number }> = [
    { id: "surface", label: "Surface", icon: PanelsTopLeft },
    { id: "chat", label: "Chat", icon: MessageSquareText },
    { id: "readiness", label: "Completeness", icon: ListChecks, count: readiness.blockers.length },
    { id: "rules", label: "Rules", icon: ShieldCheck },
  ]

  return (
    <section aria-labelledby="review-panel-heading" className="studio-review-panel">
      <header className="studio-review-panel-header">
        <div>
          <h2 id="review-panel-heading" className="text-sm font-semibold tracking-[-0.01em]">Review context</h2>
          <p className="mt-0.5 text-xs text-muted-foreground">Inspect the proposed interaction and its design evidence.</p>
        </div>
        <span className={cn("studio-readiness-badge", readiness.isReady ? "is-ready" : "has-blockers")}>
          {readiness.isReady ? "Ready" : `${readiness.blockers.length} blockers`}
        </span>
      </header>

      <div role="tablist" aria-label="Behavior review context" className="studio-review-tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button key={tab.id} type="button" role="tab" aria-selected={activeTab === tab.id} className="studio-review-tab" onClick={() => setActiveTab(tab.id)}>
              <Icon aria-hidden="true" />
              <span>{tab.label}</span>
              {tab.count ? <span className="studio-tab-count">{tab.count}</span> : null}
            </button>
          )
        })}
      </div>

      <div className="studio-review-content">
        {activeTab === "surface" && <SurfacePreview story={story} theme={theme} view="surface" />}
        {activeTab === "chat" && <SurfacePreview story={story} theme={theme} view="chat" />}
        {activeTab === "readiness" && <ReadinessPanel readiness={readiness} onNavigate={onNavigate} />}
        {activeTab === "rules" && <ScopedRules story={story} />}
      </div>
    </section>
  )
}

function ScopedRules({ story }: { story: DesignStory }) {
  const groups = [
    { name: "Behavior rules", policies: story.nodePolicies },
    ...story.capabilities.map((item) => ({ name: `${item.name || "Unnamed capability"} rules`, policies: item.policies })),
    ...story.surfaces.map((item) => ({ name: `${item.name || "Unnamed surface"} rules`, policies: item.policies })),
    ...story.operations.map((item) => ({ name: `${item.name || "Unnamed operation"} rules`, policies: item.policies })),
  ].filter((group) => group.policies.length > 0)

  return (
    <section aria-labelledby="scoped-rules-heading" className="studio-rules-panel">
      <h3 id="scoped-rules-heading" className="text-sm font-semibold">Rules active at this behavior</h3>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">Rules remain grouped by the product-design scope that owns them.</p>
      {groups.length === 0 ? (
        <p className="studio-readiness-empty">No behavior-scoped rules defined.</p>
      ) : (
        <div className="mt-4 divide-y divide-border border-y border-border">
          {groups.map((group, index) => (
            <section key={`${group.name}-${index}`} className="py-3">
              <h4 className="text-xs font-semibold">{group.name}</h4>
              <ul className="mt-2 space-y-2 text-xs leading-5 text-muted-foreground">
                {group.policies.map((policy, policyIndex) => <li key={policyIndex}>{policy || "Empty rule"}</li>)}
              </ul>
            </section>
          ))}
        </div>
      )}
    </section>
  )
}
