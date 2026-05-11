import { create } from 'zustand'

import type {
  EntryActionCard,
  EntryGraphManifest,
  EntryTurnResponse,
  EntryUIArtifact,
  GatewayState,
  RouteDeckRuntimeSnapshot,
  OperatorExperienceMode,
  OperatorSidebarItem,
  UnifiedOperatorMessage,
} from '@/types/entry'

interface EntryState {
  graphState: GatewayState | null
  mode: OperatorExperienceMode
  activeWorkspaceId: string | null
  activeSidebarItem: OperatorSidebarItem
  entrySessionId: string | null
  agentSessionId: string | null
  runId: string | null
  graphVersion: string | null
  graphManifest: EntryGraphManifest | null
  routeDeckSnapshot: RouteDeckRuntimeSnapshot | null
  selectedDebugNode: string | null
  messages: UnifiedOperatorMessage[]
  draft: string
  busy: boolean
  availableActions: EntryActionCard[]
  persistentActions: EntryActionCard[]
  uiArtifacts: EntryUIArtifact[]
  canvasOpen: boolean
  canvasCollapsed: boolean
  canvasArtifactId: string | null
  setGraphState: (graphState: GatewayState | null) => void
  setEntrySessionId: (sessionId: string | null) => void
  setAgentSessionId: (sessionId: string | null) => void
  enterOperatorMode: (workspaceId: string) => void
  setActiveSidebarItem: (item: OperatorSidebarItem) => void
  setSelectedDebugNode: (nodeId: string | null) => void
  setDraft: (draft: string) => void
  setBusy: (busy: boolean) => void
  setAvailableActions: (actions: EntryActionCard[]) => void
  setPersistentActions: (actions: EntryActionCard[]) => void
  clearAvailableActions: () => void
  appendAssistant: (content: string) => void
  appendUser: (content: string) => void
  applyArtifacts: (artifacts: EntryUIArtifact[]) => void
  applyTurnPayload: (payload: EntryTurnResponse) => void
  openCanvasArtifact: (artifactId: string) => void
  closeCanvas: () => void
  toggleCanvasCollapsed: () => void
  resetEntry: () => void
}

function makeMsg(role: 'user' | 'assistant', content: string): UnifiedOperatorMessage {
  const id = typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`
  return { id, role, content, timestamp: Date.now(), source: 'entry' }
}

function isCanvasCapable(artifact: EntryUIArtifact): boolean {
  return artifact.surface === 'canvas' || artifact.surface === 'both'
}

const initialState = {
  graphState: null,
  mode: 'entry' as OperatorExperienceMode,
  activeWorkspaceId: null,
  activeSidebarItem: 'chat' as OperatorSidebarItem,
  entrySessionId: null,
  agentSessionId: null,
  runId: null,
  graphVersion: null,
  graphManifest: null,
  routeDeckSnapshot: null,
  selectedDebugNode: null,
  messages: [],
  draft: '',
  busy: false,
  availableActions: [],
  persistentActions: [],
  uiArtifacts: [],
  canvasOpen: false,
  canvasCollapsed: false,
  canvasArtifactId: null,
}

export const useEntryStore = create<EntryState>((set) => ({
  ...initialState,

  setGraphState: (graphState) => set({ graphState }),
  setEntrySessionId: (entrySessionId) => set({ entrySessionId }),
  setAgentSessionId: (agentSessionId) => set({ agentSessionId }),
  enterOperatorMode: (activeWorkspaceId) => set({ mode: 'operator', activeWorkspaceId, activeSidebarItem: 'chat' }),
  setActiveSidebarItem: (activeSidebarItem) => set({ activeSidebarItem }),
  setSelectedDebugNode: (selectedDebugNode) => set({ selectedDebugNode }),
  setDraft: (draft) => set({ draft }),
  setBusy: (busy) => set({ busy }),
  setAvailableActions: (availableActions) => set({ availableActions }),
  setPersistentActions: (persistentActions) => set({ persistentActions }),
  clearAvailableActions: () => set({ availableActions: [] }),
  appendAssistant: (content) => set((state) => ({ messages: [...state.messages, makeMsg('assistant', content)] })),
  appendUser: (content) => set((state) => ({ messages: [...state.messages, makeMsg('user', content)] })),

  applyArtifacts: (uiArtifacts) => set((state) => {
    const selectedStillExists = state.canvasArtifactId
      ? uiArtifacts.some((artifact) => artifact.id === state.canvasArtifactId && isCanvasCapable(artifact))
      : false
    return {
      uiArtifacts,
      canvasArtifactId: selectedStillExists ? state.canvasArtifactId : null,
      canvasOpen: selectedStillExists ? state.canvasOpen : false,
      canvasCollapsed: selectedStillExists ? state.canvasCollapsed : false,
    }
  }),

  applyTurnPayload: (payload) => set((state) => {
    const uiArtifacts = Array.isArray(payload.ui_artifacts) ? payload.ui_artifacts : state.uiArtifacts
    const selectedStillExists = state.canvasArtifactId
      ? uiArtifacts.some((artifact) => artifact.id === state.canvasArtifactId && isCanvasCapable(artifact))
      : false
    const activeWorkspaceId = payload.state.active_workspace_id || state.activeWorkspaceId
    const hasWorkspace = Boolean(activeWorkspaceId)
    return {
      graphState: payload.state,
      runId: payload.run_id || state.runId,
      graphVersion: payload.graph_version || state.graphVersion,
      graphManifest: payload.graph_manifest || state.graphManifest,
      routeDeckSnapshot: payload.route_deck_snapshot || state.routeDeckSnapshot,
      selectedDebugNode: state.selectedDebugNode || payload.route_deck_snapshot?.current_node || payload.state.node,
      mode: hasWorkspace ? 'operator' : state.mode,
      activeWorkspaceId,
      activeSidebarItem: hasWorkspace && state.mode !== 'operator' ? 'chat' : state.activeSidebarItem,
      availableActions: Array.isArray(payload.available_actions) ? payload.available_actions : state.availableActions,
      persistentActions: Array.isArray(payload.persistent_actions) ? payload.persistent_actions : state.persistentActions,
      uiArtifacts,
      canvasArtifactId: selectedStillExists ? state.canvasArtifactId : null,
      canvasOpen: selectedStillExists ? state.canvasOpen : false,
      canvasCollapsed: selectedStillExists ? state.canvasCollapsed : false,
    }
  }),

  openCanvasArtifact: (artifactId) => set((state) => {
    const artifact = state.uiArtifacts.find((item) => item.id === artifactId && isCanvasCapable(item))
    if (!artifact) return {}
    return {
      canvasArtifactId: artifact.id,
      canvasOpen: true,
      canvasCollapsed: false,
    }
  }),

  closeCanvas: () => set({ canvasOpen: false, canvasCollapsed: false, canvasArtifactId: null }),
  toggleCanvasCollapsed: () => set((state) => ({ canvasCollapsed: !state.canvasCollapsed })),
  resetEntry: () => set(initialState),
}))
