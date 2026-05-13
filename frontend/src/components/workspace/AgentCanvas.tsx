import { AdminPanel } from '@/components/agent/AdminPanel'
import { AgentChat } from '@/components/agent/AgentChat'
import { AttachmentsPanel } from '@/components/agent/AttachmentsPanel'
import { ActionsCanvas } from '@/components/workspace/ActionsCanvas'
import { ConnectSetupView } from '@/components/workspace/ConnectSetupView'
import { EntitiesCanvas } from '@/components/workspace/EntitiesCanvas'
import { LockedCanvasView } from '@/components/workspace/LockedCanvasView'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import type { Workspace, WorkspaceStats } from '@/types/domain'

interface AgentCanvasProps {
  workspace?: Workspace
  stats?: WorkspaceStats
}

export function AgentCanvas({ workspace, stats }: AgentCanvasProps) {
  const activeView = useWorkspaceStore((state) => state.activeView)

  if (activeView === 'connect') {
    return <ConnectSetupView workspace={workspace} stats={stats} />
  }

  if (activeView === 'chat') {
    return <AgentChat workspace={workspace} />
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
    return <AdminPanel workspace={workspace} />
  }

  return <LockedCanvasView view={activeView} />
}
