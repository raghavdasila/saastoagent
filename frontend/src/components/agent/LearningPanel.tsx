import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, FlaskConical, X } from 'lucide-react'

import { api } from '@/lib/api'
import type { AgentLearningCandidate } from '@/types/agent'

interface LearningPanelProps {
  saasAgentId?: string | null
}

export function LearningPanel({ saasAgentId = null }: LearningPanelProps) {
  const agentApi = api.withSaaSAgent(saasAgentId)
  const queryClient = useQueryClient()
  const { data: candidates = [], isLoading } = useQuery({
    queryKey: ['agent-learnings', saasAgentId],
    queryFn: () => agentApi.get<AgentLearningCandidate[]>(`/saas-agents/${saasAgentId}/agent/learnings`),
    enabled: !!saasAgentId,
  })

  const review = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'approve' | 'reject' }) =>
      agentApi.post<AgentLearningCandidate>(`/saas-agents/${saasAgentId}/agent/learnings/${id}/${action}`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-learnings', saasAgentId] })
    },
  })

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 px-4 py-6 dark:bg-background sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Sandbox learning
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Review failed-execution learnings, missing-input hints, and owner policy proposals before they affect public automation.
          </p>
        </header>

        <section className="surface-card overflow-hidden rounded-lg">
          {isLoading ? (
            <p className="p-6 text-sm text-slate-500">Loading...</p>
          ) : candidates.length === 0 ? (
            <p className="p-6 text-sm text-slate-500">No learning candidates yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100 dark:divide-white/5">
              {candidates.map((candidate) => (
                <li key={candidate.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <FlaskConical className="mt-0.5 h-5 w-5 shrink-0 text-sky-500" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-sm font-semibold text-slate-950 dark:text-white">{candidate.title}</h2>
                        <span className="rounded-full border border-slate-200 px-2 py-0.5 text-[11px] uppercase tracking-wide text-slate-500 dark:border-white/10">
                          {candidate.status}
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{candidate.summary}</p>
                      <p className="mt-2 rounded-md bg-slate-50 p-2 text-xs leading-5 text-slate-600 dark:bg-white/[0.03] dark:text-slate-300">
                        {candidate.hint_text}
                      </p>
                      <div className="mt-2 text-xs text-slate-500">
                        {candidate.target_tool_name || 'Generated tool'} · {candidate.trigger_type} · {new Date(candidate.created_at).toLocaleString()}
                      </div>
                    </div>
                    {candidate.status === 'proposed' && (
                      <div className="flex shrink-0 gap-2">
                        <button
                          type="button"
                          onClick={() => review.mutate({ id: candidate.id, action: 'approve' })}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-emerald-200 text-emerald-700 transition hover:bg-emerald-50 dark:border-emerald-500/30 dark:text-emerald-300 dark:hover:bg-emerald-500/10"
                          title="Approve learning"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => review.mutate({ id: candidate.id, action: 'reject' })}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-red-200 text-red-700 transition hover:bg-red-50 dark:border-red-500/30 dark:text-red-300 dark:hover:bg-red-500/10"
                          title="Reject learning"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
