import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  RouteDeckDebugger,
  type RouteDeckProjection,
} from '@routedeck/react'
import {
  AlertTriangle,
  Loader2,
  Maximize2,
  Minimize2,
} from 'lucide-react'

import { api } from '@/lib/api'
import { useThemeStore } from '@/stores/themeStore'
import type { AppGraphState } from '@/types/appGraph'
import type { CorpusDiagnosticsSnapshot } from '@/types/corpus'

export function CorpusRouteDeckDiagnostics({
  projection,
  graphState,
}: {
  projection: RouteDeckProjection
  graphState: AppGraphState | null
}) {
  const theme = useThemeStore((state) => state.theme)
  const [open, setOpen] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(projection.graph_node)
  const [snapshot, setSnapshot] = useState<CorpusDiagnosticsSnapshot | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    setSelectedNodeId(projection.graph_node)
  }, [projection.graph_node])

  useEffect(() => {
    if (!open) return
    setLoadError(null)
    const params = new URLSearchParams()
    if (graphState?.node) params.set('node_id', graphState.node)
    if (graphState?.active_saas_agent_id) params.set('saas_agent_id', graphState.active_saas_agent_id)
    params.set('projection_version', String(projection.projection_version))
    void api
      .getStream(`/diagnostics/stream?${params.toString()}`, (eventType, data) => {
        if (eventType === 'diagnostic_event') {
          const payload = (data.snapshot || null) as CorpusDiagnosticsSnapshot | null
          setSnapshot(payload)
        }
      })
      .catch((error) => {
        setLoadError(error instanceof Error ? error.message : 'Diagnostics failed to load.')
      })
  }, [open, projection, graphState])

  useEffect(() => {
    if (open) return
    setFullscreen(false)
  }, [open])

  useEffect(() => {
    if (!fullscreen) return undefined
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setFullscreen(false)
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [fullscreen])

  const diagnosticsContent = (
    <div
      className={
        fullscreen
          ? 'flex h-full w-full flex-col rounded-[0.95rem] border border-border/25 bg-card/95 p-4 text-xs shadow-[0_32px_80px_-48px_hsl(var(--foreground)/0.72)] dark:border-white/10 dark:bg-[#1c1d20]/95 dark:shadow-black/50'
          : 'mt-3 max-h-[calc(100vh-13rem)] overflow-y-auto rounded-xl border border-border/25 bg-card/90 p-4 text-xs shadow-inner dark:border-white/10 dark:bg-muted/90'
      }
      data-testid={fullscreen ? 'diagnostics-fullscreen' : 'diagnostics-panel'}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <div className="font-medium text-foreground">RouteDeck navgraph diagnostics</div>
          <div className="mt-1 font-mono text-[11px] text-muted-foreground">
            {projection.current_context} / {projection.graph_node} / v{projection.projection_version}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {fullscreen && (
            <button
              type="button"
              onClick={() => setFullscreen(false)}
              className="surface-outline-button inline-flex items-center gap-2 px-3 py-1 text-xs"
            >
              <Minimize2 className="h-3.5 w-3.5" />
              Docked
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              setFullscreen(false)
              setOpen(false)
            }}
            className="surface-outline-button px-3 py-1 text-xs"
          >
            Close
          </button>
        </div>
      </div>

      <div className={fullscreen ? 'min-h-0 flex-1 overflow-y-auto pr-1' : ''}>
        {loadError && (
          <div className="mb-4 rounded-[0.625rem] bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
            {loadError}
          </div>
        )}

        {snapshot ? (
          <>
            <RouteDeckDebugger
              graphManifest={snapshot.graph_manifest as never}
              snapshot={snapshot.runtime_snapshot as never}
              selectedNodeId={selectedNodeId}
              onSelectedNodeChange={setSelectedNodeId}
              themeMode={theme}
              canvasClassName={fullscreen ? 'h-[calc(100vh-21rem)] min-h-[28rem]' : 'h-[30rem]'}
            />

            <details className="mt-4 rounded-[0.625rem] bg-slate-950 p-3 text-[11px] text-slate-100">
              <summary className="cursor-pointer font-semibold">Raw RouteDeck navgraph JSON</summary>
              <pre className="mt-3 max-h-96 overflow-auto">
                {JSON.stringify(snapshot, null, 2)}
              </pre>
            </details>
          </>
        ) : (
          <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading diagnostics
          </div>
        )}
      </div>
    </div>
  )

  return (
    <section className="mt-6" data-testid="diagnostics-sidebar">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="surface-outline-button inline-flex items-center gap-2 text-xs"
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          Diagnostics
        </button>
        {open && !fullscreen && (
          <button
            type="button"
            onClick={() => setFullscreen(true)}
            className="surface-outline-button inline-flex items-center gap-2 px-3 py-1 text-xs"
          >
            <Maximize2 className="h-3.5 w-3.5" />
            Full screen
          </button>
        )}
      </div>
      {open && !fullscreen && diagnosticsContent}
      {open && fullscreen && typeof document !== 'undefined'
        ? createPortal(
            <div className="fixed inset-0 z-[90] bg-background/72 p-4 backdrop-blur-sm">
              <div className="mx-auto h-full max-w-[120rem]">
                {diagnosticsContent}
              </div>
            </div>,
            document.body,
          )
        : null}
    </section>
  )
}

export { CorpusRouteDeckDiagnostics as DiagnosticsPanel }
