import { AdminPanel } from '@/components/agent/AdminPanel'
import { AgentChat } from '@/components/agent/AgentChat'
import { AttachmentsPanel } from '@/components/agent/AttachmentsPanel'
import { ActionsCanvas } from '@/components/saasAgent/ActionsCanvas'
import { ConnectSetupView } from '@/components/saasAgent/ConnectSetupView'
import { EntitiesCanvas } from '@/components/saasAgent/EntitiesCanvas'
import { LockedCanvasView } from '@/components/saasAgent/LockedCanvasView'
import { useSaaSAgentUiStore } from '@/stores/saasAgentUiStore'
import type { SaaSAgent, SaaSAgentStats } from '@/types/domain'

interface AgentCanvasProps {
  saasAgent?: SaaSAgent
  stats?: SaaSAgentStats
}

export function AgentCanvas({ saasAgent, stats }: AgentCanvasProps) {
  const activeView = useSaaSAgentUiStore((state) => state.activeView)
  const saasAgentId = saasAgent?.id || null

  if (activeView === 'connect') {
    return <ConnectSetupView saasAgent={saasAgent} stats={stats} saasAgentId={saasAgentId} />
  }

  if (activeView === 'chat') {
    return <AgentChat saasAgent={saasAgent} saasAgentId={saasAgentId} />
  }

  if (activeView === 'attachments') {
    return <AttachmentsPanel saasAgentId={saasAgentId} />
  }

  if (activeView === 'actions') {
    return <ActionsCanvas saasAgentId={saasAgentId} />
  }

  if (activeView === 'entities') {
    return <EntitiesCanvas saasAgentId={saasAgentId} />
  }

  if (activeView === 'admin') {
    return <AdminPanel saasAgent={saasAgent} saasAgentId={saasAgentId} />
  }

  return <LockedCanvasView view={activeView} />
}
