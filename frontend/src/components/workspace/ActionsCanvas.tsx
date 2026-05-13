import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bot, Filter, MessageSquareText, ShieldAlert } from 'lucide-react'

import { api } from '@/lib/api'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import type { ActionCatalogRead, ActionNodeRead, GeneratedToolRead } from '@/types/domain'

type RiskFilter = 'all' | 'read' | 'approval'

export function ActionsCanvas() {
  const workspaceId = useWorkspaceStore((state) => state.workspaceId)
  const setActiveView = useWorkspaceStore((state) => state.setActiveView)
  const selectedActionNodeId = useWorkspaceStore((state) => state.selectedActionNodeId)
  const selectActionNode = useWorkspaceStore((state) => state.selectActionNode)
  const [query, setQuery] = useState('')
  const [risk, setRisk] = useState<RiskFilter>('all')

  const { data: catalog, isLoading } = useQuery({
    queryKey: ['workspace-catalog', workspaceId],
    queryFn: () => api.get<ActionCatalogRead>(`/workspaces/${workspaceId}/catalog`),
    enabled: !!workspaceId,
  })

  const toolsByAction = useMemo(() => {
    const map = new Map<string, GeneratedToolRead>()
    for (const tool of catalog?.tools ?? []) map.set(tool.action_node_id, tool)
    return map
  }, [catalog?.tools])

  const actions = useMemo(() => {
    const raw = catalog?.actions ?? []
    const normalizedQuery = query.trim().toLowerCase()
    return raw.filter((action) => {
      const tool = toolsByAction.get(action.id)
      const matchesQuery = !normalizedQuery || [action.name, action.path, action.description, tool?.name].join(' ').toLowerCase().includes(normalizedQuery)
      const matchesRisk = risk === 'all' || (risk === 'read' ? action.risk_level === 'read' : action.risk_level !== 'read')
      return matchesQuery && matchesRisk
    })
  }, [catalog?.actions, query, risk, toolsByAction])

  const selected = actions.find((action) => action.id === selectedActionNodeId) || actions[0] || null
  const selectedTool = selected ? toolsByAction.get(selected.id) : null

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 px-4 py-6 dark:bg-background sm:px-6 lg:px-8" data-testid="actions-canvas">
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[minmax(20rem,0.85fr)_minmax(0,1.15fr)]">
        <section className="surface-card rounded-lg p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-600">Action catalog</div>
              <h1 className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">Generated REST actions</h1>
            </div>
            <Bot className="h-6 w-6 text-sky-600" />
          </div>

          <div className="mt-5 grid gap-2">
            <input
              className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/[0.04]"
              placeholder="Search actions, paths, tools"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <div className="flex flex-wrap gap-2">
              {(['all', 'read', 'approval'] as RiskFilter[]).map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setRisk(option)}
                  className={[
                    'inline-flex items-center gap-1 rounded-full border px-3 py-1.5 text-xs font-medium',
                    risk === option ? 'border-slate-900 bg-slate-950 text-white dark:border-white dark:bg-white dark:text-slate-950' : 'border-slate-200 text-slate-600 dark:border-white/10 dark:text-slate-300',
                  ].join(' ')}
                >
                  <Filter className="h-3 w-3" />
                  {option === 'approval' ? 'Needs approval' : option}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-5 max-h-[34rem] overflow-y-auto rounded-md border border-slate-200 dark:border-white/10">
            {isLoading ? (
              <p className="p-4 text-sm text-slate-500">Loading actions...</p>
            ) : actions.length === 0 ? (
              <p className="p-4 text-sm text-slate-500">No generated actions match this filter.</p>
            ) : actions.map((action) => (
              <ActionRow
                key={action.id}
                action={action}
                active={selected?.id === action.id}
                tool={toolsByAction.get(action.id)}
                onSelect={() => selectActionNode(action.id)}
              />
            ))}
          </div>
        </section>

        <section className="surface-card rounded-lg p-5">
          {!selected ? (
            <div className="flex min-h-[20rem] items-center justify-center text-sm text-slate-500">Activate an API to inspect generated actions.</div>
          ) : (
            <div>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-600">{selected.method} {selected.path}</div>
                  <h2 className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">{selected.name}</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-400">{selected.description || 'No OpenAPI description was provided.'}</p>
                </div>
                <RiskBadge risk={selected.risk_level} />
              </div>

              <div className="mt-6 grid gap-4 lg:grid-cols-2">
                <DetailBlock title="Generated tool">
                  {selectedTool ? (
                    <>
                      <div className="font-mono text-sm text-slate-900 dark:text-white">{selectedTool.name}</div>
                      <div className="mt-2 text-xs text-slate-500">{selectedTool.requires_approval ? 'Approval required' : 'Read-safe auto execution allowed'}</div>
                    </>
                  ) : <p className="text-sm text-slate-500">No generated tool found for this action.</p>}
                </DetailBlock>
                <DetailBlock title="Try in chat">
                  <p className="text-sm leading-6 text-slate-600 dark:text-slate-400">Ask Corpus to use this API action. Include required path or query values as `name=value` when needed.</p>
                  <button type="button" onClick={() => setActiveView('chat')} className="surface-solid-button mt-3 inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm">
                    Open chat
                    <MessageSquareText className="h-4 w-4" />
                  </button>
                </DetailBlock>
              </div>

              <DetailBlock title="Function schema" className="mt-4">
                <pre className="max-h-96 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">
                  {JSON.stringify(selectedTool?.function_schema || {}, null, 2)}
                </pre>
              </DetailBlock>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function ActionRow({ action, active, tool, onSelect }: { action: ActionNodeRead; active: boolean; tool?: GeneratedToolRead; onSelect: () => void }) {
  return (
    <button type="button" onClick={onSelect} className={['block w-full border-b border-slate-100 p-3 text-left last:border-0 dark:border-white/5', active ? 'bg-sky-50 dark:bg-sky-500/10' : 'hover:bg-slate-50 dark:hover:bg-white/[0.04]'].join(' ')}>
      <div className="flex items-center justify-between gap-3">
        <span className="truncate text-sm font-medium text-slate-900 dark:text-white">{action.name}</span>
        <RiskBadge risk={action.risk_level} compact />
      </div>
      <div className="mt-1 truncate font-mono text-xs text-slate-500">{action.method} {action.path}</div>
      {tool && <div className="mt-1 truncate text-xs text-slate-400">{tool.name}</div>}
    </button>
  )
}

function RiskBadge({ risk, compact = false }: { risk: string; compact?: boolean }) {
  const approval = risk !== 'read'
  return (
    <span className={['inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold uppercase', approval ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/10 dark:text-amber-200' : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-200', compact ? 'text-[10px]' : ''].join(' ')}>
      {approval && <ShieldAlert className="h-3 w-3" />}
      {risk}
    </span>
  )
}

function DetailBlock({ title, children, className = '' }: { title: string; children: ReactNode; className?: string }) {
  return (
    <section className={['rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]', className].join(' ')}>
      <h3 className="text-sm font-semibold text-slate-950 dark:text-white">{title}</h3>
      <div className="mt-3">{children}</div>
    </section>
  )
}
