import { AdminPanel } from '@/components/agent/AdminPanel'
import { AgentChat } from '@/components/agent/AgentChat'
import { AttachmentsPanel } from '@/components/agent/AttachmentsPanel'
import { ActionsCanvas } from '@/components/saasAgent/ActionsCanvas'
import { ConnectSetupView } from '@/components/saasAgent/ConnectSetupView'
import { EntitiesCanvas } from '@/components/saasAgent/EntitiesCanvas'
import { LockedCanvasView } from '@/components/saasAgent/LockedCanvasView'
import { useSaaSAgentStore } from '@/stores/saasAgentStore'
import type { SaaSAgent, SaaSAgentStats } from '@/types/domain'

interface AgentCanvasProps {
  saasAgent?: SaaSAgent
  stats?: SaaSAgentStats
}

export function AgentCanvas({ saasAgent, stats }: AgentCanvasProps) {
  const activeView = useSaaSAgentStore((state) => state.activeView)

  if (activeView === 'connect') {
    return <ConnectSetupView saasAgent={saasAgent} stats={stats} />
  }

  if (activeView === 'chat') {
    return <AgentChat saasAgent={saasAgent} />
  }

  if (activeView === 'attachments') {
    return <AttachmentsPanel />
  }

  if (activeView === 'actions') {
    return <ActionsCanvas />
  }

  if (activeView === 'entities') {
    return <EntitiesCanvas />
  }

  if (activeView === 'admin') {
    return <AdminPanel saasAgent={saasAgent} />
  }

  return <LockedCanvasView view={activeView} />
}
