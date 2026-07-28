import { useEffect, useRef, useState } from "react"
import { ArrowUp } from "lucide-react"

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
    <section aria-labelledby="experience-preview-heading" className="flex min-h-0 flex-col gap-2 lg:h-full">
      <div className="flex items-center justify-between gap-3">
        <h2 id="experience-preview-heading" className="text-sm font-semibold">Inline chat experience</h2>
        <span className="text-xs text-muted-foreground">{story.mockSurfacePath ? "Inline surface" : "No inline surface"}</span>
      </div>

      <div ref={chatSurfaceRef} className="flex min-h-96 flex-1 flex-col overflow-hidden border border-border bg-background lg:min-h-0">
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

            {story.mockSurfacePath && (
              <div className="mt-2 border-t border-border pt-4">
                <iframe
                  ref={iframeRef}
                  className="block w-full border-0 bg-background"
                  src={story.mockSurfacePath}
                  title={`Mock surface: ${story.title}`}
                  sandbox="allow-scripts"
                  style={{ colorScheme: theme, height: `${surfaceHeight}px` }}
                  onLoad={() => iframeRef.current?.contentWindow?.postMessage({ type: SURFACE_HEIGHT_REQUEST }, "*")}
                />
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-border bg-background px-4 py-3">
          <div className="mx-auto w-full max-w-2xl">
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
        </div>
      </div>
    </section>
  )
}
