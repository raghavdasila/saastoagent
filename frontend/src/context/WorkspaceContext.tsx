import { type ReactNode, createContext, useContext, useEffect } from 'react'
import { useParams } from 'react-router-dom'

import { storage } from '@/lib/storage'

interface WorkspaceContextValue {
  workspaceId: string | null
}

const WorkspaceContext = createContext<WorkspaceContextValue>({ workspaceId: null })

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const { workspaceId } = useParams<{ workspaceId: string }>()

  useEffect(() => {
    if (workspaceId) {
      storage.setWorkspaceId(workspaceId)
    }
  }, [workspaceId])

  return (
    <WorkspaceContext.Provider value={{ workspaceId: workspaceId || null }}>
      {children}
    </WorkspaceContext.Provider>
  )
}

export function useWorkspace() {
  return useContext(WorkspaceContext)
}
