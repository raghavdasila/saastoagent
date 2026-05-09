import { PanelRightOpen } from 'lucide-react'

import type { EntryUIArtifact } from '@/types/entry'

export function EntryCanvasLauncher({
  artifacts,
  activeArtifactId,
  onOpen,
}: {
  artifacts: EntryUIArtifact[]
  activeArtifactId?: string | null
  onOpen: (artifactId: string) => void
}) {
  if (artifacts.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2 px-4 pb-2 pt-1 sm:px-6">
      {artifacts.map((artifact) => {
        const active = artifact.id === activeArtifactId
        return (
          <button
            key={artifact.id}
            type="button"
            onClick={() => onOpen(artifact.id)}
            title={`Open ${artifact.title || 'artifact'} in canvas`}
            className={[
              'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors',
              active
                ? 'border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-300'
                : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:border-sky-500/40 dark:hover:bg-sky-500/10 dark:hover:text-sky-300',
            ].join(' ')}
          >
            <PanelRightOpen className="h-3.5 w-3.5" aria-hidden="true" />
            <span>{artifact.title || 'Open canvas'}</span>
          </button>
        )
      })}
    </div>
  )
}
