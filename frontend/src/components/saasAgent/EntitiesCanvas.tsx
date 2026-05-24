import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { GitBranch, MessageSquareText } from 'lucide-react'

import { api } from '@/lib/api'
import { useSaaSAgentUiStore } from '@/stores/saasAgentUiStore'
import type { ActionCatalogRead, EntityRead } from '@/types/domain'

interface EntitiesCanvasProps {
  saasAgentId?: string | null
}

export function EntitiesCanvas({ saasAgentId = null }: EntitiesCanvasProps) {
  const agentApi = api.withSaaSAgent(saasAgentId)
  const selectedEntityId = useSaaSAgentUiStore((state) => state.selectedEntityId)
  const selectEntity = useSaaSAgentUiStore((state) => state.selectEntity)
  const setActiveView = useSaaSAgentUiStore((state) => state.setActiveView)

  const { data: catalog, isLoading } = useQuery({
    queryKey: ['saasAgent-catalog', saasAgentId],
    queryFn: () => agentApi.get<ActionCatalogRead>(`/saas-agents/${saasAgentId}/catalog`),
    enabled: !!saasAgentId,
  })

  const entities = catalog?.entities ?? []
  const selected = entities.find((entity) => entity.id === selectedEntityId) || entities[0] || null
  const relatedActions = useMemo(() => {
    if (!selected) return []
    return (catalog?.actions ?? []).filter((action) => {
      const tags = (action.tags || []).map((tag) => String(tag).toLowerCase())
      return tags.includes(selected.id.replace(/-/g, ' ').toLowerCase()) || action.path.toLowerCase().includes(`/${selected.id.split('-')[0]}`)
    })
  }, [catalog?.actions, selected])

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 px-4 py-6 dark:bg-background sm:px-6 lg:px-8" data-testid="entities-canvas">
      <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[22rem_1fr]">
        <section className="surface-card rounded-lg p-5">
          <div className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-sky-600" />
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-600">Entities</div>
              <h1 className="text-xl font-semibold text-slate-950 dark:text-white">API groups</h1>
            </div>
          </div>
          <div className="mt-5 space-y-2">
            {isLoading ? (
              <p className="text-sm text-slate-500">Loading entities...</p>
            ) : entities.length === 0 ? (
              <p className="text-sm leading-6 text-slate-500">Activate a REST API to infer lightweight entities from tags and paths.</p>
            ) : entities.map((entity) => (
              <EntityButton key={entity.id} entity={entity} active={selected?.id === entity.id} onSelect={() => selectEntity(entity.id)} />
            ))}
          </div>
        </section>

        <section className="surface-card rounded-lg p-5">
          {!selected ? (
            <div className="flex min-h-[20rem] items-center justify-center text-sm text-slate-500">No inferred entities yet.</div>
          ) : (
            <>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-600">Inferred entity</div>
                  <h2 className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">{selected.label}</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-400">{selected.description}</p>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <Metric label="Read" value={selected.read_count} />
                  <Metric label="Write" value={selected.write_count} />
                  <Metric label="Risky" value={selected.risky_count} />
                </div>
              </div>

              <div className="mt-6 grid gap-4 lg:grid-cols-2">
                <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
                  <h3 className="text-sm font-semibold text-slate-950 dark:text-white">Sample paths</h3>
                  <ul className="mt-3 space-y-2">
                    {selected.sample_paths.map((path) => (
                      <li key={path} className="rounded-md bg-slate-50 px-3 py-2 font-mono text-xs text-slate-600 dark:bg-white/[0.04] dark:text-slate-300">{path}</li>
                    ))}
                  </ul>
                </section>
                <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
                  <h3 className="text-sm font-semibold text-slate-950 dark:text-white">Operator prompt</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-400">Ask Corpus to work with this entity. For read actions, it can attempt execution directly when required parameters are available.</p>
                  <button type="button" className="surface-solid-button mt-3 inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm" onClick={() => setActiveView('chat')}>
                    Open chat
                    <MessageSquareText className="h-4 w-4" />
                  </button>
                </section>
              </div>

              <section className="mt-4 rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
                <h3 className="text-sm font-semibold text-slate-950 dark:text-white">Related actions</h3>
                <div className="mt-3 divide-y divide-slate-100 rounded-md border border-slate-100 dark:divide-white/5 dark:border-white/10">
                  {relatedActions.length === 0 ? (
                    <p className="p-3 text-sm text-slate-500">No direct action match was found for this entity label.</p>
                  ) : relatedActions.map((action) => (
                    <div key={action.id} className="p-3">
                      <div className="text-sm font-medium text-slate-900 dark:text-white">{action.name}</div>
                      <div className="mt-1 font-mono text-xs text-slate-500">{action.method} {action.path}</div>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
        </section>
      </div>
    </div>
  )
}

function EntityButton({ entity, active, onSelect }: { entity: EntityRead; active: boolean; onSelect: () => void }) {
  return (
    <button type="button" onClick={onSelect} className={['block w-full rounded-md border p-3 text-left', active ? 'border-sky-300 bg-sky-50 dark:border-sky-500/30 dark:bg-sky-500/10' : 'border-slate-200 bg-white hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.03] dark:hover:bg-white/[0.06]'].join(' ')}>
      <div className="text-sm font-medium text-slate-950 dark:text-white">{entity.label}</div>
      <div className="mt-1 text-xs text-slate-500">{entity.action_count} actions</div>
    </button>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md bg-slate-100 px-3 py-2 dark:bg-white/[0.06]">
      <div className="text-lg font-semibold text-slate-950 dark:text-white">{value}</div>
      <div className="text-slate-500">{label}</div>
    </div>
  )
}
