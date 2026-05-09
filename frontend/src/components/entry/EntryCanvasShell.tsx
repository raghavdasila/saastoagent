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
    <aside className={['hidden min-h-[34rem] min-w-0 lg:block', collapsed ? 'lg:w-12' : 'lg:w-full'].join(' ')}>
      <div className="sticky top-20 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm dark:border-white/10 dark:bg-[#09090b]">
        <div className="flex items-center justify-between gap-3">
          {!collapsed && (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-600 dark:text-sky-300">
                Canvas
              </p>
              <h2 className="text-sm font-semibold text-slate-950 dark:text-white">{artifact.title || 'Artifact'}</h2>
            </div>
          )}
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
          >
            {collapsed ? 'Expand' : 'Collapse'}
          </button>
          {!collapsed && (
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
            >
              Close
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
