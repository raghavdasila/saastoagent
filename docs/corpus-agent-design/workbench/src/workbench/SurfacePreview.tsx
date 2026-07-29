import { useEffect, useRef, useState } from "react"
import { ArrowUp } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { Theme } from "@/workbench/theme"
import type { DesignFeature, DesignStory } from "@/workbench/types"

const DEFAULT_CHAT_HEIGHT = 640
const DEFAULT_SURFACE_HEIGHT = 240
const SURFACE_HEIGHT_MESSAGE = "corpus-design-surface-height"
const SURFACE_HEIGHT_REQUEST = "corpus-design-surface-height-request"

export function resolveInlineSurfaceHeight(contentHeight: number, chatHeight: number) {
  const safeContentHeight = Number.isFinite(contentHeight) && contentHeight > 0
    ? Math.ceil(contentHeight)
    : DEFAULT_SURFACE_HEIGHT
  const safeChatHeight = Number.isFinite(chatHeight) && chatHeight > 0
    ? chatHeight
    : DEFAULT_CHAT_HEIGHT

  return Math.max(1, Math.min(safeContentHeight, Math.floor(safeChatHeight / 2)))
}

const FRAMEWORK_POLICIES = [
  { id: "routedeck.execution_authority", instruction: "Call only operations legal in the current RouteDeck context." },
  { id: "routedeck.intent_authority", instruction: "Treat legal operations as permitted, not automatically requested." },
  { id: "routedeck.state_authority", instruction: "Treat completed results and refreshed RouteDeck context as application-state authority." },
]

export function SurfacePreview({ story, feature, theme }: { story: DesignStory; feature: DesignFeature; theme: Theme }) {
  const chatSurfaceRef = useRef<HTMLDivElement>(null)
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [chatHeight, setChatHeight] = useState(DEFAULT_CHAT_HEIGHT)
  const [surfaceContentHeight, setSurfaceContentHeight] = useState(DEFAULT_SURFACE_HEIGHT)
  const [policyNodeId, setPolicyNodeId] = useState(feature.policies.nodes[0]?.id ?? "")
  const surfaceHeight = resolveInlineSurfaceHeight(surfaceContentHeight, chatHeight)
  const policyNode = feature.policies.nodes.find((node) => node.id === policyNodeId) ?? feature.policies.nodes[0]
  const effectivePolicies = [...new Set([
    ...feature.policies.policies,
    ...(policyNode?.policies ?? []),
    ...(policyNode?.capabilities.flatMap((capability) => capability.policies) ?? []),
    ...(policyNode?.activeSurface?.policies ?? []),
    ...(policyNode?.operations.flatMap((operation) => operation.policies) ?? []),
  ].map((policy) => policy.trim()).filter(Boolean))]

  useEffect(() => {
    setPolicyNodeId(feature.policies.nodes[0]?.id ?? "")
  }, [feature.id, feature.policies.nodes])

  useEffect(() => {
    const chatSurface = chatSurfaceRef.current
    if (!chatSurface) return

    const measureChat = () => {
      const nextHeight = chatSurface.getBoundingClientRect().height
      if (nextHeight > 0) setChatHeight(nextHeight)
    }

    measureChat()
    window.addEventListener("resize", measureChat)

    if (typeof ResizeObserver === "undefined") {
      return () => window.removeEventListener("resize", measureChat)
    }

    const observer = new ResizeObserver(measureChat)
    observer.observe(chatSurface)

    return () => {
      observer.disconnect()
      window.removeEventListener("resize", measureChat)
    }
  }, [])

  useEffect(() => {
    setSurfaceContentHeight(DEFAULT_SURFACE_HEIGHT)
  }, [story.mockSurfacePath])

  useEffect(() => {
    const receiveHeight = (event: MessageEvent) => {
      const frameWindow = iframeRef.current?.contentWindow
      const data = event.data as { type?: unknown; height?: unknown } | null

      if (
        !frameWindow
        || event.source !== frameWindow
        || data?.type !== SURFACE_HEIGHT_MESSAGE
        || typeof data.height !== "number"
        || !Number.isFinite(data.height)
        || data.height <= 0
      ) return

      setSurfaceContentHeight(Math.ceil(data.height))
    }

    window.addEventListener("message", receiveHeight)
    return () => window.removeEventListener("message", receiveHeight)
  }, [])

  return (
    <section aria-labelledby="experience-preview-heading" className="flex min-h-0 flex-col gap-2 lg:h-full">
      <div className="flex items-center justify-between gap-3">
        <h2 id="experience-preview-heading" className="text-sm font-semibold">Behavior paths</h2>
        <span className="text-xs text-muted-foreground">Same task, two interaction modes</span>
      </div>

      <div ref={chatSurfaceRef} className="grid min-h-96 flex-1 grid-rows-[minmax(0,1fr)_minmax(0,1fr)] overflow-hidden border border-border bg-background lg:min-h-0">
        <section aria-labelledby="surface-path-heading" className="flex min-h-0 flex-col border-b border-border">
          <div className="border-b border-border px-3 py-2">
            <h3 id="surface-path-heading" className="text-xs font-semibold uppercase tracking-wide">Surface path</h3>
            <p className="text-xs text-muted-foreground">The task completed through structured product UI.</p>
            {policyNode?.activeSurface && <p className="mt-1 text-[11px] text-muted-foreground">Surface policy: {policyNode.activeSurface.policies.length ? policyNode.activeSurface.policies.join(" · ") : "none"}</p>}
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-3">
            {story.mockSurfacePath ? (
              <iframe
                ref={iframeRef}
                className="block w-full border-0 bg-background"
                src={story.mockSurfacePath}
                title={`Mock surface: ${story.title}`}
                sandbox="allow-scripts"
                style={{ colorScheme: theme, height: `${surfaceHeight}px` }}
                onLoad={() => iframeRef.current?.contentWindow?.postMessage({ type: SURFACE_HEIGHT_REQUEST }, "*")}
              />
            ) : (
              <div className="grid min-h-40 place-items-center border border-dashed border-border p-5 text-center text-sm text-muted-foreground">
                No surface path designed for this behavior.
              </div>
            )}
          </div>
        </section>

        <section aria-labelledby="chat-path-heading" className="flex min-h-0 flex-col">
          <div className="border-b border-border px-3 py-2">
            <div className="flex items-start justify-between gap-3">
              <div><h3 id="chat-path-heading" className="text-xs font-semibold uppercase tracking-wide">Chat path</h3><p className="text-xs text-muted-foreground">The same task completed conversationally.</p></div>
              {feature.policies.nodes.length > 0 && <label className="text-[11px] text-muted-foreground">Policy context<select className="ml-2 h-7 border border-input bg-background px-2 text-xs text-foreground" value={policyNode?.id ?? ""} onChange={(event) => setPolicyNodeId(event.target.value)}>{feature.policies.nodes.map((node) => <option key={node.id} value={node.id}>{node.id}</option>)}</select></label>}
            </div>
            <details className="mt-2 text-xs">
              <summary className="cursor-pointer font-medium">Effective AgentPolicy ({FRAMEWORK_POLICIES.length + effectivePolicies.length})</summary>
              <div className="mt-2 space-y-1 border-l border-border pl-2">
                {FRAMEWORK_POLICIES.map((policy) => <p key={policy.id}><span className="font-mono text-[11px]">{policy.id}</span> — {policy.instruction}</p>)}
                {effectivePolicies.map((policy, index) => <p key={`${policy}-${index}`}>{policy}</p>)}
              </div>
            </details>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
            <div className="mx-auto flex min-h-full w-full max-w-2xl flex-col justify-end gap-3">
            {story.messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "max-w-[84%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                  message.actor === "Owner"
                    ? "ml-auto bg-primary text-primary-foreground"
                    : "mr-auto bg-muted text-foreground",
                )}
              >
                <p className="mb-1 text-[11px] font-semibold opacity-65">{message.actor}</p>
                <p>{message.content || "Empty message"}</p>
              </div>
            ))}

            {story.messages.length === 0 && <p className="text-center text-sm text-muted-foreground">No chat path drafted yet.</p>}
            </div>
          </div>
          <div className="border-t border-border bg-background px-4 py-3">
            {story.actions.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-2" aria-label="Available actions">
                {story.actions.map((action) => (
                  <Button key={action.id} type="button" variant="outline" size="sm">
                    {action.label || "Untitled action"}
                  </Button>
                ))}
              </div>
            )}
            <div className="flex items-center gap-3 rounded-2xl border border-input bg-card px-4 py-3 shadow-sm">
              <span className="min-w-0 flex-1 text-sm text-muted-foreground">Message Corpus...</span>
              <span className="grid size-8 place-items-center rounded-full bg-primary text-primary-foreground" aria-hidden="true">
                <ArrowUp className="size-4" />
              </span>
            </div>
          </div>
        </section>
      </div>
    </section>
  )
}
