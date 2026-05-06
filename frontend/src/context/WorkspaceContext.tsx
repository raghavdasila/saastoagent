import { type ReactNode, createContext, useContext, useEffect } from 'react'
import { useParams } from 'react-router-dom'

import { useWorkspaceStore, type WorkspaceView } from '@/stores/workspaceStore'

interface WorkspaceContextValue {
  workspaceId: string | null
  activeView: WorkspaceView
  setActiveView: (view: WorkspaceView) => void
}

const WorkspaceContext = createContext<WorkspaceContextValue>({
  workspaceId: null,
  activeView: 'chat',
  setActiveView: () => undefined,
})

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const storedWorkspaceId = useWorkspaceStore((state) => state.workspaceId)
  const activeView = useWorkspaceStore((state) => state.activeView)
  const setWorkspaceId = useWorkspaceStore((state) => state.setWorkspaceId)
  const setActiveView = useWorkspaceStore((state) => state.setActiveView)

  useEffect(() => {
    setWorkspaceId(workspaceId || null)
  }, [setWorkspaceId, workspaceId])

  return (
    <WorkspaceContext.Provider value={{ workspaceId: storedWorkspaceId, activeView, setActiveView }}>
      {children}
    </WorkspaceContext.Provider>
  )
}

export function useWorkspace() {
  return useContext(WorkspaceContext)
}
