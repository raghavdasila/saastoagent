import { useEffect, useRef, useState } from "react"
import { ArrowUp, ChevronDown, PanelsTopLeft } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { Theme } from "@/workbench/theme"
import type { DesignStory } from "@/workbench/types"

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
export function SurfacePreview({ story, theme }: { story: DesignStory; theme: Theme }) {
  const chatSurfaceRef = useRef<HTMLDivElement>(null)
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [chatHeight, setChatHeight] = useState(DEFAULT_CHAT_HEIGHT)
  const [surfaceContentHeight, setSurfaceContentHeight] = useState(DEFAULT_SURFACE_HEIGHT)
  const surfaceHeight = resolveInlineSurfaceHeight(surfaceContentHeight, chatHeight)

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
    <section aria-labelledby="experience-preview-heading" className="flex min-h-0 flex-col gap-3 lg:h-full">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="experience-preview-heading" className="text-sm font-semibold tracking-[-0.01em]">Behavior paths</h2>
          <p className="mt-0.5 text-xs text-muted-foreground">Same task, two interaction modes</p>
        </div>
        <details className="group rounded-md border border-border bg-[var(--studio-panel-subtle)] px-2.5 py-1.5 text-xs">
          <summary className="flex cursor-pointer list-none items-center gap-1.5 font-medium text-muted-foreground [&::-webkit-details-marker]:hidden">
            <ChevronDown className="size-3 transition-transform group-open:rotate-180" />
            {story.capabilities.length} capabilities · {story.surfaces.length} surfaces · {story.operations.length} operations
          </summary>
          <div className="mt-2 space-y-1.5 border-t border-border pt-2 text-muted-foreground">
            <p><span className="font-medium text-foreground">Node AgentPolicies:</span> {story.nodePolicies.length}</p>
            {story.capabilities.map((capability, index) => <p key={`capability-${index}`}><span className="font-medium text-foreground">Capability:</span> {capability.name || "Unnamed capability"}</p>)}
            {story.operations.map((operation, index) => <p key={`operation-${index}`}><span className="font-medium text-foreground">Operation:</span> {operation.name || "Unnamed operation"}</p>)}
          </div>
        </details>
      </div>

      <div ref={chatSurfaceRef} className="grid min-h-96 flex-1 grid-rows-[minmax(0,1fr)_minmax(0,1fr)] overflow-hidden rounded-lg border border-border bg-[var(--studio-field)] shadow-[var(--studio-shadow-panel)] lg:min-h-0">
        <section aria-labelledby="surface-path-heading" className="flex min-h-0 flex-col border-b border-border">
          <PathHeader id="surface-path-heading" title="Surface path" description="The task completed through structured product UI." />
          <div className="min-h-0 flex-1 overflow-y-auto p-3">
            {story.mockSurfacePath ? (
              <iframe
                ref={iframeRef}
                className="block w-full rounded-md border-0"
                src={story.mockSurfacePath}
                title={`Mock surface: ${story.title}`}
                sandbox="allow-scripts"
                style={{ backgroundColor: "var(--studio-field)", colorScheme: theme, height: `${surfaceHeight}px` }}
                onLoad={() => iframeRef.current?.contentWindow?.postMessage({ type: SURFACE_HEIGHT_REQUEST }, "*")}
              />
            ) : (
              <div className="grid min-h-40 h-full place-items-center rounded-md border border-dashed border-border p-5 text-center text-sm text-muted-foreground">
                <div>
                  <PanelsTopLeft className="mx-auto mb-3 size-6 text-muted-foreground/70" strokeWidth={1.5} />
                  <p>No surface path designed for this behavior.</p>
                </div>
              </div>
            )}
          </div>
        </section>

        <section aria-labelledby="chat-path-heading" className="flex min-h-0 flex-col">
          <PathHeader id="chat-path-heading" title="Chat path" description="The same task completed conversationally." />
          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
            <div className="mx-auto flex min-h-full w-full max-w-2xl flex-col justify-end gap-3">
              {story.messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "max-w-[84%] rounded-xl border px-4 py-3 text-[13px] leading-relaxed shadow-[var(--studio-shadow-panel)]",
                    message.actor === "Owner"
                      ? "ml-auto border-primary/30 bg-primary text-primary-foreground"
                      : "mr-auto border-border bg-[var(--studio-panel-raised)] text-foreground",
                  )}
                >
                  <p className="mb-1 text-[11px] font-semibold opacity-65">{message.actor}</p>
                  <p>{message.content || "Empty message"}</p>
                </div>
              ))}

              {story.messages.length === 0 && <p className="text-center text-sm text-muted-foreground">No chat path drafted yet.</p>}
            </div>
          </div>
          <div className="border-t border-border bg-[var(--studio-panel)] px-4 py-3">
            {story.suggestedActions.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-2" aria-label="Suggested actions">
                {story.suggestedActions.map((action) => (
                  <Button key={action.id} type="button" variant="outline" size="sm">
                    {action.label || "Untitled suggested action"}
                  </Button>
                ))}
              </div>
            )}
            <div className="flex items-center gap-3 rounded-lg border border-input bg-[var(--studio-field)] px-3 py-2 shadow-[var(--studio-shadow-panel)]">
              <span className="min-w-0 flex-1 text-[13px] text-muted-foreground">Message Corpus...</span>
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

function PathHeader({ id, title, description }: { id: string; title: string; description: string }) {
  return (
    <div className="flex shrink-0 items-start gap-2 border-b border-border bg-[var(--studio-panel)] px-3 py-2.5">
      <ChevronDown className="mt-0.5 size-3.5 text-muted-foreground" aria-hidden="true" />
      <div>
        <h3 id={id} className="text-xs font-semibold">{title}</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
  )
}
