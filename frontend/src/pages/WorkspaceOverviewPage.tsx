import { useQuery } from '@tanstack/react-query'

import { AgentCanvas } from '@/components/workspace/AgentCanvas'
import { useWorkspace } from '@/context/WorkspaceContext'
import { api } from '@/lib/api'
import type { Workspace, WorkspaceStats } from '@/types/domain'

export function WorkspaceOverviewPage() {
  const { workspaceId } = useWorkspace()

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
