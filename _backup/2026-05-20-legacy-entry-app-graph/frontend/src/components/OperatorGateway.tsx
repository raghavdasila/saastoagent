import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Bot,
} from 'lucide-react'

import { AdminPanel } from '@/components/agent/AdminPanel'
import { AttachmentsPanel } from '@/components/agent/AttachmentsPanel'
import { ChatInput } from '@/components/agent/ChatInput'
import { CommandComposer } from '@/components/agent/CommandComposer'
import { LearningPanel } from '@/components/agent/LearningPanel'
import { MessageBubble } from '@/components/agent/MessageBubble'
import { ThinkingIndicator } from '@/components/agent/ThinkingIndicator'
import { EntryActionCards } from '@/components/entry/EntryActionCards'
import { EntryArtifactRenderer } from '@/components/entry/EntryArtifactRenderer'
import { EntryCanvasLauncher } from '@/components/entry/EntryCanvasLauncher'
import { EntryCanvasShell } from '@/components/entry/EntryCanvasShell'
import {
  ActionDock,
  buildReadiness,
  CapabilityRail,
  ContextLens,
  EvidenceDrawer,
  OperatorStatusStrip,
  type AutonomyLevel,
} from '@/components/operator/OperatorWorkbench'
import { RouteDeckNavWidget } from '@/components/operator/RouteDeckNavWidget'
import { QAAgentPanel } from '@/components/qa/QAAgentPanel'
import { ThemeToggleButton } from '@/components/theme/ThemeToggleButton'
import { ActionsCanvas } from '@/components/saasAgent/ActionsCanvas'
import { ConnectSetupView } from '@/components/saasAgent/ConnectSetupView'
import { EntitiesCanvas } from '@/components/saasAgent/EntitiesCanvas'
import { useAuth } from '@/context/AuthContext'
import { useSSEChat } from '@/hooks/useSSEChat'
import { api, ApiError } from '@/lib/api'
import { cn } from '@/lib/cn'
import { formatSaaSAgentDisplayName, OPERATOR_NAME, PRODUCT_NAME } from '@/lib/entryGraph'
import { entryCapabilities, findCapabilityAction, pickNextBestAction, saasAgentCapabilities, type OperatorCapabilityDefinition } from '@/lib/operatorExperience'
import { storage } from '@/lib/storage'
import { useAuthStore } from '@/stores/authStore'
import { useEntryStore } from '@/stores/entryStore'
import { useSaaSAgentStore, type SaaSAgentView } from '@/stores/saasAgentStore'
import type { AgentDocument, AgentHandoffContext } from '@/types/agent'
import type { SaaSAgent, SaaSAgentStats } from '@/types/domain'
import type {
  AuthIntent,
  EntryActionCard,
  EntryPersistentActionsResponse,
  EntryTurnResponse,
  EntryUIArtifact,
  GatewayNode,
  OperatorExperienceMode,
  OperatorSidebarItem,
  SaaSAgentRouteDeckContext,
  SaaSAgentRouteDeckResponse,
  StageCompletedEvent,
} from '@/types/entry'

type EntryStreamEvent =
  | 'stream_start'
  | 'run_started'
  | 'stage_started'
  | 'message_delta'
  | 'stage_completed'
  | 'entry_turn_result'
  | 'setup_step'
  | 'run_completed'
  | 'stream_end'
  | 'error'

export interface OperatorGatewayProps {
  initialIntent?: AuthIntent
  initialSaaSAgentId?: string | null
}

const agentStarterPrompts = [
  'What can you do here?',
  'Help me connect an API.',
  'What should I set up next?',
]

function setupStepMessage(data: Record<string, unknown>): string | null {
  const step = typeof data.step === 'string' ? data.step : null
  const status = typeof data.status === 'string' ? data.status : null
  if (!step || !status) return null
  if (data.type === 'error') {
    return `Setup blocked: ${typeof data.message === 'string' ? data.message : 'unknown error'}`
  }
  if (status === 'running') return `Running setup step: ${step}.`
  if (status === 'done') return `Completed setup step: ${step}.`
  if (status === 'skipped' && typeof data.message === 'string') return data.message
  return null
}

function isCanvasCapableArtifact(artifact: EntryUIArtifact): boolean {
  return artifact.surface === 'canvas' || artifact.surface === 'both'
}

function saasAgentIdFromPath(path?: string | null): string | null {
  if (!path) return null
  const match = /^\/agents\/([^/?#]+)/.exec(path)
  return match ? decodeURIComponent(match[1]) : null
}

function isEntryGraphActive(stateNode?: GatewayNode | null): boolean {
  return Boolean(stateNode && stateNode !== 'operator_ready')
}

function dedupeActions(actions: EntryActionCard[]): EntryActionCard[] {
  const seen = new Set<string>()
  const deduped: EntryActionCard[] = []
  for (const action of actions) {
    if (seen.has(action.id)) continue
    seen.add(action.id)
    deduped.push(action)
  }
  return deduped
}

export function OperatorGateway({ initialIntent, initialSaaSAgentId }: OperatorGatewayProps) {
  const { isLoading: authLoading, user, logout } = useAuth()
  const applySession = useAuthStore((state) => state.applySession)

  const gs = useEntryStore((state) => state.graphState)
  const mode = useEntryStore((state) => state.mode)
  const activeSaaSAgentId = useEntryStore((state) => state.activeSaaSAgentId)
  const activeSidebarItem = useEntryStore((state) => state.activeSidebarItem)
  const entrySessionId = useEntryStore((state) => state.entrySessionId)
  const agentSessionId = useEntryStore((state) => state.agentSessionId)
  const runId = useEntryStore((state) => state.runId)
  const graphManifest = useEntryStore((state) => state.graphManifest)
  const routeDeckSnapshot = useEntryStore((state) => state.routeDeckSnapshot)
  const selectedDebugNode = useEntryStore((state) => state.selectedDebugNode)
  const messages = useEntryStore((state) => state.messages)
  const draft = useEntryStore((state) => state.draft)
  const busy = useEntryStore((state) => state.busy)
  const availableActions = useEntryStore((state) => state.availableActions)
  const persistentActions = useEntryStore((state) => state.persistentActions)
  const uiArtifacts = useEntryStore((state) => state.uiArtifacts)
  const canvasOpen = useEntryStore((state) => state.canvasOpen)
  const canvasCollapsed = useEntryStore((state) => state.canvasCollapsed)
  const canvasArtifactId = useEntryStore((state) => state.canvasArtifactId)

  const setDraft = useEntryStore((state) => state.setDraft)
  const setBusy = useEntryStore((state) => state.setBusy)
  const setAvailableActions = useEntryStore((state) => state.setAvailableActions)
  const setPersistentActions = useEntryStore((state) => state.setPersistentActions)
  const clearAvailableActions = useEntryStore((state) => state.clearAvailableActions)
  const appendAssistant = useEntryStore((state) => state.appendAssistant)
  const appendAssistantDelta = useEntryStore((state) => state.appendAssistantDelta)
  const appendUser = useEntryStore((state) => state.appendUser)
  const applyArtifacts = useEntryStore((state) => state.applyArtifacts)
  const applyTurnPayload = useEntryStore((state) => state.applyTurnPayload)
  const openCanvasArtifact = useEntryStore((state) => state.openCanvasArtifact)
  const closeCanvas = useEntryStore((state) => state.closeCanvas)
  const toggleCanvasCollapsed = useEntryStore((state) => state.toggleCanvasCollapsed)
  const setEntrySessionId = useEntryStore((state) => state.setEntrySessionId)
  const setAgentSessionId = useEntryStore((state) => state.setAgentSessionId)
  const enterOperatorMode = useEntryStore((state) => state.enterOperatorMode)
  const setActiveSidebarItem = useEntryStore((state) => state.setActiveSidebarItem)
  const setSelectedDebugNode = useEntryStore((state) => state.setSelectedDebugNode)
  const resetEntryForQA = useEntryStore((state) => state.resetEntryForQA)

  const setSaaSAgentId = useSaaSAgentStore((state) => state.setSaaSAgentId)
  const setSaaSAgentActiveView = useSaaSAgentStore((state) => state.setActiveView)

  const queryClient = useQueryClient()
  const [operatorError, setOperatorError] = useState<string | null>(null)
  const [injectText, setInjectText] = useState('')
  const [handoffSaaSAgentId, setHandoffSaaSAgentId] = useState<string | null>(initialSaaSAgentId ?? null)
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [autonomyLevel, setAutonomyLevel] = useState<AutonomyLevel>('ask')

  const scrollRef = useRef<HTMLDivElement>(null)
  const bootstrapped = useRef(false)
  const xhrRef = useRef<XMLHttpRequest | null>(null)
  const streamCursorRef = useRef(0)
  const streamBufferRef = useRef('')
  const entrySessionIdRef = useRef<string | null>(entrySessionId)
  const routeSaaSAgentId = useMemo(
    () => initialSaaSAgentId || saasAgentIdFromPath(window.location.pathname),
    [initialSaaSAgentId],
  )

  const graphSaaSAgentId = typeof gs?.active_saas_agent_id === 'string' ? gs.active_saas_agent_id : null
  const saasAgentId = handoffSaaSAgentId || activeSaaSAgentId || graphSaaSAgentId || routeSaaSAgentId || null
  const entryGraphActive = isEntryGraphActive(gs?.node)
  const showOperatorMode = Boolean(saasAgentId) && !entryGraphActive && (mode === 'operator' || Boolean(handoffSaaSAgentId) || Boolean(graphSaaSAgentId) || Boolean(routeSaaSAgentId))
  const canvasArtifacts = useMemo(
    () => uiArtifacts.filter(isCanvasCapableArtifact),
    [uiArtifacts],
  )
  const canvasArtifact = useMemo(() => {
    if (!canvasOpen || !canvasArtifactId) return null
    return uiArtifacts.find((artifact) => artifact.id === canvasArtifactId && isCanvasCapableArtifact(artifact)) || null
  }, [canvasArtifactId, canvasOpen, uiArtifacts])

  const {
    messages: agentMessages,
    isStreaming: agentStreaming,
    sessionId: liveAgentSessionId,
    sendMessage: sendAgentMessage,
  } = useSSEChat({
    saasAgentId,
    onError: setOperatorError,
  })

  const { data: saasAgent } = useQuery({
    queryKey: ['saasAgent', saasAgentId],
    queryFn: () => api.get<SaaSAgent>(`/saas-agents/${saasAgentId}`),
    enabled: !!saasAgentId && !!user,
  })

  const { data: stats } = useQuery({
    queryKey: ['saasAgent-stats', saasAgentId],
    queryFn: () => api.get<SaaSAgentStats>(`/saas-agents/${saasAgentId}/stats`),
    enabled: !!saasAgentId && !!user,
  })

  const { data: saasAgentRouteDeck } = useQuery({
    queryKey: ['saasAgent-route-deck', saasAgentId, stats?.connections_count, stats?.tools_count],
    queryFn: () => api.get<SaaSAgentRouteDeckResponse>(`/saas-agents/${saasAgentId}/route-deck`),
    enabled: showOperatorMode && !!saasAgentId && !!user,
    refetchInterval: showOperatorMode ? 10_000 : false,
  })

  const uploadFile = useMutation({
    mutationFn: (file: File) => api.upload<AgentDocument>(`/saas-agents/${saasAgentId}/agent/documents`, file),
    onSuccess: (doc) => {
      queryClient.invalidateQueries({ queryKey: ['agent-documents', saasAgentId] })
      setInjectText(`Tell me what's in ${doc.original_name}`)
    },
    onError: (error) => {
      setOperatorError(error instanceof ApiError ? error.message : 'Upload failed')
    },
  })
  const { data: persistentActionsData } = useQuery<EntryPersistentActionsResponse>({
    queryKey: ['entry-persistent-actions', Boolean(user), saasAgentId],
    queryFn: () => api.get(`/entry/persistent-actions${saasAgentId ? `?saas_agent_id=${encodeURIComponent(saasAgentId)}` : ''}`),
    enabled: !entryGraphActive,
    staleTime: 30_000,
  })

  const allMessages = useMemo(() => [...messages, ...agentMessages], [messages, agentMessages])
  const persistentActionIds = useMemo(
    () => new Set(persistentActions.map((action) => action.id)),
    [persistentActions],
  )
  const contextualActions = useMemo(
    () => availableActions.filter((action) => !persistentActionIds.has(action.id)),
    [availableActions, persistentActionIds],
  )
  const actionLookup = useMemo(
    () => dedupeActions([...persistentActions, ...availableActions]),
    [availableActions, persistentActions],
  )
  const visibleMode: OperatorExperienceMode = showOperatorMode ? 'operator' : 'entry'
  const capabilities = visibleMode === 'operator' ? saasAgentCapabilities : entryCapabilities
  const activeCapability = capabilities.find((candidate) => candidate.id === activeSidebarItem)
  const capabilityRuntime = useMemo(
    () => ({
      busy: showOperatorMode ? agentStreaming : busy,
      hasSaaSAgent: Boolean(saasAgentId),
      isAuthenticated: Boolean(user),
      stats,
      operatorError,
    }),
    [agentStreaming, busy, operatorError, stats, user, saasAgentId, showOperatorMode],
  )
  const readiness = useMemo(
    () => buildReadiness({
      mode: visibleMode,
      saasAgentId,
      stats,
      isAuthenticated: Boolean(user),
      operatorError,
    }),
    [operatorError, stats, user, visibleMode, saasAgentId],
  )
  const nextBestAction = useMemo(
    () => pickNextBestAction(actionLookup, visibleMode),
    [actionLookup, visibleMode],
  )
  const saasAgentDisplayName = useMemo(
    () => formatSaaSAgentDisplayName(saasAgent?.name),
    [saasAgent?.name],
  )
  const activeGraphManifest = showOperatorMode && saasAgentRouteDeck?.manifest ? saasAgentRouteDeck.manifest : graphManifest
  const activeRouteDeckSnapshot = showOperatorMode && saasAgentRouteDeck?.snapshot ? saasAgentRouteDeck.snapshot : routeDeckSnapshot
  const activeGraphNode = showOperatorMode
    ? saasAgentRouteDeck?.snapshot?.current_node || null
    : gs?.node || null

  useEffect(() => {
    if (persistentActionsData) {
      setPersistentActions(persistentActionsData.persistent_actions)
    }
  }, [persistentActionsData, setPersistentActions])

  useEffect(() => {
    entrySessionIdRef.current = entrySessionId
  }, [entrySessionId])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [allMessages])

  useEffect(() => {
    if (routeSaaSAgentId) {
      setHandoffSaaSAgentId(routeSaaSAgentId)
      enterOperatorMode(routeSaaSAgentId)
    }
  }, [enterOperatorMode, routeSaaSAgentId])

  useEffect(() => {
    setSaaSAgentId(saasAgentId)
  }, [setSaaSAgentId, saasAgentId])

  useEffect(() => {
    if (liveAgentSessionId) {
      setAgentSessionId(liveAgentSessionId)
    }
  }, [liveAgentSessionId, setAgentSessionId])

  const finishStream = useCallback(() => {
    appendAssistantDelta('', true)
    setBusy(false)
    xhrRef.current = null
    streamCursorRef.current = 0
    streamBufferRef.current = ''
  }, [appendAssistantDelta, setBusy])

  const applyTurnResult = useCallback(
    (payload: EntryTurnResponse) => {
      if (payload.session) {
        applySession(payload.session.user, payload.session.access_token)
      }

      const pathSaaSAgentId = saasAgentIdFromPath(payload.replace_path)
      const resultSaaSAgentId = payload.state.active_saas_agent_id || pathSaaSAgentId
      if (resultSaaSAgentId) {
        setHandoffSaaSAgentId(resultSaaSAgentId)
        enterOperatorMode(resultSaaSAgentId)
      }

      if (payload.replace_path) {
        window.history.replaceState(null, '', payload.replace_path)
      } else if (payload.state.node === 'operator_ready' && payload.state.active_saas_agent_id) {
        window.history.replaceState(null, '', `/agents/${payload.state.active_saas_agent_id}`)
      }

      if (Array.isArray(payload.available_actions)) {
        setAvailableActions(payload.available_actions)
      }
      if (Array.isArray(payload.persistent_actions)) {
        setPersistentActions(payload.persistent_actions)
      }
      applyTurnPayload(payload)
    },
    [applySession, applyTurnPayload, enterOperatorMode, setAvailableActions, setPersistentActions],
  )

  const handleStreamEvent = useCallback(
    (eventType: EntryStreamEvent, data: Record<string, unknown>) => {
      switch (eventType) {
        case 'stream_start': {
          if (typeof data.session_id === 'string') {
            entrySessionIdRef.current = data.session_id
            setEntrySessionId(data.session_id)
          }
          break
        }
        case 'message_delta': {
          const content = data.content
          if (typeof content === 'string' && (content.length > 0 || data.is_final === true)) {
            appendAssistantDelta(content, data.is_final === true)
          }
          break
        }
        case 'stage_completed': {
          const output = (data as unknown as StageCompletedEvent).output
          if (output && Array.isArray(output.available_actions)) setAvailableActions(output.available_actions)
          if (output && Array.isArray(output.persistent_actions)) setPersistentActions(output.persistent_actions)
          if (output && Array.isArray(output.ui_artifacts)) applyArtifacts(output.ui_artifacts)
          const pathSaaSAgentId = output && typeof output.replace_path === 'string' ? saasAgentIdFromPath(output.replace_path) : null
          const stageSaaSAgentId = output && typeof output.active_saas_agent_id === 'string' ? output.active_saas_agent_id : pathSaaSAgentId
          if (stageSaaSAgentId) {
            setHandoffSaaSAgentId(stageSaaSAgentId)
            enterOperatorMode(stageSaaSAgentId)
          }
          if (output && typeof output.replace_path === 'string') {
            window.history.replaceState(null, '', output.replace_path)
          }
          break
        }
        case 'entry_turn_result': {
          if (typeof data.session_id === 'string') {
            entrySessionIdRef.current = data.session_id
            setEntrySessionId(data.session_id)
          }
          applyTurnResult(data as unknown as EntryTurnResponse)
          break
        }
        case 'setup_step': {
          const content = setupStepMessage(data)
          if (content) appendAssistant(content)
          break
        }
        case 'error': {
          appendAssistant(typeof data.message === 'string' ? data.message : 'Entry flow failed.')
          break
        }
      }
    },
    [appendAssistant, appendAssistantDelta, applyArtifacts, applyTurnResult, enterOperatorMode, setAvailableActions, setEntrySessionId, setPersistentActions],
  )

  const parseSSEChunk = useCallback(
    (text: string) => {
      const chunk = text.slice(streamCursorRef.current)
      streamCursorRef.current = text.length
      streamBufferRef.current += chunk

      const frames = streamBufferRef.current.split('\n\n')
      streamBufferRef.current = frames.pop() ?? ''

      for (const frame of frames) {
        const lines = frame.split('\n')
        let eventType: EntryStreamEvent | null = null
        const dataLines: string[] = []

        for (const line of lines) {
          if (line.startsWith(':')) continue
          if (line.startsWith('event: ')) eventType = line.slice(7).trim() as EntryStreamEvent
          else if (line.startsWith('data: ')) dataLines.push(line.slice(6))
        }

        if (!eventType || dataLines.length === 0) continue
        try {
          handleStreamEvent(eventType, JSON.parse(dataLines.join('\n')))
        } catch {
          // Ignore malformed or incomplete event payloads.
        }
      }
    },
    [handleStreamEvent],
  )

  const runTurn = useCallback(
    async ({
      userInput,
      selectedActionId,
      actionPayload,
      forceFresh,
    }: { userInput?: string; selectedActionId?: string; actionPayload?: Record<string, unknown>; forceFresh?: boolean } = {}) => {
      if (useEntryStore.getState().busy) return

      setBusy(true)
      clearAvailableActions()
      appendAssistantDelta('', false)
      streamCursorRef.current = 0
      streamBufferRef.current = ''

      const xhr = new XMLHttpRequest()
      xhrRef.current = xhr
      xhr.open('POST', '/api/entry/stream')
      xhr.withCredentials = true
      xhr.setRequestHeader('Content-Type', 'application/json')

      const token = storage.getToken()
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)

      xhr.onprogress = () => parseSSEChunk(xhr.responseText)
      xhr.onloadend = () => {
        if (xhr.responseText.length > streamCursorRef.current) parseSSEChunk(xhr.responseText)

        if (xhr.status >= 400 && !xhr.responseText.includes('event:')) {
          try {
            const body = JSON.parse(xhr.responseText) as { detail?: string }
            appendAssistantDelta(body.detail || 'Entry flow failed.', true)
          } catch {
            appendAssistantDelta('Entry flow failed.', true)
          }
        }

        finishStream()
      }
      xhr.onerror = () => {
        appendAssistantDelta('Connection failed', true)
        finishStream()
      }
      const fallbackSaaSAgentState = !forceFresh && !gs && saasAgentId
        ? {
            node: 'operator_ready',
            intent: null,
            display_name: '',
            email: '',
            saas_agent_name: '',
            saas_agent_slug: '',
            active_saas_agent_id: saasAgentId,
          }
        : undefined

      xhr.send(
        JSON.stringify({
          session_id: entrySessionIdRef.current,
          state: fallbackSaaSAgentState,
          user_input: userInput,
          selected_action_id: selectedActionId,
          action_payload: actionPayload,
          initial_intent: userInput ? undefined : initialIntent,
        }),
      )
    },
    [appendAssistantDelta, clearAvailableActions, finishStream, gs, initialIntent, parseSSEChunk, setBusy, saasAgentId],
  )

  useEffect(() => {
    return () => {
      if (xhrRef.current) {
        xhrRef.current.abort()
        xhrRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    if (authLoading || bootstrapped.current || routeSaaSAgentId) return
    bootstrapped.current = true
    void runTurn({})
  }, [authLoading, routeSaaSAgentId, runTurn])

  const handleEntrySend = useCallback(async () => {
    const value = draft.trim()
    if (!value || busy || !gs || gs.node === 'operator_ready') return
    setDraft('')
    appendUser(gs.node === 'password' ? '........' : value)
    await runTurn({ userInput: value })
  }, [appendUser, busy, draft, gs, runTurn, setDraft])

  const handleActionSelect = useCallback(async (action: EntryActionCard, payload?: Record<string, unknown>) => {
    if (busy) return
    const prompt = typeof action.payload?.prompt === 'string' ? action.payload.prompt : null
    if (prompt && !payload) {
      appendUser(prompt)
      await runTurn({ userInput: prompt, selectedActionId: action.id })
      return
    }
    await runTurn({ selectedActionId: action.id, actionPayload: payload })
  }, [appendUser, busy, runTurn])

  const handleRouteDeckActionSelect = useCallback((action: EntryActionCard) => {
    if (!showOperatorMode) {
      void handleActionSelect(action)
      return
    }
    const targetSurface = typeof action.payload?.target_surface === 'string' ? action.payload.target_surface : null
    if (targetSurface === 'connect') {
      setActiveSidebarItem('connect')
      return
    }
    if (targetSurface === 'actions') {
      setActiveSidebarItem('actions')
      setSaaSAgentActiveView('actions')
      return
    }
    if (targetSurface === 'learn') {
      setActiveSidebarItem('learn')
      return
    }
    setActiveSidebarItem('chat')
  }, [handleActionSelect, setActiveSidebarItem, setSaaSAgentActiveView, showOperatorMode])

  const handoffContext: AgentHandoffContext | null = useMemo(() => {
    if (!saasAgentId) return null
    return {
      entry_session_id: entrySessionId,
      saas_agent_id: saasAgentId,
      saas_agent_name: saasAgent?.name ?? null,
      entry_draft: gs?.entry_draft || {},
      connection_draft: gs?.connection_draft || {},
      active_connection_id: gs?.active_connection_id || null,
      recent_entry_messages: messages.slice(-8).map((message) => `${message.role}: ${message.content}`),
    }
  }, [entrySessionId, gs?.active_connection_id, gs?.connection_draft, gs?.entry_draft, messages, saasAgent?.name, saasAgentId])

  const handleAgentSend = useCallback((value: string) => {
    if (!saasAgentId || agentStreaming) return
    setOperatorError(null)
    sendAgentMessage(value, agentSessionId, 'balanced', handoffContext)
  }, [agentSessionId, agentStreaming, handoffContext, sendAgentMessage, saasAgentId])

  const handleQaResetRuntime = useCallback(async () => {
    if (xhrRef.current) {
      xhrRef.current.abort()
      xhrRef.current = null
    }
    finishStream()
    logout()
    resetEntryForQA()
    entrySessionIdRef.current = null
    setEntrySessionId(null)
    setAgentSessionId(null)
    setHandoffSaaSAgentId(null)
    setSaaSAgentId(null)
    setOperatorError(null)
    window.history.replaceState(null, '', '/')
    bootstrapped.current = true
    await new Promise((resolve) => window.setTimeout(resolve, 0))
    await runTurn({ forceFresh: true })
  }, [finishStream, logout, resetEntryForQA, runTurn, setAgentSessionId, setEntrySessionId, setSaaSAgentId])

  const handleSidebarAction = useCallback((item: OperatorSidebarItem) => {
    setActiveSidebarItem(item)
    const definition = [...entryCapabilities, ...saasAgentCapabilities].find((candidate) => candidate.id === item)
    const action = findCapabilityAction(definition, actionLookup, graphManifest)
    if (action) {
      void handleActionSelect(action)
      return
    }
    if (definition?.saasAgentView) setSaaSAgentActiveView(definition.saasAgentView)
  }, [actionLookup, graphManifest, handleActionSelect, setActiveSidebarItem, setSaaSAgentActiveView])

  const inlineArtifacts = useMemo(
    () => uiArtifacts.filter((artifact) => artifact.surface !== 'canvas'),
    [uiArtifacts],
  )

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-muted border-t-primary" />
      </div>
    )
  }

  const inputDisabled = busy || !gs
  const inputType: 'text' | 'email' | 'password' = gs?.node === 'password' ? 'password' : gs?.node === 'email' ? 'email' : 'text'
  const manifestNode = gs ? graphManifest?.nodes.find((node) => node.id === gs.node) : null
  const placeholder: Record<GatewayNode, string> = {
    bootstrap: 'Starting SaaS Agent setup...',
    intent: 'Ask about SaaStoAgent, draft setup, or sign in',
    display_name: 'Display name, or skip',
    email: 'you@example.com',
    password: 'Password',
    saas_agent_select: 'Number or new SaaS Agent name',
    saas_agent_job: 'SaaS Agent name',
    saas_agent_confirm: 'launch or rename',
    setup_intro: 'Connect an API or choose an action',
    connection_confirm: 'activate or edit setup',
    operator_ready: '',
  }

  const showCanvas = canvasOpen && Boolean(canvasArtifact)
  const mobileCanvasArtifact = canvasArtifact?.surface === 'canvas' ? canvasArtifact : null
  const showPanel = activeSidebarItem !== 'chat'
  const hasEntryStreamingBubble = allMessages.some((message) => message.role === 'assistant' && message.isStreaming)
  const showEntryThinking = !showOperatorMode && busy && !hasEntryStreamingBubble
  const userHasInteracted = allMessages.some((message) => message.role === 'user')
  const graphNeedsControls = entryGraphActive && gs?.node !== 'bootstrap' && gs?.node !== 'intent'
  const hasVisibleActions = actionLookup.length > 0
  const showActionDock = hasVisibleActions || showOperatorMode || userHasInteracted || graphNeedsControls || activeSidebarItem === 'qa'
  const workbenchGridClass = showCanvas
    ? canvasCollapsed
      ? 'max-w-7xl lg:grid-cols-[minmax(0,1fr)_3.5rem]'
      : 'max-w-7xl lg:grid-cols-[minmax(0,1fr)_minmax(22rem,0.48fr)]'
    : showPanel
      ? 'max-w-7xl lg:grid-cols-[minmax(0,1fr)_minmax(22rem,0.48fr)]'
      : 'max-w-5xl'

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur dark:border-white/10 dark:bg-[#050506]/90">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div>
            <div className="text-sm font-semibold tracking-tight text-foreground">{PRODUCT_NAME}</div>
            <div className="hidden text-xs text-muted-foreground sm:block">
              {showOperatorMode
                ? saasAgentDisplayName
                  ? `${OPERATOR_NAME} - ${saasAgentDisplayName}`
                  : OPERATOR_NAME
                : `${OPERATOR_NAME} - entry, setup, and SaaS Agent chat`}
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <ThemeToggleButton />
            {user?.email && <span className="hidden text-muted-foreground sm:inline">{user.email}</span>}
            {user && (
              <button type="button" onClick={logout} className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90">
                Log out
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="md:flex">
        <CapabilityRail
          capabilities={capabilities}
          activeItem={activeSidebarItem}
          runtime={capabilityRuntime}
          onSelect={handleSidebarAction}
        />

        <main className="min-w-0 flex-1">
          <div className={cn('mx-auto grid gap-4 px-3 py-4 sm:px-6 lg:px-8', workbenchGridClass)}>
            <div className={cn((showCanvas || showPanel) && 'lg:col-span-2')}>
              <OperatorStatusStrip
                mode={visibleMode}
                saasAgent={saasAgent}
                saasAgentId={saasAgentId}
                stats={stats}
                graphNode={activeGraphNode}
                graphManifest={activeGraphManifest}
                agentContext={showOperatorMode ? saasAgentRouteDeck?.context : null}
                readiness={readiness}
                busy={showOperatorMode ? agentStreaming : busy}
              />
            </div>
            <div className={cn((showCanvas || showPanel) && 'lg:col-span-2')}>
              <RouteDeckNavWidget
                graphNode={activeGraphNode}
                graphManifest={activeGraphManifest}
                routeDeckSnapshot={activeRouteDeckSnapshot}
                selectedDebugNode={selectedDebugNode}
                onSelectedDebugNodeChange={setSelectedDebugNode}
                onActionSelect={handleRouteDeckActionSelect}
                runId={runId}
                sessionId={showOperatorMode ? agentSessionId : entrySessionId}
              />
            </div>
            <section className="surface-card min-w-0 overflow-hidden rounded-lg">
              <div ref={scrollRef} className="h-[clamp(14rem,calc(100vh-25rem),34rem)] overflow-y-auto py-4">
                {allMessages.length === 0 ? (
                  <div className="flex min-h-[18rem] items-center justify-center text-slate-400 dark:text-slate-500">
                    {showEntryThinking ? (
                      <div className="rounded-2xl bg-muted px-4 py-2.5 text-foreground">
                        <ThinkingIndicator />
                      </div>
                    ) : (
                      <span className="text-sm">{showOperatorMode ? 'Corpus is ready for direction.' : 'Ask a question or describe the API workflow to set up.'}</span>
                    )}
                  </div>
                ) : (
                  <>
                    {allMessages.map((message) => (
                      <MessageBubble key={message.id} message={message} onFollowUp={showOperatorMode ? setInjectText : undefined} />
                    ))}
                    {showEntryThinking && (
                      <div className="flex gap-3 px-4 py-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                          <Bot className="h-4 w-4" />
                        </div>
                        <div className="max-w-[75%] rounded-2xl bg-muted px-4 py-2.5 text-foreground">
                          <ThinkingIndicator />
                        </div>
                      </div>
                    )}
                    {!showOperatorMode && inlineArtifacts.length > 0 && (
                      <div className={cn('space-y-3 px-4 pb-2 pt-1 sm:px-6', showCanvas && 'lg:hidden')}>
                        {inlineArtifacts.map((artifact) => (
                          <EntryArtifactRenderer key={artifact.id} artifact={artifact} compact />
                        ))}
                      </div>
                    )}
                    {!showOperatorMode && (
                      <EntryCanvasLauncher artifacts={canvasArtifacts} activeArtifactId={canvasOpen ? canvasArtifactId : null} onOpen={openCanvasArtifact} />
                    )}
                    {mobileCanvasArtifact && (
                      <div className="space-y-3 px-4 pb-2 pt-1 sm:px-6 lg:hidden">
                        <EntryArtifactRenderer artifact={mobileCanvasArtifact} compact />
                      </div>
                    )}
                    {!showOperatorMode && (
                      <EntryActionCards actions={contextualActions} busy={busy} onSelect={(action, payload) => { void handleActionSelect(action, payload) }} />
                    )}
                    {showOperatorMode && agentMessages.length === 0 && !agentStreaming && (
                      <div className="flex flex-wrap gap-2 px-4 pb-2 pt-1 sm:px-6">
                        {agentStarterPrompts.map((prompt) => (
                          <button key={prompt} type="button" onClick={() => handleAgentSend(prompt)} className="surface-outline-button rounded-full px-3 py-1.5 text-xs">
                            {prompt}
                          </button>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="border-t border-slate-200 bg-white px-4 py-4 dark:border-white/10 dark:bg-[#09090b] sm:px-6">
                {showActionDock && (
                  <ActionDock
                    primaryAction={nextBestAction}
                    actions={persistentActions}
                    busy={busy}
                    onSelect={(action) => { void handleActionSelect(action) }}
                  />
                )}
                {showOperatorMode ? (
                  <>
                    {operatorError && (
                      <div className="mb-2 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
                        {operatorError}
                      </div>
                    )}
                    {uploadFile.isPending && <div className="mb-2 text-xs text-slate-500">Uploading...</div>}
                    <ChatInput
                      onSend={handleAgentSend}
                      onFileUpload={user ? (file) => uploadFile.mutate(file) : undefined}
                      disabled={agentStreaming || !saasAgentId}
                      placeholder="Describe what you need done"
                      injectText={injectText}
                    />
                  </>
                ) : (
                  <CommandComposer
                    value={draft}
                    onChange={setDraft}
                    onSend={() => { void handleEntrySend() }}
                    placeholder={manifestNode?.prompt_placeholder || (gs ? placeholder[gs.node] : 'Starting SaaS Agent setup...')}
                    disabled={inputDisabled}
                    inputType={inputType}
                  />
                )}
              </div>
              <EvidenceDrawer
                open={evidenceOpen}
                onToggle={() => setEvidenceOpen((value) => !value)}
                mode={visibleMode}
                graphNode={activeGraphNode}
                runId={runId}
                sessionId={showOperatorMode ? agentSessionId : entrySessionId}
                readiness={readiness}
                uiArtifacts={uiArtifacts}
                autonomyLevel={autonomyLevel}
                onAutonomyChange={setAutonomyLevel}
              />
            </section>

            {showCanvas ? (
              <EntryCanvasShell artifact={canvasArtifact} collapsed={canvasCollapsed} onToggleCollapsed={toggleCanvasCollapsed} onClose={closeCanvas} />
            ) : (
              showPanel && (
                <UnifiedSidePanel
                  item={activeSidebarItem}
                  mode={showOperatorMode ? 'operator' : 'entry'}
                  saasAgent={saasAgent}
                  stats={stats}
                  uiArtifacts={uiArtifacts}
                  capability={activeCapability}
                  agentContext={showOperatorMode ? saasAgentRouteDeck?.context : null}
                  onOpenCanvas={openCanvasArtifact}
                  onClose={() => setActiveSidebarItem('chat')}
                  onQaResetRuntime={handleQaResetRuntime}
                />
              )
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

function UnifiedSidePanel({
  item,
  mode,
  saasAgent,
  stats,
  uiArtifacts,
  capability,
  agentContext,
  onOpenCanvas,
  onClose,
  onQaResetRuntime,
}: {
  item: OperatorSidebarItem
  mode: OperatorExperienceMode
  saasAgent?: SaaSAgent
  stats?: SaaSAgentStats
  uiArtifacts: EntryUIArtifact[]
  capability?: OperatorCapabilityDefinition
  agentContext?: SaaSAgentRouteDeckContext | null
  onOpenCanvas: (artifactId: string) => void
  onClose: () => void
  onQaResetRuntime: () => Promise<void>
}) {
  const qaHostedView = useSaaSAgentStore((state) => state.activeView)
  let content: JSX.Element
  if (item === 'qa') {
    const hostedContent = mode === 'operator' ? renderSaaSAgentPanel(qaHostedView, saasAgent, stats) : null
    content = (
      <div className="space-y-4">
        <QAAgentPanel onResetRuntime={onQaResetRuntime} />
        {hostedContent && (
            <div data-testid="qa-saas-agent-view-host">
            {hostedContent}
          </div>
        )}
      </div>
    )
  } else if (mode === 'operator') {
    content = renderSaaSAgentPanel(item, saasAgent, stats)
  } else {
    const artifact = item === 'learn'
      ? uiArtifacts.find((candidate) => candidate.widget_type === 'platform_overview')
      : item === 'setup'
        ? uiArtifacts.find((candidate) => candidate.widget_type === 'setup_draft_summary' || candidate.widget_type === 'onboarding_checklist')
        : null
    content = artifact
      ? <EntryArtifactRenderer artifact={artifact} />
      : <PanelEmpty title={capability?.label || 'SaaS Agent context'} body={capability?.emptyState || 'Ask in chat or choose an action to populate this panel.'} />
  }

  return (
    <ContextLens
      title={capability?.label || 'SaaS Agent context'}
      capability={capability}
      uiArtifacts={uiArtifacts}
      agentContext={agentContext}
      onOpenCanvas={onOpenCanvas}
      onClose={onClose}
    >
      {content}
    </ContextLens>
  )
}

function renderSaaSAgentPanel(item: OperatorSidebarItem | SaaSAgentView, saasAgent?: SaaSAgent, stats?: SaaSAgentStats): JSX.Element {
  if (item === 'connect') return <ConnectSetupView saasAgent={saasAgent} stats={stats} />
  if (item === 'learn') return <LearningPanel />
  if (item === 'attachments') return <AttachmentsPanel />
  if (item === 'admin') return <AdminPanel saasAgent={saasAgent} />
  if (item === 'entities') return <EntitiesCanvas />
  if (item === 'actions') return <ActionsCanvas />
  if (item === 'chat' || item === 'qa') return <></>
  return <PanelEmpty title="SaaS Agent panel" body="Select a SaaS Agent surface from the rail." />
}

function PanelEmpty({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-200 p-4 text-sm dark:border-white/10">
      <div className="font-semibold text-slate-950 dark:text-white">{title}</div>
      <p className="mt-2 text-slate-500 dark:text-slate-400">{body}</p>
    </div>
  )
}
