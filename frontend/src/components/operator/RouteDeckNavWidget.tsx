import { GitBranch, Maximize2, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { RouteDeckDebugger } from '@routedeck/react'

import type { EntryGraphManifest, GatewayNode, RouteDeckRuntimeSnapshot } from '@/types/entry'

interface RouteDeckNavWidgetProps {
  graphNode?: GatewayNode | null
  graphManifest?: EntryGraphManifest | null
  routeDeckSnapshot?: RouteDeckRuntimeSnapshot | null
  selectedDebugNode?: string | null
  onSelectedDebugNodeChange: (nodeId: string | null) => void
  runId?: string | null
  sessionId?: string | null
}

export function RouteDeckNavWidget({
  graphNode,
  graphManifest,
  routeDeckSnapshot,
  selectedDebugNode,
  onSelectedDebugNodeChange,
  runId,
  sessionId,
}: RouteDeckNavWidgetProps) {
  const [mapOpen, setMapOpen] = useState(false)
  const currentNode = selectedDebugNode || routeDeckSnapshot?.current_node || graphNode || null
  const activeNode = graphManifest?.nodes.find((node) => node.id === currentNode) || null
  const validActionCount = routeDeckSnapshot?.valid_actions?.length ?? 0
  const blockedCount = routeDeckSnapshot?.blocked_actions?.length ?? 0
  const nextCount = useMemo(
    () => (graphManifest?.edges || []).filter((edge) => edge.from === currentNode).length,
    [currentNode, graphManifest?.edges],
  )

  return (
    <>
      <section className="rounded-xl border border-slate-200 bg-white/85 px-3 py-2 shadow-sm backdrop-blur dark:border-white/10 dark:bg-[#09090b]/85" aria-label="RouteDeck navigation">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200">
              <GitBranch className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">RouteDeck</div>
              <div className="truncate text-sm font-semibold text-slate-900 dark:text-white">
                {activeNode?.label || currentNode || 'Waiting for graph'}
              </div>
            </div>
          </div>

          <div className="flex min-w-0 flex-1 items-center justify-end gap-2 text-[11px] text-slate-500 dark:text-slate-400">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 dark:border-white/10 dark:bg-white/[0.04]">
              {graphManifest?.nodes.length ?? 0} nodes
            </span>
            <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200">
              {nextCount} next
            </span>
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200">
              {validActionCount} actions
            </span>
            {blockedCount > 0 && (
              <span className="rounded-full border border-red-200 bg-red-50 px-2.5 py-1 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
                {blockedCount} blocked
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={() => setMapOpen(true)}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-full border border-slate-200 bg-slate-950 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800 dark:border-white/10 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          >
            <Maximize2 className="h-3.5 w-3.5" />
            Map
          </button>
        </div>
      </section>

      {mapOpen && (
        <div className="fixed inset-0 z-50">
          <button
            type="button"
            className="absolute inset-0 bg-slate-950/30 backdrop-blur-[1px]"
            aria-label="Close RouteDeck map"
            onClick={() => setMapOpen(false)}
          />
          <aside className="absolute bottom-0 right-0 top-0 flex w-full max-w-[72rem] flex-col border-l border-slate-200 bg-white shadow-2xl dark:border-white/10 dark:bg-[#09090b]">
            <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-white/10">
              <div>
                <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">RouteDeck map</div>
                <div className="text-sm font-semibold text-slate-950 dark:text-white">
                  {activeNode?.label || currentNode || 'Graph navigation'}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setMapOpen(false)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900 dark:border-white/10 dark:text-slate-400 dark:hover:bg-white/[0.06] dark:hover:text-white"
                aria-label="Close RouteDeck map"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-4">
              <RouteDeckDebugger
                graphManifest={graphManifest}
                snapshot={routeDeckSnapshot}
                selectedNodeId={currentNode}
                onSelectedNodeChange={onSelectedDebugNodeChange}
                runId={runId}
                sessionId={sessionId}
                className="h-full"
              />
            </div>
          </aside>
        </div>
      )}
    </>
  )
}
