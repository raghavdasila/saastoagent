import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Bot,
} from 'lucide-react'

import { AdminPanel } from '@/components/agent/AdminPanel'
import { AttachmentsPanel } from '@/components/agent/AttachmentsPanel'
import { ChatInput } from '@/components/agent/ChatInput'
import { CommandComposer } from '@/components/agent/CommandComposer'
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
import { ThemeToggleButton } from '@/components/theme/ThemeToggleButton'
import { ConnectSetupView } from '@/components/workspace/ConnectSetupView'
import { LockedCanvasView } from '@/components/workspace/LockedCanvasView'
import { useAuth } from '@/context/AuthContext'
import { useSSEChat } from '@/hooks/useSSEChat'
import { api, ApiError } from '@/lib/api'
import { cn } from '@/lib/cn'
import { formatWorkspaceDisplayName, OPERATOR_NAME, PRODUCT_NAME } from '@/lib/entryGraph'
import { entryCapabilities, findCapabilityAction, pickNextBestAction, workspaceCapabilities, type OperatorCapabilityDefinition } from '@/lib/operatorExperience'
import { storage } from '@/lib/storage'
import { useAuthStore } from '@/stores/authStore'
import { useEntryStore } from '@/stores/entryStore'
import { useWorkspaceStore, type WorkspaceView } from '@/stores/workspaceStore'
import type { AgentDocument, AgentHandoffContext } from '@/types/agent'
import type { Workspace, WorkspaceStats } from '@/types/domain'
import type {
  AuthIntent,
  EntryActionCard,
  EntryPersistentActionsResponse,
  EntryTurnResponse,
  EntryUIArtifact,
  GatewayNode,
  OperatorExperienceMode,
  OperatorSidebarItem,
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
  initialWorkspaceId?: string | null
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

function workspaceIdFromPath(path?: string | null): string | null {
  if (!path) return null
  const match = /^\/w\/([^/?#]+)/.exec(path)
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

export function OperatorGateway({ initialIntent, initialWorkspaceId }: OperatorGatewayProps) {
  const { isLoading: authLoading, user, logout } = useAuth()
  const applySession = useAuthStore((state) => state.applySession)

  const gs = useEntryStore((state) => state.graphState)
  const mode = useEntryStore((state) => state.mode)
  const activeWorkspaceId = useEntryStore((state) => state.activeWorkspaceId)
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

  const setWorkspaceId = useWorkspaceStore((state) => state.setWorkspaceId)
  const setWorkspaceActiveView = useWorkspaceStore((state) => state.setActiveView)

  const queryClient = useQueryClient()
  const [operatorError, setOperatorError] = useState<string | null>(null)
  const [injectText, setInjectText] = useState('')
  const [handoffWorkspaceId, setHandoffWorkspaceId] = useState<string | null>(initialWorkspaceId ?? null)
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [autonomyLevel, setAutonomyLevel] = useState<AutonomyLevel>('ask')

  const scrollRef = useRef<HTMLDivElement>(null)
  const bootstrapped = useRef(false)
  const xhrRef = useRef<XMLHttpRequest | null>(null)
  const streamCursorRef = useRef(0)
  const streamBufferRef = useRef('')
  const entrySessionIdRef = useRef<string | null>(entrySessionId)
  const routeWorkspaceId = useMemo(
    () => initialWorkspaceId || workspaceIdFromPath(window.location.pathname),
    [initialWorkspaceId],
  )

  const graphWorkspaceId = typeof gs?.active_workspace_id === 'string' ? gs.active_workspace_id : null
  const workspaceId = handoffWorkspaceId || activeWorkspaceId || graphWorkspaceId || routeWorkspaceId || null
  const entryGraphActive = isEntryGraphActive(gs?.node)
  const showOperatorMode = Boolean(workspaceId) && !entryGraphActive && (mode === 'operator' || Boolean(handoffWorkspaceId) || Boolean(graphWorkspaceId) || Boolean(routeWorkspaceId))
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
    workspaceId,
    onError: setOperatorError,
  })

  const { data: workspace } = useQuery({
    queryKey: ['workspace', workspaceId],
    queryFn: () => api.get<Workspace>(`/workspaces/${workspaceId}`),
    enabled: !!workspaceId && !!user,
  })

  const { data: stats } = useQuery({
    queryKey: ['workspace-stats', workspaceId],
    queryFn: () => api.get<WorkspaceStats>(`/workspaces/${workspaceId}/stats`),
    enabled: !!workspaceId && !!user,
  })

  const uploadFile = useMutation({
    mutationFn: (file: File) => api.upload<AgentDocument>(`/workspaces/${workspaceId}/agent/documents`, file),
    onSuccess: (doc) => {
      queryClient.invalidateQueries({ queryKey: ['agent-documents', workspaceId] })
      setInjectText(`Tell me what's in ${doc.original_name}`)
    },
    onError: (error) => {
      setOperatorError(error instanceof ApiError ? error.message : 'Upload failed')
    },
  })
  const { data: persistentActionsData } = useQuery<EntryPersistentActionsResponse>({
    queryKey: ['entry-persistent-actions', Boolean(user), workspaceId],
    queryFn: () => api.get(`/entry/persistent-actions${workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : ''}`),
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
  const capabilities = visibleMode === 'operator' ? workspaceCapabilities : entryCapabilities
  const activeCapability = capabilities.find((candidate) => candidate.id === activeSidebarItem)
  const capabilityRuntime = useMemo(
    () => ({
      busy: showOperatorMode ? agentStreaming : busy,
      hasWorkspace: Boolean(workspaceId),
      isAuthenticated: Boolean(user),
      stats,
      operatorError,
    }),
    [agentStreaming, busy, operatorError, stats, user, workspaceId, showOperatorMode],
  )
  const readiness = useMemo(
    () => buildReadiness({
      mode: visibleMode,
      workspaceId,
      stats,
      isAuthenticated: Boolean(user),
      operatorError,
    }),
    [operatorError, stats, user, visibleMode, workspaceId],
  )
  const nextBestAction = useMemo(
    () => pickNextBestAction(actionLookup, visibleMode),
    [actionLookup, visibleMode],
  )
  const workspaceDisplayName = useMemo(
    () => formatWorkspaceDisplayName(workspace?.name),
    [workspace?.name],
  )

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
    if (routeWorkspaceId) {
      setHandoffWorkspaceId(routeWorkspaceId)
      enterOperatorMode(routeWorkspaceId)
    }
  }, [enterOperatorMode, routeWorkspaceId])

  useEffect(() => {
    setWorkspaceId(workspaceId)
  }, [setWorkspaceId, workspaceId])

  useEffect(() => {
    if (liveAgentSessionId) {
      setAgentSessionId(liveAgentSessionId)
    }
  }, [liveAgentSessionId, setAgentSessionId])

  const finishStream = useCallback(() => {
    setBusy(false)
    xhrRef.current = null
    streamCursorRef.current = 0
    streamBufferRef.current = ''
  }, [setBusy])

  const applyTurnResult = useCallback(
    (payload: EntryTurnResponse) => {
      if (payload.session) {
        applySession(payload.session.user, payload.session.access_token)
      }

      const pathWorkspaceId = workspaceIdFromPath(payload.replace_path)
      const resultWorkspaceId = payload.state.active_workspace_id || pathWorkspaceId
      if (resultWorkspaceId) {
        setHandoffWorkspaceId(resultWorkspaceId)
        enterOperatorMode(resultWorkspaceId)
      }

      if (payload.replace_path) {
        window.history.replaceState(null, '', payload.replace_path)
      } else if (payload.state.node === 'operator_ready' && payload.state.active_workspace_id) {
        window.history.replaceState(null, '', `/w/${payload.state.active_workspace_id}`)
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
          if (typeof content === 'string' && content.length > 0) appendAssistant(content)
          break
        }
        case 'stage_completed': {
          const output = (data as unknown as StageCompletedEvent).output
          if (output && Array.isArray(output.available_actions)) setAvailableActions(output.available_actions)
          if (output && Array.isArray(output.persistent_actions)) setPersistentActions(output.persistent_actions)
          if (output && Array.isArray(output.ui_artifacts)) applyArtifacts(output.ui_artifacts)
          const pathWorkspaceId = output && typeof output.replace_path === 'string' ? workspaceIdFromPath(output.replace_path) : null
          const stageWorkspaceId = output && typeof output.active_workspace_id === 'string' ? output.active_workspace_id : pathWorkspaceId
          if (stageWorkspaceId) {
            setHandoffWorkspaceId(stageWorkspaceId)
            enterOperatorMode(stageWorkspaceId)
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
    [appendAssistant, applyArtifacts, applyTurnResult, enterOperatorMode, setAvailableActions, setEntrySessionId, setPersistentActions],
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
    async ({ userInput, selectedActionId, actionPayload }: { userInput?: string; selectedActionId?: string; actionPayload?: Record<string, unknown> } = {}) => {
      if (busy) return

      setBusy(true)
      clearAvailableActions()
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
            appendAssistant(body.detail || 'Entry flow failed.')
          } catch {
            appendAssistant('Entry flow failed.')
          }
        }

        finishStream()
      }
      xhr.onerror = () => {
        appendAssistant('Connection failed')
        finishStream()
      }
      const fallbackWorkspaceState = !gs && workspaceId
        ? {
            node: 'operator_ready',
            intent: null,
            display_name: '',
            email: '',
            workspace_name: '',
            workspace_slug: '',
            active_workspace_id: workspaceId,
          }
        : undefined

      xhr.send(
        JSON.stringify({
          session_id: entrySessionIdRef.current,
          state: fallbackWorkspaceState,
          user_input: userInput,
          selected_action_id: selectedActionId,
          action_payload: actionPayload,
          initial_intent: userInput ? undefined : initialIntent,
        }),
      )
    },
    [appendAssistant, busy, clearAvailableActions, finishStream, gs, initialIntent, parseSSEChunk, setBusy, workspaceId],
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
    if (authLoading || bootstrapped.current || routeWorkspaceId) return
    bootstrapped.current = true
    void runTurn({})
  }, [authLoading, routeWorkspaceId, runTurn])

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

  const handoffContext: AgentHandoffContext | null = useMemo(() => {
    if (!workspaceId) return null
    return {
      entry_session_id: entrySessionId,
      workspace_id: workspaceId,
      workspace_name: workspace?.name ?? null,
      entry_draft: gs?.entry_draft || {},
      connection_draft: gs?.connection_draft || {},
      active_connection_id: gs?.active_connection_id || null,
      recent_entry_messages: messages.slice(-8).map((message) => `${message.role}: ${message.content}`),
    }
  }, [entrySessionId, gs?.active_connection_id, gs?.connection_draft, gs?.entry_draft, messages, workspace?.name, workspaceId])

  const handleAgentSend = useCallback((value: string) => {
    if (!workspaceId || agentStreaming) return
    setOperatorError(null)
    sendAgentMessage(value, agentSessionId, 'balanced', handoffContext)
  }, [agentSessionId, agentStreaming, handoffContext, sendAgentMessage, workspaceId])

  const handleSidebarAction = useCallback((item: OperatorSidebarItem) => {
    setActiveSidebarItem(item)
    const definition = [...entryCapabilities, ...workspaceCapabilities].find((candidate) => candidate.id === item)
    const action = findCapabilityAction(definition, actionLookup, graphManifest)
    if (action) {
      void handleActionSelect(action)
      return
    }
    if (definition?.workspaceView) setWorkspaceActiveView(definition.workspaceView)
  }, [actionLookup, graphManifest, handleActionSelect, setActiveSidebarItem, setWorkspaceActiveView])

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
    bootstrap: 'Starting workspace setup...',
    intent: 'Ask about SaaStoAgent, draft setup, or sign in',
    display_name: 'Display name, or skip',
    email: 'you@example.com',
    password: 'Password',
    workspace_select: 'Number or new job description',
    workspace_job: 'What SaaS job should this workspace handle?',
    workspace_confirm: 'launch or rename',
    setup_intro: 'Connect an API or choose an action',
    connection_confirm: 'activate or edit setup',
    operator_ready: '',
  }

  const showCanvas = canvasOpen && Boolean(canvasArtifact)
  const mobileCanvasArtifact = canvasArtifact?.surface === 'canvas' ? canvasArtifact : null
  const showPanel = activeSidebarItem !== 'chat'
  const showEntryThinking = !showOperatorMode && busy

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur dark:border-white/10 dark:bg-[#050506]/90">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div>
            <div className="text-sm font-semibold tracking-tight text-foreground">{PRODUCT_NAME}</div>
            <div className="hidden text-xs text-muted-foreground sm:block">
              {showOperatorMode
                ? workspaceDisplayName
                  ? `${OPERATOR_NAME} Â· ${workspaceDisplayName}`
                  : OPERATOR_NAME
                : `${OPERATOR_NAME} Â· entry, setup, and workspace chat`}
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
          <div className={cn('mx-auto grid gap-4 px-3 py-4 sm:px-6 lg:px-8', showCanvas || showPanel ? 'max-w-7xl lg:grid-cols-[minmax(0,1fr)_minmax(24rem,0.52fr)]' : 'max-w-5xl')}>
            <div className={cn((showCanvas || showPanel) && 'lg:col-span-2')}>
              <OperatorStatusStrip
                mode={visibleMode}
                workspace={workspace}
                workspaceId={workspaceId}
                stats={stats}
                graphNode={gs?.node}
                graphManifest={graphManifest}
                readiness={readiness}
                busy={showOperatorMode ? agentStreaming : busy}
              />
            </div>
            <div className={cn((showCanvas || showPanel) && 'lg:col-span-2')}>
              <RouteDeckNavWidget
                graphNode={gs?.node}
                graphManifest={graphManifest}
                routeDeckSnapshot={routeDeckSnapshot}
                selectedDebugNode={selectedDebugNode}
                onSelectedDebugNodeChange={setSelectedDebugNode}
                runId={runId}
                sessionId={showOperatorMode ? agentSessionId : entrySessionId}
              />
            </div>
            <section className="surface-card min-w-0 overflow-hidden rounded-2xl">
              <div ref={scrollRef} className="h-[clamp(14rem,calc(100vh-25rem),34rem)] overflow-y-auto py-4">
                {allMessages.length === 0 ? (
                  <div className="flex min-h-[18rem] items-center justify-center text-slate-400 dark:text-slate-500">
                    {showEntryThinking ? (
                      <div className="rounded-2xl bg-muted px-4 py-2.5 text-foreground">
                        <ThinkingIndicator />
                      </div>
                    ) : (
                      <span className="text-sm">{showOperatorMode ? 'Corpus is ready.' : 'Starting workspace setup...'}</span>
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
                <ActionDock
                  primaryAction={nextBestAction}
                  actions={persistentActions}
                  busy={busy}
                  onSelect={(action) => { void handleActionSelect(action) }}
                />
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
                      disabled={agentStreaming || !workspaceId}
                      placeholder="Describe what you need done"
                      injectText={injectText}
                    />
                  </>
                ) : (
                  <CommandComposer
                    value={draft}
                    onChange={setDraft}
                    onSend={() => { void handleEntrySend() }}
                    placeholder={manifestNode?.prompt_placeholder || (gs ? placeholder[gs.node] : 'Starting workspace setup...')}
                    disabled={inputDisabled}
                    inputType={inputType}
                  />
                )}
              </div>
              <EvidenceDrawer
                open={evidenceOpen}
                onToggle={() => setEvidenceOpen((value) => !value)}
                mode={visibleMode}
                graphNode={gs?.node}
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
                  workspace={workspace}
                  stats={stats}
                  uiArtifacts={uiArtifacts}
                  capability={activeCapability}
                  onOpenCanvas={openCanvasArtifact}
                  onClose={() => setActiveSidebarItem('chat')}
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
  workspace,
  stats,
  uiArtifacts,
  capability,
  onOpenCanvas,
  onClose,
}: {
  item: OperatorSidebarItem
  mode: OperatorExperienceMode
  workspace?: Workspace
  stats?: WorkspaceStats
  uiArtifacts: EntryUIArtifact[]
  capability?: OperatorCapabilityDefinition
  onOpenCanvas: (artifactId: string) => void
  onClose: () => void
}) {
  let content: JSX.Element
  if (mode === 'operator') {
    if (item === 'connect') content = <ConnectSetupView workspace={workspace} stats={stats} />
    else if (item === 'attachments') content = <AttachmentsPanel />
    else if (item === 'admin') content = <AdminPanel workspace={workspace} />
    else if (item === 'entities' || item === 'actions' || item === 'qa') content = <LockedCanvasView view={item as WorkspaceView} />
    else content = <PanelEmpty title="Workspace panel" body="Select a workspace surface from the rail." />
  } else {
    const artifact = item === 'learn'
      ? uiArtifacts.find((candidate) => candidate.widget_type === 'platform_overview')
      : item === 'setup'
        ? uiArtifacts.find((candidate) => candidate.widget_type === 'setup_draft_summary' || candidate.widget_type === 'onboarding_checklist')
        : null
    content = artifact
      ? <EntryArtifactRenderer artifact={artifact} />
      : <PanelEmpty title={capability?.label || 'Workspace context'} body={capability?.emptyState || 'Ask in chat or choose an action to populate this panel.'} />
  }

  return (
    <ContextLens
      title={capability?.label || 'Workspace context'}
      capability={capability}
      uiArtifacts={uiArtifacts}
      onOpenCanvas={onOpenCanvas}
      onClose={onClose}
    >
      {content}
    </ContextLens>
  )
}

function PanelEmpty({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-200 p-4 text-sm dark:border-white/10">
      <div className="font-semibold text-slate-950 dark:text-white">{title}</div>
      <p className="mt-2 text-slate-500 dark:text-slate-400">{body}</p>
    </div>
  )
}
