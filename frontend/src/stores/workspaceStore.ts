import { create } from 'zustand'

import { storage } from '@/lib/storage'

export type WorkspaceView = 'connect' | 'entities' | 'actions' | 'chat' | 'attachments' | 'admin' | 'qa'
export type CapabilityStatus = 'active' | 'ready' | 'pending' | 'locked'

export interface ShellMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: number
}

export interface CapabilityItem {
  id: WorkspaceView
  label: string
  shortLabel: string
  slice: string
  status: CapabilityStatus
  disabledReason?: string
}

interface WorkspaceState {
  workspaceId: string | null
  activeView: WorkspaceView
  lastActiveViewByWorkspace: Record<string, WorkspaceView>
  shellDraftByWorkspace: Record<string, string>
  shellMessagesByWorkspace: Record<string, ShellMessage[]>
  selectedConnectionId: string | null
  selectedEntityId: string | null
  selectedActionNodeId: string | null
  selectedQaRunId: string | null
  setWorkspaceId: (workspaceId: string | null) => void
  clearWorkspace: () => void
  setActiveView: (view: WorkspaceView) => void
  setShellDraft: (workspaceId: string, draft: string) => void
  appendShellMessage: (workspaceId: string, message: ShellMessage) => void
  clearShellMessages: (workspaceId: string) => void
  selectConnection: (id: string | null) => void
  selectEntity: (id: string | null) => void
  selectActionNode: (id: string | null) => void
  selectQaRun: (id: string | null) => void
  resetCanvasSelections: () => void
}

const ACTIVE_VIEW_KEY = 'sta_v01_active_views'

function readActiveViews(): Record<string, WorkspaceView> {
  try {
    return JSON.parse(localStorage.getItem(ACTIVE_VIEW_KEY) || '{}')
  } catch {
    return {}
  }
}

function writeActiveViews(activeViews: Record<string, WorkspaceView>) {
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
    slice: 'Later',
    status: 'locked',
    disabledReason: 'Entity exploration unlocks after REST activation',
  },
  {
    id: 'actions',
    label: 'Actions',
    shortLabel: 'Actions',
    slice: 'Later',
    status: 'locked',
    disabledReason: 'Generated action tools unlock after REST activation',
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

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  workspaceId: storage.getWorkspaceId(),
  activeView: 'chat',
  lastActiveViewByWorkspace: readActiveViews(),
  shellDraftByWorkspace: {},
  shellMessagesByWorkspace: {},
  selectedConnectionId: null,
  selectedEntityId: null,
  selectedActionNodeId: null,
  selectedQaRunId: null,

  setWorkspaceId: (workspaceId) => {
    const lastActiveViewByWorkspace = get().lastActiveViewByWorkspace
    const nextActiveView = workspaceId ? lastActiveViewByWorkspace[workspaceId] || 'chat' : 'chat'

    if (workspaceId) {
      storage.setWorkspaceId(workspaceId)
    } else {
      storage.removeWorkspaceId()
    }

    set({ workspaceId, activeView: nextActiveView })
  },

  clearWorkspace: () => {
    storage.removeWorkspaceId()
    set({
      workspaceId: null,
      activeView: 'chat',
      shellDraftByWorkspace: {},
      shellMessagesByWorkspace: {},
      selectedConnectionId: null,
      selectedEntityId: null,
      selectedActionNodeId: null,
      selectedQaRunId: null,
    })
  },

  setActiveView: (activeView) => {
    const { workspaceId, lastActiveViewByWorkspace } = get()

    if (!workspaceId) {
      set({ activeView })
      return
    }

    const nextViews = { ...lastActiveViewByWorkspace, [workspaceId]: activeView }
    writeActiveViews(nextViews)
    set({ activeView, lastActiveViewByWorkspace: nextViews })
  },

  setShellDraft: (workspaceId, draft) =>
    set((state) => ({
      shellDraftByWorkspace: {
        ...state.shellDraftByWorkspace,
        [workspaceId]: draft,
      },
    })),
  appendShellMessage: (workspaceId, message) =>
    set((state) => ({
      shellMessagesByWorkspace: {
        ...state.shellMessagesByWorkspace,
        [workspaceId]: [...(state.shellMessagesByWorkspace[workspaceId] || []), message],
      },
    })),
  clearShellMessages: (workspaceId) =>
    set((state) => ({
      shellMessagesByWorkspace: {
        ...state.shellMessagesByWorkspace,
        [workspaceId]: [],
      },
      shellDraftByWorkspace: {
        ...state.shellDraftByWorkspace,
        [workspaceId]: '',
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
