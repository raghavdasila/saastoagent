import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouteDeckStore } from '@routedeck/react'
import { Check, ExternalLink, FlaskConical, X } from 'lucide-react'

import { api } from '@/lib/api'
import type { AgentLearningCandidate } from '@/types/agent'
import { corpusOperationIds } from '@/components/appGraph/corpusRouteDeckCatalog'

interface LearningPanelProps {
  saasAgentId?: string | null
  filter?: string
  candidateId?: string | null
  readonly?: boolean
}

export function LearningPanel({
  saasAgentId = null,
  filter = 'policy_gaps',
  candidateId = null,
  readonly = false,
}: LearningPanelProps) {
  const agentApi = api.withSaaSAgent(saasAgentId)
  const queryClient = useQueryClient()
  const routeDeckStore = useRouteDeckStore()
  const { data: candidates = [], isLoading } = useQuery({
    queryKey: ['agent-learnings', saasAgentId],
    queryFn: () => agentApi.get<AgentLearningCandidate[]>(`/saas-agents/${saasAgentId}/agent/learnings`),
    enabled: !!saasAgentId,
    staleTime: 0,
    refetchOnWindowFocus: true,
    refetchInterval: candidateId ? false : 2_000,
  })

  const review = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'approve' | 'reject' }) =>
      action === 'approve'
        ? agentApi.post<AgentLearningCandidate>(`/saas-agents/${saasAgentId}/agent/learnings/${id}/approve`)
        : agentApi.post<AgentLearningCandidate>(`/saas-agents/${saasAgentId}/agent/learnings/${id}/reject`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-learnings', saasAgentId] })
    },
  })

  const selectedCandidate = candidateId ? candidates.find((candidate) => candidate.id === candidateId) : null
  const visibleCandidates = candidateId
    ? (selectedCandidate ? [selectedCandidate] : [])
    : candidates.filter((candidate) => candidateMatchesFilter(candidate, filter))

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 px-4 py-6 dark:bg-background sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            {candidateId ? 'Learning review' : 'Sandbox learning'}
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            {candidateId
              ? 'Review policy evidence before it affects visitor automation.'
              : 'Review policy proposals separately from failed executions and active policies.'}
          </p>
        </header>

        {!candidateId && (
          <div className="mb-4 flex flex-wrap gap-2">
            {[
              ['policy_gaps', 'Policy gaps'],
              ['failed_executions', 'Failed executions'],
              ['active_policies', 'Active policies'],
              ['rejected', 'Rejected'],
            ].map(([id, label]) => (
              <button
                key={id}
                type="button"
                onClick={() => {
                  queryClient.invalidateQueries({ queryKey: ['agent-learnings', saasAgentId] })
                  void routeDeckStore.switchSurface(`learning.${id}`)
                }}
                className={[
                  'rounded-md border px-3 py-1.5 text-sm font-medium transition',
                  filter === id
                    ? 'border-sky-300 bg-sky-50 text-sky-800 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-200'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-300',
                ].join(' ')}
              >
                {label}
              </button>
            ))}
          </div>
        )}

        <section className="surface-card overflow-hidden rounded-lg">
          {isLoading ? (
            <p className="p-6 text-sm text-slate-500">Loading...</p>
          ) : visibleCandidates.length === 0 ? (
            <p className="p-6 text-sm text-slate-500">No learning candidates yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100 dark:divide-white/5">
              {visibleCandidates.map((candidate) => (
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
                        {candidate.target_tool_name || 'Generated tool'} - {candidate.trigger_type} - {new Date(candidate.created_at).toLocaleString()}
                      </div>
                      {candidate.trigger_type === 'domain_policy_gap' && <PolicyEvidence candidate={candidate} />}
                    </div>
                    <div className="flex shrink-0 gap-2">
                      {!candidateId && (
                        <button
                          type="button"
                          onClick={() =>
                            void routeDeckStore.dispatch({
                              operation_id:
                                ['approved', 'active'].includes(candidate.status)
                                  ? corpusOperationIds.learningActivePolicyOpen
                                  : corpusOperationIds.learningPolicyCandidateOpen,
                              args: { candidate_id: candidate.id },
                            })
                          }
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 text-slate-600 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/[0.05]"
                          title="Open review"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </button>
                      )}
                      {candidate.status === 'proposed' && !readonly && (
                        <>
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
                        </>
                      )}
                    </div>
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

function candidateMatchesFilter(candidate: AgentLearningCandidate, filter: string) {
  if (filter === 'policy_gaps') return candidate.trigger_type === 'domain_policy_gap' && candidate.status === 'proposed'
  if (filter === 'failed_executions') return candidate.trigger_type === 'failed_execution'
  if (filter === 'active_policies') return candidate.trigger_type === 'domain_policy_gap' && ['approved', 'active'].includes(candidate.status)
  if (filter === 'rejected') return candidate.status === 'rejected'
  return true
}

function PolicyEvidence({ candidate }: { candidate: AgentLearningCandidate }) {
  const evidence = candidate.evidence || {}
  const allowed = Array.isArray(evidence.allowed_action_paths) ? evidence.allowed_action_paths.map(String) : []
  const missing = Array.isArray(evidence.missing_internal_inputs) ? evidence.missing_internal_inputs.map(String) : []
  return (
    <dl className="mt-3 grid gap-2 rounded-md border border-slate-200 bg-white p-3 text-xs dark:border-white/10 dark:bg-white/[0.03] sm:grid-cols-2">
      <EvidenceItem label="Target action" value={candidate.target_action_path || 'Generated action'} />
      <EvidenceItem label="Risk" value={candidate.target_risk_level || 'Unclassified'} />
      <EvidenceItem label="Allowed chain" value={allowed.length ? allowed.join(' -> ') : 'Not provided'} />
      <EvidenceItem label="Internal dependency" value={missing.length ? missing.join(', ') : 'None recorded'} />
      <EvidenceItem label="Public channel" value={evidence.public_channel === true ? 'Yes' : 'No'} />
      <EvidenceItem label="Source session" value={String(evidence.session_id || 'Not recorded')} />
    </dl>
  )
}

function EvidenceItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="font-medium text-slate-500 dark:text-slate-400">{label}</dt>
      <dd className="mt-1 break-words font-mono text-[11px] text-slate-700 dark:text-slate-200">{value}</dd>
    </div>
  )
}
