import { type ReactNode, createContext, useContext, useEffect } from 'react'
import { useParams } from 'react-router-dom'

import { useSaaSAgentStore, type SaaSAgentView } from '@/stores/saasAgentStore'

interface SaaSAgentContextValue {
  saasAgentId: string | null
  activeView: SaaSAgentView
  setActiveView: (view: SaaSAgentView) => void
}

const SaaSAgentContext = createContext<SaaSAgentContextValue>({
  saasAgentId: null,
  activeView: 'chat',
  setActiveView: () => undefined,
})

interface SaaSAgentProviderProps {
  children: ReactNode
  /** Optional override — when set, useParams is ignored.  Used by SaaSAgentShell
   *  (rendered inside OperatorGateway) which is not mounted under a /agents/:id route. */
  saasAgentId?: string
}

export function SaaSAgentProvider({ children, saasAgentId: saasAgentIdProp }: SaaSAgentProviderProps) {
  const { saasAgentId: routeSaaSAgentId } = useParams<{ saasAgentId: string }>()
  const saasAgentId = saasAgentIdProp ?? routeSaaSAgentId
  const storedSaaSAgentId = useSaaSAgentStore((state) => state.saasAgentId)
  const activeView = useSaaSAgentStore((state) => state.activeView)
  const setSaaSAgentId = useSaaSAgentStore((state) => state.setSaaSAgentId)
  const setActiveView = useSaaSAgentStore((state) => state.setActiveView)

  useEffect(() => {
    setSaaSAgentId(saasAgentId || null)
  }, [setSaaSAgentId, saasAgentId])

  return (
    <SaaSAgentContext.Provider value={{ saasAgentId: storedSaaSAgentId, activeView, setActiveView }}>
      {children}
    </SaaSAgentContext.Provider>
  )
}

export function useSaaSAgent() {
  return useContext(SaaSAgentContext)
}
