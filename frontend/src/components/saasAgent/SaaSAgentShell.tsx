/**
 * SaaSAgentShell
 *
 * Renders the full operator saasAgent UI (Header + ActivityBar + AgentCanvas)
 * while accepting `saasAgentId` as a prop instead of reading it from React
 * Router's useParams.  This lets OperatorGateway mount the saasAgent inline
 * when the graph reaches `operator_ready` — without any route navigation.
 *
 * The /agents/:saasAgentId deep-link route still uses SaaSAgentLayout (which relies
 * on useParams via SaaSAgentProvider's default behaviour) and that path is
 * unaffected by this component.
 */

import { Header } from '@/components/layout/Header'
import { ActivityBar } from '@/components/saasAgent/ActivityBar'
import { AgentCanvas } from '@/components/saasAgent/AgentCanvas'
import { SaaSAgentProvider } from '@/context/SaaSAgentContext'
import { api } from '@/lib/api'
import type { SaaSAgent, SaaSAgentStats } from '@/types/domain'
import { useQuery } from '@tanstack/react-query'

interface SaaSAgentShellProps {
  saasAgentId: string
}

function SaaSAgentContent({ saasAgentId }: SaaSAgentShellProps) {
  const { data: saasAgent } = useQuery({
    queryKey: ['saasAgent', saasAgentId],
    queryFn: () => api.get<SaaSAgent>(`/saas-agents/${saasAgentId}`),
    enabled: !!saasAgentId,
  })

  const { data: stats } = useQuery({
    queryKey: ['saasAgent-stats', saasAgentId],
    queryFn: () => api.get<SaaSAgentStats>(`/saas-agents/${saasAgentId}/stats`),
    enabled: !!saasAgentId,
  })

  return <AgentCanvas saasAgent={saasAgent} stats={stats} />
}

export function SaaSAgentShell({ saasAgentId }: SaaSAgentShellProps) {
  return (
    <SaaSAgentProvider saasAgentId={saasAgentId}>
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <div className="md:flex">
          <ActivityBar />
          <main className="min-w-0 flex-1">
            <SaaSAgentContent saasAgentId={saasAgentId} />
          </main>
        </div>
      </div>
    </SaaSAgentProvider>
  )
}
