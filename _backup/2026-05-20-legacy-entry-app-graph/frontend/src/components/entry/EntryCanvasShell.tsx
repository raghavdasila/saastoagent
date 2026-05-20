import { PanelRightClose, PanelRightOpen, X } from 'lucide-react'

import { EntryArtifactRenderer } from '@/components/entry/EntryArtifactRenderer'
import type { EntryUIArtifact } from '@/types/entry'

export function EntryCanvasShell({
  artifact,
  collapsed,
  onToggleCollapsed,
  onClose,
}: {
  artifact?: EntryUIArtifact | null
  collapsed: boolean
  onToggleCollapsed: () => void
  onClose: () => void
}) {
  if (!artifact) return null

  return (
    <aside className={['hidden min-h-[34rem] min-w-0 lg:block', collapsed ? 'lg:w-14' : 'lg:w-full'].join(' ')}>
      <div className="sticky top-20 rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-white/10 dark:bg-[#09090b]">
        <div className={collapsed ? 'flex justify-center' : 'flex items-center justify-between gap-3'}>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-600 dark:text-sky-300">
                Canvas
              </p>
              <h2 className="truncate text-sm font-semibold text-slate-950 dark:text-white">{artifact.title || 'Artifact'}</h2>
            </div>
          )}
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-500 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
            title={collapsed ? 'Expand canvas' : 'Collapse canvas'}
            aria-label={collapsed ? 'Expand canvas' : 'Collapse canvas'}
          >
            {collapsed ? <PanelRightOpen className="h-4 w-4" /> : <PanelRightClose className="h-4 w-4" />}
          </button>
          {!collapsed && (
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-slate-200 text-slate-500 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
              title="Close canvas"
              aria-label="Close canvas"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        {!collapsed && (
          <div className="mt-3 max-h-[calc(100vh-9rem)] overflow-y-auto">
            <EntryArtifactRenderer artifact={artifact} />
          </div>
        )}
      </div>
    </aside>
  )
}
