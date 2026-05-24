import { type ReactNode, createContext, useContext, useEffect } from 'react'
import { useParams } from 'react-router-dom'

import { useSaaSAgentUiStore, type SaaSAgentView } from '@/stores/saasAgentUiStore'

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
  /** Optional override: when set, useParams is ignored. Used by SaaSAgentShell
   *  when Corpus renders an agent surface without a /agents/:id route. */
  saasAgentId?: string
}

export function SaaSAgentProvider({ children, saasAgentId: saasAgentIdProp }: SaaSAgentProviderProps) {
  const { saasAgentId: routeSaaSAgentId } = useParams<{ saasAgentId: string }>()
  const saasAgentId = saasAgentIdProp ?? routeSaaSAgentId
  const effectiveSaaSAgentId = saasAgentId || null
  const mirroredSaaSAgentId = useSaaSAgentUiStore((state) => state.mirroredSaaSAgentId)
  const activeView = useSaaSAgentUiStore((state) => state.activeView)
  const setMirroredSaaSAgentId = useSaaSAgentUiStore((state) => state.setMirroredSaaSAgentId)
  const setActiveView = useSaaSAgentUiStore((state) => state.setActiveView)

  useEffect(() => {
    setMirroredSaaSAgentId(saasAgentId || null)
  }, [setMirroredSaaSAgentId, saasAgentId])

  return (
    <SaaSAgentContext.Provider value={{ saasAgentId: effectiveSaaSAgentId || mirroredSaaSAgentId, activeView, setActiveView }}>
      {children}
    </SaaSAgentContext.Provider>
  )
}

export function useSaaSAgent() {
  return useContext(SaaSAgentContext)
}
