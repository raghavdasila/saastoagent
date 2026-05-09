/**
 * WorkspaceShell
 *
 * Renders the full operator workspace UI (Header + ActivityBar + AgentCanvas)
 * while accepting `workspaceId` as a prop instead of reading it from React
 * Router's useParams.  This lets OperatorGateway mount the workspace inline
 * when the graph reaches `operator_ready` — without any route navigation.
 *
 * The /w/:workspaceId deep-link route still uses WorkspaceLayout (which relies
 * on useParams via WorkspaceProvider's default behaviour) and that path is
 * unaffected by this component.
 */

import { Header } from '@/components/layout/Header'
import { ActivityBar } from '@/components/workspace/ActivityBar'
import { AgentCanvas } from '@/components/workspace/AgentCanvas'
import { WorkspaceProvider } from '@/context/WorkspaceContext'
import { api } from '@/lib/api'
import type { Workspace, WorkspaceStats } from '@/types/domain'
import { useQuery } from '@tanstack/react-query'

interface WorkspaceShellProps {
  workspaceId: string
}

function WorkspaceContent({ workspaceId }: WorkspaceShellProps) {
  const { data: workspace } = useQuery({
    queryKey: ['workspace', workspaceId],
    queryFn: () => api.get<Workspace>(`/workspaces/${workspaceId}`),
    enabled: !!workspaceId,
  })

  const { data: stats } = useQuery({
    queryKey: ['workspace-stats', workspaceId],
    queryFn: () => api.get<WorkspaceStats>(`/workspaces/${workspaceId}/stats`),
    enabled: !!workspaceId,
  })

  return <AgentCanvas workspace={workspace} stats={stats} />
}

export function WorkspaceShell({ workspaceId }: WorkspaceShellProps) {
  return (
    <WorkspaceProvider workspaceId={workspaceId}>
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <div className="md:flex">
          <ActivityBar />
          <main className="min-w-0 flex-1">
            <WorkspaceContent workspaceId={workspaceId} />
          </main>
        </div>
      </div>
    </WorkspaceProvider>
  )
}
