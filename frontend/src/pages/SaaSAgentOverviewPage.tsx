import { useQuery } from '@tanstack/react-query'

import { AgentCanvas } from '@/components/saasAgent/AgentCanvas'
import { useSaaSAgent } from '@/context/SaaSAgentContext'
import { api } from '@/lib/api'
import type { SaaSAgent, SaaSAgentStats } from '@/types/domain'

export function SaaSAgentOverviewPage() {
  const { saasAgentId } = useSaaSAgent()

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
