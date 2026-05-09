import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Bot,
  Brain,
  Database,
  FlaskConical,
  GitBranch,
  LogIn,
  MessageSquareText,
  Paperclip,
  PanelRightOpen,
  PlugZap,
  Shield,
  UserPlus,
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
import { ThemeToggleButton } from '@/components/theme/ThemeToggleButton'
import { ConnectSetupView } from '@/components/workspace/ConnectSetupView'
import { LockedCanvasView } from '@/components/workspace/LockedCanvasView'
import { useAuth } from '@/context/AuthContext'
import { useSSEChat } from '@/hooks/useSSEChat'
import { api, ApiError } from '@/lib/api'
import { cn } from '@/lib/cn'
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

const entrySidebarItems: Array<{
  id: OperatorSidebarItem
  label: string
  description: string
  icon: typeof MessageSquareText
  actionId?: string
}> = [
  { id: 'chat', label: 'Chat', description: 'Ask or continue setup', icon: MessageSquareText },
  { id: 'learn', label: 'Learn', description: 'Platform overview', icon: Brain, actionId: 'entry.learn.platform' },
  { id: 'setup', label: 'Setup Draft', description: 'Prepare API setup', icon: Database, actionId: 'entry.learn.setup' },
  { id: 'signin', label: 'Sign In', description: 'Existing account', icon: LogIn, actionId: 'intent.sign_in' },
  { id: 'register', label: 'Create Account', description: 'New account', icon: UserPlus, actionId: 'intent.register' },
]

const workspaceSidebarItems: Array<{
  id: OperatorSidebarItem
  workspaceView?: WorkspaceView
  label: string
  description: string
  icon: typeof MessageSquareText
  enabled: boolean
}> = [
  { id: 'chat', workspaceView: 'chat', label: 'Operator Chat', description: 'Primary workspace chat', icon: MessageSquareText, enabled: true },
  { id: 'connect', workspaceView: 'connect', label: 'Connections', description: 'REST setup and activation', icon: PlugZap, enabled: true },
  { id: 'attachments', workspaceView: 'attachments', label: 'Knowledge Base', description: 'Documents and sources', icon: Paperclip, enabled: true },
  { id: 'admin', workspaceView: 'admin', label: 'Sessions', description: 'Memory and admin', icon: Shield, enabled: true },
  { id: 'entities', workspaceView: 'entities', label: 'Entities', description: 'Unlocks after runtime wiring', icon: GitBranch, enabled: false },
  { id: 'actions', workspaceView: 'actions', label: 'Actions', description: 'Unlocks after tool binding', icon: Bot, enabled: false },
  { id: 'qa', workspaceView: 'qa', label: 'QA', description: 'Unlocks after execution', icon: FlaskConical, enabled: false },
]

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

  const setWorkspaceId = useWorkspaceStore((state) => state.setWorkspaceId)
  const setWorkspaceActiveView = useWorkspaceStore((state) => state.setActiveView)

  const queryClient = useQueryClient()
  const [operatorError, setOperatorError] = useState<string | null>(null)
  const [injectText, setInjectText] = useState('')
  const [handoffWorkspaceId, setHandoffWorkspaceId] = useState<string | null>(initialWorkspaceId ?? null)

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

      xhr.send(
        JSON.stringify({
          session_id: entrySessionIdRef.current,
          user_input: userInput,
          selected_action_id: selectedActionId,
          action_payload: actionPayload,
          initial_intent: userInput ? undefined : initialIntent,
        }),
      )
    },
    [appendAssistant, busy, clearAvailableActions, finishStream, initialIntent, parseSSEChunk, setBusy],
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
    const entryItem = entrySidebarItems.find((candidate) => candidate.id === item)
    if (entryItem?.actionId) {
      const action = actionLookup.find((candidate) => candidate.id === entryItem.actionId)
      if (action) void handleActionSelect(action)
      return
    }
    const workspaceItem = workspaceSidebarItems.find((candidate) => candidate.id === item)
    if (workspaceItem?.workspaceView) setWorkspaceActiveView(workspaceItem.workspaceView)
  }, [actionLookup, handleActionSelect, setActiveSidebarItem, setWorkspaceActiveView])

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
  const placeholder: Record<GatewayNode, string> = {
    intent: 'Ask about SaaStoAgent, draft setup, or sign in',
    display_name: 'Display name, or skip',
    email: 'you@example.com',
    password: 'Password',
    workspace_select: 'Number or new job description',
    workspace_job: 'What SaaS job should this operator own?',
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
            <div className="text-sm font-semibold tracking-tight text-foreground">SaaSToAgent Operator</div>
            <div className="hidden text-xs text-muted-foreground sm:block">
              {showOperatorMode ? workspace?.name || 'Workspace operator' : 'Entry, setup, and operator chat'}
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
        <UnifiedSidebar
          mode={showOperatorMode ? 'operator' : 'entry'}
          activeItem={activeSidebarItem}
          hasWorkspace={Boolean(workspaceId)}
          isAuthenticated={Boolean(user)}
          onSelect={handleSidebarAction}
        />

        <main className="min-w-0 flex-1">
          <div className={cn('mx-auto grid gap-4 px-3 py-4 sm:px-6 lg:px-8', showCanvas || showPanel ? 'max-w-7xl lg:grid-cols-[minmax(0,1fr)_minmax(24rem,0.52fr)]' : 'max-w-5xl')}>
            <section className="surface-card min-w-0 overflow-hidden rounded-2xl">
              <div ref={scrollRef} className="min-h-[calc(100vh-14rem)] max-h-[calc(100vh-11rem)] overflow-y-auto py-4">
                {allMessages.length === 0 ? (
                  <div className="flex min-h-[18rem] items-center justify-center text-slate-400 dark:text-slate-500">
                    {showEntryThinking ? (
                      <div className="rounded-2xl bg-muted px-4 py-2.5 text-foreground">
                        <ThinkingIndicator />
                      </div>
                    ) : (
                      <span className="text-sm">{showOperatorMode ? 'Ready for operator chat.' : 'Starting operator flow...'}</span>
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
                <PersistentActionRail
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
                      placeholder="Tell the operator what you need done"
                      injectText={injectText}
                    />
                  </>
                ) : (
                  <CommandComposer
                    value={draft}
                    onChange={setDraft}
                    onSend={() => { void handleEntrySend() }}
                    placeholder={gs ? placeholder[gs.node] : 'Starting operator flow...'}
                    disabled={inputDisabled}
                    inputType={inputType}
                  />
                )}
              </div>
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

function UnifiedSidebar({
  mode,
  activeItem,
  hasWorkspace,
  isAuthenticated,
  onSelect,
}: {
  mode: OperatorExperienceMode
  activeItem: OperatorSidebarItem
  hasWorkspace: boolean
  isAuthenticated: boolean
  onSelect: (item: OperatorSidebarItem) => void
}) {
  const items = mode === 'operator' ? workspaceSidebarItems : entrySidebarItems
  return (
    <aside className="border-b border-slate-200 bg-white md:min-h-[calc(100vh-3.5rem)] md:w-20 md:shrink-0 md:border-b-0 md:border-r dark:border-white/10 dark:bg-[#09090b]">
      <div className="hidden border-b border-slate-200 px-3 py-4 md:flex md:justify-center dark:border-white/10">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-sky-200 bg-sky-50 text-xs font-bold tracking-[0.16em] text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200">
          STA
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto px-2 py-2 md:flex-col md:items-center md:gap-2 md:px-0 md:py-4" aria-label="Operator navigation">
        {items.map((item) => {
          const Icon = item.icon
          const isActive = item.id === activeItem
          const enabled = mode === 'entry' ? true : item.enabled && hasWorkspace && (isAuthenticated || item.id === 'chat')
          return (
            <button
              key={item.id}
              type="button"
              disabled={!enabled}
              onClick={() => onSelect(item.id)}
              title={enabled ? item.label : `${item.label} - ${item.description}`}
              className={cn(
                'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border transition',
                isActive
                  ? 'border-slate-900 bg-slate-950 text-white shadow-sm dark:border-white dark:bg-white dark:text-slate-950'
                  : 'border-transparent text-slate-600 hover:border-slate-200 hover:bg-slate-50 dark:text-slate-400 dark:hover:border-white/10 dark:hover:bg-white/[0.06]',
                enabled ? 'cursor-pointer' : 'cursor-not-allowed opacity-50',
              )}
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
              <span className="sr-only">{item.label}</span>
            </button>
          )
        })}
      </nav>
    </aside>
  )
}

function UnifiedSidePanel({
  item,
  mode,
  workspace,
  stats,
  uiArtifacts,
  onOpenCanvas,
  onClose,
}: {
  item: OperatorSidebarItem
  mode: OperatorExperienceMode
  workspace?: Workspace
  stats?: WorkspaceStats
  uiArtifacts: EntryUIArtifact[]
  onOpenCanvas: (artifactId: string) => void
  onClose: () => void
}) {
  let content: JSX.Element
  if (mode === 'operator') {
    if (item === 'connect') content = <ConnectSetupView workspace={workspace} stats={stats} />
    else if (item === 'attachments') content = <AttachmentsPanel />
    else if (item === 'admin') content = <AdminPanel workspace={workspace} />
    else if (item === 'entities' || item === 'actions' || item === 'qa') content = <LockedCanvasView view={item as WorkspaceView} />
    else content = <PanelEmpty title="Operator panel" body="Select a workspace surface from the sidebar." />
  } else {
    const artifact = item === 'learn'
      ? uiArtifacts.find((candidate) => candidate.widget_type === 'platform_overview')
      : uiArtifacts.find((candidate) => candidate.widget_type === 'setup_draft_summary' || candidate.widget_type === 'onboarding_checklist')
    content = artifact
      ? <EntryArtifactRenderer artifact={artifact} />
      : <PanelEmpty title={item === 'learn' ? 'Platform overview' : 'Setup draft'} body="Ask in chat or choose an action to populate this panel." />
  }

  return (
    <aside className="operator-side-panel flex min-w-0 flex-col rounded-2xl border border-slate-200 bg-white p-3 shadow-2xl dark:border-white/10 dark:bg-[#09090b] lg:shadow-sm">
      <div className="mb-3 flex shrink-0 items-center justify-between gap-3">
        <button type="button" onClick={onClose} className="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5">
          Close
        </button>
        {uiArtifacts.some((artifact) => artifact.surface === 'canvas' || artifact.surface === 'both') && (
          <button
            type="button"
            onClick={() => {
              const artifact = uiArtifacts.find((candidate) => candidate.surface === 'canvas' || candidate.surface === 'both')
              if (artifact) onOpenCanvas(artifact.id)
            }}
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
          >
            <PanelRightOpen className="h-3.5 w-3.5" />
            Canvas
          </button>
        )}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto lg:max-h-[calc(100vh-10rem)]">{content}</div>
    </aside>
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

function PersistentActionRail({
  actions,
  busy,
  onSelect,
}: {
  actions: EntryActionCard[]
  busy: boolean
  onSelect: (action: EntryActionCard) => void
}) {
  const railActions = actions.filter((action) => action.kind !== 'form')
  if (railActions.length === 0) return null

  return (
    <div className="mb-3 flex flex-wrap gap-2">
      {railActions.map((action) => {
        const isPrimary = action.emphasis === 'primary'
        return (
          <button
            key={action.id}
            type="button"
            disabled={busy || Boolean(action.disabled_reason)}
            title={action.description ?? undefined}
            onClick={() => onSelect(action)}
            className={cn(
              'inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-50',
              isPrimary
                ? 'border-sky-300 bg-sky-50 text-sky-700 hover:bg-sky-100 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-300 dark:hover:bg-sky-500/20'
                : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:border-sky-500/40 dark:hover:bg-sky-500/10 dark:hover:text-sky-300',
            )}
          >
            {action.label}
          </button>
        )
      })}
    </div>
  )
}
