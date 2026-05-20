import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { SaaSAgentLaunchPad } from '@/components/saasAgent/SaaSAgentLaunchPad'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { formatSaaSAgentDisplayName, PRODUCT_NAME } from '@/lib/entryGraph'
import { useSaaSAgentStore } from '@/stores/saasAgentStore'
import type { SaaSAgent } from '@/types/domain'

const medusaPresets = [
  {
    name: 'Medusa Storefront Agent',
    slug: 'medusa-storefront-agent',
    description: 'Customer-facing Store API agent. Activate this before Admin.',
  },
  {
    name: 'Medusa Admin Agent',
    slug: 'medusa-admin-agent',
    description: 'Back-office Admin API agent. Keep admin auth separate from Storefront.',
  },
]

function SaaSAgentListItem({
  saasAgent,
  isCurrent,
  onOpen,
}: {
  saasAgent: SaaSAgent
  isCurrent: boolean
  onOpen: () => void
}) {
  return (
    <button
      className={[
        'surface-card flex w-full items-center justify-between rounded-3xl px-5 py-5 text-left transition',
        isCurrent
          ? 'border-sky-400 shadow-[0_0_0_1px_rgba(56,189,248,0.35)] dark:border-sky-500/40'
          : 'hover:border-slate-300 dark:hover:border-white/15',
      ].join(' ')}
      onClick={onOpen}
      type="button"
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <div className="truncate text-base font-semibold text-slate-950 dark:text-white">{formatSaaSAgentDisplayName(saasAgent.name) || saasAgent.name}</div>
          {isCurrent && (
            <span className="rounded-full bg-sky-100 px-2 py-0.5 text-[11px] font-medium text-sky-700 dark:bg-sky-500/10 dark:text-sky-300">
              Current
            </span>
          )}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <span>/{saasAgent.slug}</span>
          <span className="h-1 w-1 rounded-full bg-slate-300 dark:bg-slate-600" />
          <span className="capitalize">{saasAgent.role || 'member'}</span>
        </div>
      </div>
      <ArrowRight className="h-4 w-4 shrink-0 text-slate-400 dark:text-slate-500" aria-hidden="true" />
    </button>
  )
}

export function DashboardPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const currentSaaSAgentId = useSaaSAgentStore((state) => state.saasAgentId)
  const setSaaSAgentId = useSaaSAgentStore((state) => state.setSaaSAgentId)
  const [error, setError] = useState('')

  const { data: saasAgents, isLoading } = useQuery({
    queryKey: ['saasAgents'],
    queryFn: () => api.get<SaaSAgent[]>('/saas-agents'),
  })

  useEffect(() => {
    if (isLoading || !saasAgents) {
      return
    }

    if (saasAgents.length === 1) {
      setSaaSAgentId(saasAgents[0].id)
      navigate(`/agents/${saasAgents[0].id}`, { replace: true })
    }
  }, [isLoading, navigate, setSaaSAgentId, saasAgents])

  const createSaaSAgent = useMutation({
    mutationFn: (body: { name: string; slug: string }) => api.post<SaaSAgent>('/saas-agents', body),
    onSuccess: async (saasAgent) => {
      await queryClient.invalidateQueries({ queryKey: ['saasAgents'] })
      setError('')
      setSaaSAgentId(saasAgent.id)
      navigate(`/agents/${saasAgent.id}`)
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create SaaS Agent')
    },
  })

  const saasAgentsList = saasAgents || []
  const primarySaaSAgent = useMemo(() => {
    if (saasAgentsList.length === 0) {
      return null
    }

    return saasAgentsList.find((saasAgent) => saasAgent.id === currentSaaSAgentId) || saasAgentsList[0]
  }, [currentSaaSAgentId, saasAgentsList])

  return (
    <div className="grid gap-6 xl:grid-cols-[22rem_1fr]">
      <aside className="space-y-6">
        <section className="surface-card rounded-3xl p-6 sm:p-8">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">SaaS Agent navigation</div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            {saasAgentsList.length === 0 ? 'Launch your first SaaS Agent' : PRODUCT_NAME}
          </h1>
          <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-400">
            {saasAgentsList.length === 0
              ? 'Start by naming a SaaS Agent. API schema connections are configured after the SaaS Agent exists.'
              : primarySaaSAgent
                ? `Current SaaS Agent: ${formatSaaSAgentDisplayName(primarySaaSAgent.name) || primarySaaSAgent.name}. Pick a SaaS Agent from the list or launch another one here.`
                : 'Pick a SaaS Agent from the list or launch another one here.'}
          </p>

          {primarySaaSAgent && (
            <button
              className="surface-solid-button mt-6 inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium"
              onClick={() => navigate(`/agents/${primarySaaSAgent.id}`)}
              type="button"
            >
              Open current SaaS Agent
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </section>

        <SaaSAgentLaunchPad
          title={saasAgentsList.length === 0 ? 'Launch a SaaS Agent' : 'Launch another SaaS Agent'}
          description={
            saasAgentsList.length === 0
              ? 'Name the first SaaS Agent, then add API schema connections from the SaaS Agent.'
              : 'Name the new SaaS Agent, then configure its API schema connections.'
          }
          error={error}
          isPending={createSaaSAgent.isPending}
          presets={medusaPresets}
          onCreate={(body) => createSaaSAgent.mutate(body)}
        />
      </aside>

      <section className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">SaaS Agent list</div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
              {user?.display_name ? `${user.display_name}'s SaaS Agents` : 'SaaS Agents'}
            </h2>
          </div>

          {!isLoading && saasAgentsList.length > 0 && (
            <div className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600 dark:bg-white/[0.06] dark:text-slate-400">
              {saasAgentsList.length} SaaS Agent{saasAgentsList.length === 1 ? '' : 's'}
            </div>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((item) => (
              <div key={item} className="surface-card h-24 rounded-3xl animate-pulse" />
            ))}
          </div>
        ) : saasAgentsList.length > 0 ? (
          <div className="space-y-3">
            {saasAgentsList.map((saasAgent) => (
              <SaaSAgentListItem
                key={saasAgent.id}
                saasAgent={saasAgent}
                isCurrent={saasAgent.id === primarySaaSAgent?.id}
                onOpen={() => {
                  setSaaSAgentId(saasAgent.id)
                  navigate(`/agents/${saasAgent.id}`)
                }}
              />
            ))}
          </div>
        ) : (
          <section className="surface-card rounded-3xl p-6 sm:p-8">
            <div className="text-sm font-semibold text-slate-950 dark:text-white">No SaaS Agents launched yet</div>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
              Once you create a SaaS Agent, it will appear here with its slug and access role.
            </p>
          </section>
        )}
      </section>
    </div>
  )
}
