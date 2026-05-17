import { create } from 'zustand'

import { storage } from '@/lib/storage'

export type SaaSAgentView = 'connect' | 'entities' | 'actions' | 'chat' | 'attachments' | 'admin' | 'learn' | 'qa'
export type CapabilityStatus = 'active' | 'ready' | 'pending' | 'locked'

export interface ShellMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: number
}

export interface CapabilityItem {
  id: SaaSAgentView
  label: string
  shortLabel: string
  slice: string
  status: CapabilityStatus
  disabledReason?: string
}

interface SaaSAgentState {
  saasAgentId: string | null
  activeView: SaaSAgentView
  lastActiveViewBySaaSAgent: Record<string, SaaSAgentView>
  shellDraftBySaaSAgent: Record<string, string>
  shellMessagesBySaaSAgent: Record<string, ShellMessage[]>
  selectedConnectionId: string | null
  selectedEntityId: string | null
  selectedActionNodeId: string | null
  selectedQaRunId: string | null
  setSaaSAgentId: (saasAgentId: string | null) => void
  clearSaaSAgent: () => void
  setActiveView: (view: SaaSAgentView) => void
  setShellDraft: (saasAgentId: string, draft: string) => void
  appendShellMessage: (saasAgentId: string, message: ShellMessage) => void
  clearShellMessages: (saasAgentId: string) => void
  selectConnection: (id: string | null) => void
  selectEntity: (id: string | null) => void
  selectActionNode: (id: string | null) => void
  selectQaRun: (id: string | null) => void
  resetCanvasSelections: () => void
}

const ACTIVE_VIEW_KEY = 'sta_v01_active_views'

function readActiveViews(): Record<string, SaaSAgentView> {
  try {
    return JSON.parse(localStorage.getItem(ACTIVE_VIEW_KEY) || '{}')
  } catch {
    return {}
  }
}

function writeActiveViews(activeViews: Record<string, SaaSAgentView>) {
  localStorage.setItem(ACTIVE_VIEW_KEY, JSON.stringify(activeViews))
}

export const capabilityItems: CapabilityItem[] = [
  {
    id: 'chat',
    label: 'Operator Chat',
    shortLabel: 'Chat',
    slice: 'Live now',
    status: 'active',
  },
  {
    id: 'connect',
    label: 'Connections',
    shortLabel: 'Connect',
    slice: 'Live now',
    status: 'ready',
    disabledReason: 'Use this view to prepare the first API connection',
  },
  {
    id: 'attachments',
    label: 'Knowledge Base',
    shortLabel: 'Knowledge',
    slice: 'Live now',
    status: 'ready',
  },
  {
    id: 'admin',
    label: 'Sessions & Memory',
    shortLabel: 'Sessions',
    slice: 'Live now',
    status: 'ready',
  },
  {
    id: 'entities',
    label: 'Entities',
    shortLabel: 'Entities',
    slice: 'Live after activation',
    status: 'ready',
    disabledReason: 'Entity exploration populates after REST activation',
  },
  {
    id: 'actions',
    label: 'Actions',
    shortLabel: 'Actions',
    slice: 'Live after activation',
    status: 'ready',
    disabledReason: 'Generated action tools populate after REST activation',
  },
  {
    id: 'qa',
    label: 'QA',
    shortLabel: 'QA',
    slice: 'Later',
    status: 'locked',
    disabledReason: 'QA and learnings arrive after execution is available',
  },
]

export const useSaaSAgentStore = create<SaaSAgentState>((set, get) => ({
  saasAgentId: storage.getSaaSAgentId(),
  activeView: 'chat',
  lastActiveViewBySaaSAgent: readActiveViews(),
  shellDraftBySaaSAgent: {},
  shellMessagesBySaaSAgent: {},
  selectedConnectionId: null,
  selectedEntityId: null,
  selectedActionNodeId: null,
  selectedQaRunId: null,

  setSaaSAgentId: (saasAgentId) => {
    const lastActiveViewBySaaSAgent = get().lastActiveViewBySaaSAgent
    const nextActiveView = saasAgentId ? lastActiveViewBySaaSAgent[saasAgentId] || 'chat' : 'chat'

    if (saasAgentId) {
      storage.setSaaSAgentId(saasAgentId)
    } else {
      storage.removeSaaSAgentId()
    }

    set({ saasAgentId, activeView: nextActiveView })
  },

  clearSaaSAgent: () => {
    storage.removeSaaSAgentId()
    set({
      saasAgentId: null,
      activeView: 'chat',
      shellDraftBySaaSAgent: {},
      shellMessagesBySaaSAgent: {},
      selectedConnectionId: null,
      selectedEntityId: null,
      selectedActionNodeId: null,
      selectedQaRunId: null,
    })
  },

  setActiveView: (activeView) => {
    const { saasAgentId, lastActiveViewBySaaSAgent } = get()

    if (!saasAgentId) {
      set({ activeView })
      return
    }

    const nextViews = { ...lastActiveViewBySaaSAgent, [saasAgentId]: activeView }
    writeActiveViews(nextViews)
    set({ activeView, lastActiveViewBySaaSAgent: nextViews })
  },

  setShellDraft: (saasAgentId, draft) =>
    set((state) => ({
      shellDraftBySaaSAgent: {
        ...state.shellDraftBySaaSAgent,
        [saasAgentId]: draft,
      },
    })),
  appendShellMessage: (saasAgentId, message) =>
    set((state) => ({
      shellMessagesBySaaSAgent: {
        ...state.shellMessagesBySaaSAgent,
        [saasAgentId]: [...(state.shellMessagesBySaaSAgent[saasAgentId] || []), message],
      },
    })),
  clearShellMessages: (saasAgentId) =>
    set((state) => ({
      shellMessagesBySaaSAgent: {
        ...state.shellMessagesBySaaSAgent,
        [saasAgentId]: [],
      },
      shellDraftBySaaSAgent: {
        ...state.shellDraftBySaaSAgent,
        [saasAgentId]: '',
      },
    })),
  selectConnection: (selectedConnectionId) => set({ selectedConnectionId }),
  selectEntity: (selectedEntityId) => set({ selectedEntityId }),
  selectActionNode: (selectedActionNodeId) => set({ selectedActionNodeId }),
  selectQaRun: (selectedQaRunId) => set({ selectedQaRunId }),
  resetCanvasSelections: () =>
    set({
      selectedConnectionId: null,
      selectedEntityId: null,
      selectedActionNodeId: null,
      selectedQaRunId: null,
    }),
}))
