import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FileText, MessageSquare, Plus, Shield, Sparkles, Trash2, Users } from 'lucide-react'

import { api } from '@/lib/api'
import type {
  AgentAdminStats,
  AgentDocument,
  AgentDocumentChunk,
  AgentMemoryRow,
  AgentMessageRow,
  AgentSession,
} from '@/types/agent'
import type { SaaSAgent } from '@/types/domain'

interface AdminPanelProps {
  saasAgent?: SaaSAgent
  saasAgentId?: string | null
}

type Tab = 'sessions' | 'documents' | 'memories'

export function AdminPanel({ saasAgent, saasAgentId: saasAgentIdProp }: AdminPanelProps) {
  const saasAgentId = saasAgentIdProp || saasAgent?.id || null
  const agentApi = api.withSaaSAgent(saasAgentId)
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<Tab>('sessions')
  const [openSessionId, setOpenSessionId] = useState<string | null>(null)
  const [openDocumentId, setOpenDocumentId] = useState<string | null>(null)
  const [memoryContent, setMemoryContent] = useState('')
  const [memoryCategory, setMemoryCategory] = useState<'fact' | 'preference' | 'instruction'>('fact')
  const role = saasAgent?.role
  const isAdmin = role === 'owner' || role === 'admin'

  const { data: stats } = useQuery({
    queryKey: ['agent-admin-stats', saasAgentId],
    queryFn: () =>
      agentApi.get<AgentAdminStats>(`/saas-agents/${saasAgentId}/agent/admin/stats`),
    enabled: !!saasAgentId && isAdmin,
  })

  const { data: sessionsData } = useQuery({
    queryKey: ['agent-sessions', saasAgentId],
    queryFn: () =>
      agentApi.get<{ sessions: AgentSession[]; total: number }>(
        `/saas-agents/${saasAgentId}/agent/sessions`,
      ),
    enabled: !!saasAgentId && isAdmin && tab === 'sessions',
  })

  const { data: documents } = useQuery({
    queryKey: ['agent-documents', saasAgentId],
    queryFn: () =>
      agentApi.get<AgentDocument[]>(`/saas-agents/${saasAgentId}/agent/documents`),
    enabled: !!saasAgentId && isAdmin && tab === 'documents',
  })

  const { data: memories } = useQuery({
    queryKey: ['agent-memories', saasAgentId],
    queryFn: () =>
      agentApi.get<AgentMemoryRow[]>(`/saas-agents/${saasAgentId}/agent/memories`),
    enabled: !!saasAgentId && isAdmin && tab === 'memories',
  })

  const { data: openMessages } = useQuery({
    queryKey: ['agent-session-messages', saasAgentId, openSessionId],
    queryFn: () =>
      agentApi.get<AgentMessageRow[]>(
        `/saas-agents/${saasAgentId}/agent/sessions/${openSessionId}/messages`,
      ),
    enabled: !!saasAgentId && !!openSessionId,
  })

  const { data: openChunks } = useQuery({
    queryKey: ['agent-document-chunks', saasAgentId, openDocumentId],
    queryFn: () =>
      agentApi.get<AgentDocumentChunk[]>(
        `/saas-agents/${saasAgentId}/agent/admin/documents/${openDocumentId}/chunks`,
      ),
    enabled: !!saasAgentId && !!openDocumentId,
  })

  const deleteSession = useMutation({
    mutationFn: (sid: string) =>
      agentApi.delete<{ status: string }>(
        `/saas-agents/${saasAgentId}/agent/admin/sessions/${sid}`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-sessions', saasAgentId] })
      queryClient.invalidateQueries({ queryKey: ['agent-admin-stats', saasAgentId] })
      setOpenSessionId(null)
    },
  })

  const deleteMemory = useMutation({
    mutationFn: (mid: string) =>
      agentApi.delete<{ status: string }>(`/saas-agents/${saasAgentId}/agent/memories/${mid}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-memories', saasAgentId] })
      queryClient.invalidateQueries({ queryKey: ['agent-admin-stats', saasAgentId] })
    },
  })

  const createMemory = useMutation({
    mutationFn: () =>
      agentApi.post<AgentMemoryRow>(`/saas-agents/${saasAgentId}/agent/memories`, {
        content: memoryContent,
        category: memoryCategory,
      }),
    onSuccess: () => {
      setMemoryContent('')
      queryClient.invalidateQueries({ queryKey: ['agent-memories', saasAgentId] })
      queryClient.invalidateQueries({ queryKey: ['agent-admin-stats', saasAgentId] })
    },
  })

  if (!isAdmin) {
    return (
      <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center bg-slate-50 px-6 dark:bg-background">
        <div className="surface-card max-w-md rounded-lg p-8 text-center">
          <Shield className="mx-auto h-10 w-10 text-slate-400" />
          <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-white">
            Admin access required
          </h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Only saasAgent owners and admins can view this dashboard. Your role: {role || 'member'}.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 px-4 py-6 dark:bg-background sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            SaaSAgent admin
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Inspect agent activity, documents, and persistent memory in this saasAgent.
          </p>
        </header>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Sessions" icon={MessageSquare} value={stats?.total_sessions ?? '—'} />
          <StatCard label="Messages" icon={Users} value={stats?.total_messages ?? '—'} />
          <StatCard label="Documents" icon={FileText} value={stats?.total_documents ?? '—'} />
          <StatCard label="Memories" icon={Sparkles} value={stats?.total_memories ?? '—'} />
        </div>

        <div className="mt-6 flex gap-1 border-b border-slate-200 dark:border-white/10">
          {(['sessions', 'documents', 'memories'] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={[
                'px-4 py-2 text-sm font-medium capitalize transition',
                tab === t
                  ? 'border-b-2 border-sky-500 text-slate-900 dark:text-white'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white',
              ].join(' ')}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="mt-4">
          {tab === 'sessions' && (
            <div className="surface-card overflow-hidden rounded-lg">
              {!sessionsData?.sessions?.length ? (
                <p className="p-6 text-sm text-slate-500">No sessions yet.</p>
              ) : (
                <ul className="divide-y divide-slate-100 dark:divide-white/5">
                  {sessionsData.sessions.map((s) => (
                    <li key={s.id} className="p-4">
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => setOpenSessionId(openSessionId === s.id ? null : s.id)}
                          className="flex-1 text-left"
                        >
                          <div className="text-sm font-medium text-slate-900 dark:text-white">
                            {s.title || 'Untitled session'}
                          </div>
                          <div className="text-xs text-slate-500">
                            {s.message_count} messages · {new Date(s.created_at).toLocaleString()}
                          </div>
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            if (confirm('Delete this session and all its messages?')) {
                              deleteSession.mutate(s.id)
                            }
                          }}
                          className="rounded-md p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                      {openSessionId === s.id && (
                        <div className="mt-3 max-h-72 space-y-2 overflow-y-auto rounded border border-slate-200 bg-slate-50 p-3 text-xs dark:border-white/10 dark:bg-white/[0.02]">
                          {openMessages?.length ? (
                            openMessages.map((m) => (
                              <div key={m.id}>
                                <span className="font-semibold text-slate-700 dark:text-slate-300">
                                  {m.role}:
                                </span>{' '}
                                <span className="whitespace-pre-wrap text-slate-600 dark:text-slate-400">
                                  {m.content}
                                </span>
                              </div>
                            ))
                          ) : (
                            <p className="text-slate-500">Loading…</p>
                          )}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {tab === 'documents' && (
            <div className="surface-card overflow-hidden rounded-lg">
              {!documents?.length ? (
                <p className="p-6 text-sm text-slate-500">No documents yet.</p>
              ) : (
                <ul className="divide-y divide-slate-100 dark:divide-white/5">
                  {documents.map((d) => (
                    <li key={d.id} className="p-4">
                      <button
                        type="button"
                        onClick={() =>
                          setOpenDocumentId(openDocumentId === d.id ? null : d.id)
                        }
                        className="flex w-full items-center gap-3 text-left"
                      >
                        <FileText className="h-5 w-5 text-slate-400" />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-medium text-slate-900 dark:text-white">
                            {d.original_name}
                          </div>
                          <div className="text-xs text-slate-500">
                            {d.chunk_count} chunks · {(d.size_bytes / 1024).toFixed(1)} KB ·{' '}
                            {new Date(d.created_at).toLocaleString()}
                          </div>
                        </div>
                      </button>
                      {openDocumentId === d.id && (
                        <div className="mt-3 max-h-72 space-y-2 overflow-y-auto rounded border border-slate-200 bg-slate-50 p-3 text-xs dark:border-white/10 dark:bg-white/[0.02]">
                          {openChunks?.length ? (
                            openChunks.map((chunk) => (
                              <div key={chunk.id} className="rounded border border-slate-200 bg-white p-2 dark:border-white/10 dark:bg-black/20">
                                <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                                  Chunk {chunk.chunk_index + 1} · {chunk.has_embedding ? 'embedded' : 'no embedding'}
                                </div>
                                <div className="whitespace-pre-wrap text-slate-600 dark:text-slate-400">
                                  {chunk.content}
                                </div>
                              </div>
                            ))
                          ) : (
                            <p className="text-slate-500">Loading…</p>
                          )}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {tab === 'memories' && (
            <div className="space-y-3">
              <form
                className="surface-card rounded-lg p-4"
                onSubmit={(event) => {
                  event.preventDefault()
                  if (memoryContent.trim()) createMemory.mutate()
                }}
              >
                <div className="text-sm font-semibold text-slate-900 dark:text-white">Save memory</div>
                <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_10rem_auto]">
                  <input
                    value={memoryContent}
                    onChange={(event) => setMemoryContent(event.target.value)}
                    placeholder="Fact, preference, or instruction this SaaS Agent should remember"
                    className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 dark:border-white/10 dark:bg-black/20 dark:text-white"
                  />
                  <select
                    value={memoryCategory}
                    onChange={(event) => setMemoryCategory(event.target.value as 'fact' | 'preference' | 'instruction')}
                    className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 dark:border-white/10 dark:bg-black/20 dark:text-white"
                  >
                    <option value="fact">Fact</option>
                    <option value="preference">Preference</option>
                    <option value="instruction">Instruction</option>
                  </select>
                  <button
                    type="submit"
                    disabled={!memoryContent.trim() || createMemory.isPending}
                    className="inline-flex items-center justify-center gap-2 rounded-md bg-slate-950 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
                  >
                    <Plus className="h-4 w-4" />
                    Save
                  </button>
                </div>
              </form>
              <div className="surface-card overflow-hidden rounded-lg">
              {!memories?.length ? (
                <p className="p-6 text-sm text-slate-500">No memories saved yet.</p>
              ) : (
                <ul className="divide-y divide-slate-100 dark:divide-white/5">
                  {memories.map((m) => (
                    <li key={m.id} className="flex items-start gap-3 p-4">
                      <Sparkles className="mt-0.5 h-4 w-4 text-amber-500" />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm text-slate-900 dark:text-white">{m.content}</div>
                        <div className="mt-1 text-xs text-slate-500">
                          {m.category} · {new Date(m.created_at).toLocaleString()}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          if (confirm('Delete this memory?')) {
                            deleteMemory.mutate(m.id)
                          }
                        }}
                        className="rounded-md p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  label,
  icon: Icon,
  value,
}: {
  label: string
  icon: typeof Shield
  value: number | string
}) {
  return (
    <div className="surface-card rounded-lg p-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-slate-500">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">{value}</div>
    </div>
  )
}
