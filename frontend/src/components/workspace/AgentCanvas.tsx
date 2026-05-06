import { AgentChatStub } from '@/components/workspace/AgentChatStub'
import { ConnectSetupView } from '@/components/workspace/ConnectSetupView'
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
    return <AgentChatStub workspace={workspace} stats={stats} />
  }

  return <LockedCanvasView view={activeView} />
}
