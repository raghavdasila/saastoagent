import { useEffect, useMemo, useRef, useState } from 'react'
import type { ChangeEvent, FormEvent, ReactNode } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { createPortal } from 'react-dom'
import {
  RouteDeckDebugger,
  RouteDeckProvider,
  createRouteDeckStore,
  useRouteDeckDispatch,
  useRouteDeckProjection,
  useRouteDeckState,
  useRouteDeckStore,
  useRouteDeckSurface,
  type RouteDeckClientState,
  type RouteDeckDispatchResult,
  type RouteDeckEvent,
  type RouteDeckOperation,
  type RouteDeckProjection,
  type RouteDeckStore,
  type RouteDeckSurface,
} from '@routedeck/react'
import {
  Activity,
  AlertTriangle,
  BookOpen,
  Bot,
  Boxes,
  Brain,
  CheckCircle2,
  Circle,
  ClipboardCheck,
  Database,
  FileText,
  GraduationCap,
  Home,
  KeyRound,
  Loader2,
  Lock,
  LogOut,
  Maximize2,
  Minimize2,
  Play,
  Plug,
  ShieldCheck,
  Sparkles,
  User,
  Wrench,
} from 'lucide-react'

import { AdminPanel } from '@/components/agent/AdminPanel'
import { AttachmentsPanel } from '@/components/agent/AttachmentsPanel'
import { CommandComposer } from '@/components/agent/CommandComposer'
import { LearningPanel } from '@/components/agent/LearningPanel'
import { MessageBubble } from '@/components/agent/MessageBubble'
import { ActionsCanvas } from '@/components/saasAgent/ActionsCanvas'
import { EntitiesCanvas } from '@/components/saasAgent/EntitiesCanvas'
import { QAAgentPanel } from '@/components/qa/QAAgentPanel'
import { ThemeToggleButton } from '@/components/theme/ThemeToggleButton'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { isValidEmail } from '@/lib/entryGraph'
import { useSaaSAgentStore } from '@/stores/saasAgentStore'
import { useThemeStore } from '@/stores/themeStore'
import type { ChatUIMessage } from '@/types/agent'
import type { AppGraphContextLens, AppGraphState } from '@/types/appGraph'
import type {
  CorpusActionResponse,
  CorpusDiagnosticsSnapshot,
  CorpusExpectedActiveSurface,
  CorpusProposal,
  CorpusStateResponse,
  CorpusSurfaceOpening,
  CorpusSurfacePrompt,
} from '@/types/corpus'
import type { SaaSAgent } from '@/types/domain'

interface AppGraphShellProps {
  nodeId?: string
  saasAgentId?: string
}

interface ProposalField {
  key: string
  label: string
  field_type?: 'text' | 'password' | 'select' | 'url'
  required?: boolean
  placeholder?: string | null
  default?: unknown
  options?: Array<{ value: string; label: string }> | null
  sensitive?: boolean
}

type WorkbenchStatus =
  | 'Ready'
  | 'Thinking'
  | 'Navigating'
  | 'Opening surface'
  | 'Preparing proposal'
  | 'Committing'
  | 'Running diagnostics'
  | 'Waiting for input'
  | 'Waiting for approval'
  | 'Needs attention'

interface CorpusQuickAction {
  operation: RouteDeckOperation
  label: string
  description?: string | null
  icon: ReactNode
  tone: 'primary' | 'tonal' | 'outline'
}

interface CapabilityItem {
  id: string
  label: string
  icon: ReactNode
  nodes: string[]
  operationId?: string
}

interface RailSelectionNotice {
  label: string
  state: 'active' | 'locked'
  message: string
}

export function AppGraphShell({ nodeId, saasAgentId }: AppGraphShellProps) {
  const statePath = useMemo(() => corpusStatePath(nodeId, saasAgentId), [nodeId, saasAgentId])
  const [routeDeckStore, setRouteDeckStore] = useState<RouteDeckStore | null>(null)

  const stateQuery = useQuery({
    queryKey: ['corpus-state', nodeId || 'home', saasAgentId || 'none'],
    queryFn: () => api.get<CorpusStateResponse>(statePath),
  })

  useEffect(() => {
    if (!stateQuery.data) return
    setRouteDeckStore((current) =>
      current ||
      createSaaStoAgentRouteDeckStore({
        initialState: stateQuery.data,
        statePath,
        nodeId,
        saasAgentId,
      }),
    )
  }, [nodeId, saasAgentId, statePath, stateQuery.data])

  if (stateQuery.isLoading && !routeDeckStore) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-slate-500">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        Loading Corpus
      </div>
    )
  }

  if (!routeDeckStore) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-6">
        <div className="max-w-md rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
          Corpus could not load the RouteDeck projection.
        </div>
      </div>
    )
  }

  return (
    <RouteDeckProvider store={routeDeckStore}>
      <AppGraphShellRuntime nodeId={nodeId} saasAgentId={saasAgentId} />
    </RouteDeckProvider>
  )
}

function AppGraphShellRuntime({ nodeId, saasAgentId }: AppGraphShellProps) {
  const routeDeckState = useRouteDeckState()
  const routeDeckStore = useRouteDeckStore()
  const dispatchRouteDeck = useRouteDeckDispatch()
  const projection = useRouteDeckProjection()
  const { user, logout } = useAuth()
  const graphState = graphStateFromRouteDeckState(routeDeckState)
  const replacePath = routeDeckState.location || null
  const setSaaSAgentId = useSaaSAgentStore((state) => state.setSaaSAgentId)
  const [chatMessages, setChatMessages] = useState<ChatUIMessage[]>(() => [
    makeAgentMessage(
      'assistant',
      'Hi. I can explain the platform, move through the graph, and open the right workflow when you ask.',
    ),
  ])
  const [draft, setDraft] = useState('')
  const [pendingProposal, setPendingProposal] = useState<CorpusProposal | null>(null)
  const [pendingSurfaceOpening, setPendingSurfaceOpening] = useState<CorpusSurfaceOpening | null>(null)
  const [queuedSurfacePrompt, setQueuedSurfacePrompt] = useState<CorpusSurfacePrompt | null>(null)
  const [corpusStatus, setCorpusStatus] = useState<WorkbenchStatus>('Ready')
  const [railNotice, setRailNotice] = useState<RailSelectionNotice | null>(null)
  const activeSurface = activeSurfaceFromProjection(projection)
  const quickActions = useMemo(() => corpusQuickActions(projection), [projection])
  const contextLens = contextLensFromProjection(projection)

  useEffect(() => {
    if (!projection || !graphState) return
    setSaaSAgentId(graphState.active_saas_agent_id || null)
    if (replacePath && replacePath !== window.location.pathname) {
      replaceBrowserPath(replacePath)
    }
  }, [graphState, projection, replacePath, setSaaSAgentId])

  useEffect(() => {
    if (!queuedSurfacePrompt) return
    if (!surfaceMatchesExpected(activeSurface, queuedSurfacePrompt.expected_active_surface)) return
    setChatMessages((current) => [...current, makeAgentMessage('assistant', queuedSurfacePrompt.content)])
    setQueuedSurfacePrompt(null)
    setPendingSurfaceOpening(null)
  }, [activeSurface, queuedSurfacePrompt])

  useEffect(() => {
    if (!pendingSurfaceOpening || queuedSurfacePrompt) return
    if (!surfaceMatchesExpected(activeSurface, pendingSurfaceOpening.expected_active_surface)) return
    setPendingSurfaceOpening(null)
  }, [activeSurface, pendingSurfaceOpening, queuedSurfacePrompt])

  const executeOperation = useMutation({
    mutationFn: async ({
      operationId,
      args,
    }: {
      operationId: string
      args?: Record<string, unknown>
    }) => {
      return dispatchRouteDeck({ operation_id: operationId, args: args || {} })
    },
    onSuccess: (response) => {
      const nextGraphState = graphStateFromRouteDeckState(response.state)
      setPendingProposal(null)
      setCorpusStatus('Ready')
      setSaaSAgentId(nextGraphState?.active_saas_agent_id || null)
      if (response.messages && response.messages.length > 0) {
        setChatMessages((current) => [
          ...current,
          ...response.messages.map((message) => makeAgentMessage('assistant', String(message.content || ''))),
        ])
      }
      const nextPath = response.state.location || null
      if (nextPath && nextPath !== window.location.pathname) {
        replaceBrowserPath(nextPath)
      }
    },
  })

  const turn = useMutation({
    mutationFn: async (userInput: string) => {
      const currentGraphState = graphStateFromRouteDeckState(routeDeckStore.getState()) || graphState
      const params = new URLSearchParams({ user_input: userInput })
      if (currentGraphState?.node) params.set('node_id', currentGraphState.node)
      if (currentGraphState?.active_saas_agent_id) {
        params.set('saas_agent_id', currentGraphState.active_saas_agent_id)
      } else if (saasAgentId) {
        params.set('saas_agent_id', saasAgentId)
      }
      if (projection?.projection_version) {
        params.set('projection_version', String(projection.projection_version))
      }

      const streamMessageId = crypto.randomUUID()
      const ensureStreamingMessage = () => {
        setChatMessages((current) => {
          if (current.some((message) => message.id === streamMessageId)) return current
          return [
            ...current,
            {
              id: streamMessageId,
              role: 'assistant',
              content: '',
              timestamp: Date.now(),
              source: 'agent',
              isStreaming: true,
            },
          ]
        })
      }
      const finishStreamingMessage = () => {
        setChatMessages((current) =>
          current.map((message) =>
            message.id === streamMessageId
              ? { ...message, isStreaming: false, thinking: undefined }
              : message,
          ),
        )
      }
      const removeEmptyStreamingMessage = () => {
        setChatMessages((current) =>
          current.filter((message) => message.id !== streamMessageId || Boolean(message.content.trim())),
        )
      }

      setPendingProposal(null)
      setQueuedSurfacePrompt(null)
      setCorpusStatus('Thinking')

      await api.getStream(`/corpus/stream?${params.toString()}`, (eventType, eventData) => {
        const routeDeckEvent = { event_type: eventType, payload: eventData.payload || {} } as RouteDeckEvent
        const payload = (eventData.payload || {}) as Record<string, unknown>
        if (eventType === 'corpus_status') {
          setCorpusStatus('Thinking')
          ensureStreamingMessage()
        }
        if (eventType === 'message_delta' && typeof payload.delta === 'string') {
          ensureStreamingMessage()
          setChatMessages((current) =>
            current.map((message) =>
              message.id === streamMessageId
                ? { ...message, content: `${message.content}${payload.delta as string}` }
                : message,
            ),
          )
        }
        if (eventType === 'message_delta' && typeof payload.content === 'string' && payload.content.trim()) {
          ensureStreamingMessage()
          setChatMessages((current) =>
            current.map((message) =>
              message.id === streamMessageId
                ? { ...message, content: payload.content as string }
                : message,
            ),
          )
        }
        if (eventType === 'proposal') {
          setCorpusStatus('Preparing proposal')
          setPendingProposal(payload as unknown as CorpusProposal)
          finishStreamingMessage()
        }
        if (eventType === 'surface_opening') {
          setCorpusStatus('Opening surface')
          removeEmptyStreamingMessage()
          setPendingSurfaceOpening(payload as unknown as CorpusSurfaceOpening)
        }
        if (eventType === 'operation_completed') {
          setCorpusStatus('Committing')
          const nextProjection = payload.projection as RouteDeckProjection | undefined
          if (nextProjection) {
            const nextState = payload.state as AppGraphState | undefined
            routeDeckStore.receiveEvent(routeDeckEvent)
            setSaaSAgentId(nextState?.active_saas_agent_id || null)
          }
          const surfacePrompt = payload.surface_prompt as CorpusSurfacePrompt | null | undefined
          if (surfacePrompt?.content) {
            setQueuedSurfacePrompt(surfacePrompt)
          }
          const nextPath = typeof payload.replace_path === 'string' ? payload.replace_path : null
          if (nextPath && nextPath !== window.location.pathname) {
            replaceBrowserPath(nextPath)
          }
          finishStreamingMessage()
        }
        if (eventType === 'projection_update') {
          setCorpusStatus('Navigating')
          routeDeckStore.receiveEvent(routeDeckEvent)
        }
        if (eventType === 'corpus_done') {
          setCorpusStatus('Ready')
          finishStreamingMessage()
        }
        if (eventType === 'corpus_error') {
          setCorpusStatus('Needs attention')
          ensureStreamingMessage()
          setChatMessages((current) =>
            current.map((message) =>
              message.id === streamMessageId
                ? {
                    ...message,
                    content: String(payload.message || 'Corpus could not complete the turn.'),
                    isStreaming: false,
                    thinking: undefined,
                  }
                : message,
            ),
          )
        }
      })
    },
  })

  const hasStreamingCorpusMessage = chatMessages.some((message) => message.isStreaming)
  const authSurfaceActive = activeSurface?.component === 'CorpusAuthSurface'
  const composerDisabled = executeOperation.isPending || turn.isPending || Boolean(pendingSurfaceOpening) || authSurfaceActive
  const visibleStatus: WorkbenchStatus = executeOperation.isPending
    ? 'Committing'
    : pendingSurfaceOpening
      ? 'Opening surface'
      : pendingProposal
        ? 'Waiting for input'
        : contextLens?.pending_trace_id
          ? 'Waiting for approval'
          : corpusStatus
  const composerPlaceholder = authSurfaceActive
    ? 'Complete authentication in the active surface'
    : pendingSurfaceOpening
      ? `Opening ${pendingSurfaceOpening.label}...`
      : 'Message Corpus'

  const sendChatTurn = () => {
    const value = draft.trim()
    if (!value || composerDisabled) return
    setDraft('')
    setChatMessages((current) => [...current, makeAgentMessage('user', value)])
    turn.mutate(value)
  }

  const handleQuickAction = (action: CorpusQuickAction) => {
    setRailNotice(null)
    const operation = action.operation
    if (operation.execution_mode === 'review' || operation.kind === 'form') {
      setPendingProposal(operationToProposal(operation))
      setCorpusStatus('Ready')
      return
    }
    setCorpusStatus(operation.target_node && operation.target_node !== projection.graph_node ? 'Navigating' : 'Committing')
    executeOperation.mutate({ operationId: operation.id, args: operation.payload || {} })
  }

  const handleRailSelect = (item: CapabilityItem, action: CorpusQuickAction | null, state: 'active' | 'ready' | 'locked') => {
    if (state === 'ready' && action) {
      handleQuickAction(action)
      return
    }

    setRailNotice({
      label: item.label,
      state: state === 'active' ? 'active' : 'locked',
      message:
        state === 'active'
          ? `${item.label} is already the active RouteDeck node. Corpus will keep working in the current surface.`
          : lockedCapabilityReason(item, contextLens),
    })
  }

  const handleLogout = () => {
    logout()
    setSaaSAgentId(null)
    void routeDeckStore.refresh().catch(() => undefined)
  }

  return (
    <div className="workbench-canvas">
      <WorkbenchTopbar
        projection={projection}
        contextLens={contextLens}
        status={visibleStatus}
        user={user}
        onLogout={handleLogout}
      />

      <div className="relative grid min-h-[calc(100vh-5.25rem)] gap-4 px-4 pb-4 lg:h-[calc(100vh-5.25rem)] lg:grid-cols-[16rem_minmax(0,1fr)_22rem] lg:overflow-hidden">
        <CapabilityRail projection={projection} graphState={graphState} contextLens={contextLens} onSelect={handleRailSelect} />

        <main className="min-w-0 lg:min-h-0 lg:overflow-hidden">
          <AgentConversation
            messages={chatMessages}
            draft={draft}
            busy={executeOperation.isPending || (turn.isPending && !hasStreamingCorpusMessage && !pendingSurfaceOpening)}
            composerDisabled={composerDisabled}
            composerPlaceholder={composerPlaceholder}
            status={visibleStatus}
            error={turn.error || executeOperation.error}
            pendingProposal={pendingProposal}
            pendingSurfaceOpening={pendingSurfaceOpening}
            quickActions={quickActions}
            activeSurfacePanel={<ActiveSurfacePanel projection={projection} graphState={graphState} />}
            activeSurfaceKey={activeSurface ? `${activeSurface.component}:${activeSurface.variant}` : 'none'}
            onDraftChange={setDraft}
            onSend={sendChatTurn}
            onQuickAction={handleQuickAction}
            onProposalAccept={(args) =>
              pendingProposal &&
              executeOperation.mutate({ operationId: pendingProposal.operation_id, args })
            }
            onProposalDismiss={() => setPendingProposal(null)}
          />
        </main>

        <aside className="workbench-panel min-w-0 p-4 dark:!bg-[rgba(26,27,30,0.8)] lg:min-h-0 lg:overflow-y-auto">
          <ContextPanel projection={projection} status={visibleStatus} railNotice={railNotice} />
          <DiagnosticsPanel
            projection={projection}
            graphState={graphState}
          />
        </aside>
      </div>
    </div>
  )
}

function corpusStatePath(nodeId?: string, saasAgentId?: string) {
  const params = new URLSearchParams()
  if (nodeId) params.set('node_id', nodeId)
  if (saasAgentId) params.set('saas_agent_id', saasAgentId)
  const query = params.toString()
  return `/corpus/state${query ? `?${query}` : ''}`
}

function createSaaStoAgentRouteDeckStore({
  initialState,
  statePath,
  nodeId,
  saasAgentId,
}: {
  initialState: CorpusStateResponse
  statePath: string
  nodeId?: string
  saasAgentId?: string
}) {
  return createRouteDeckStore({
    initialState: corpusStateToRouteDeckState(initialState),
    snapshot: async () => corpusStateToRouteDeckState(await api.get<CorpusStateResponse>(statePath)),
    dispatch: async (input, currentState) => {
      const graphState = graphStateFromRouteDeckState(currentState)
      if (!graphState) throw new Error('Graph state is unavailable')
      const response = await api.post<CorpusActionResponse>('/corpus/action', {
        state: graphState,
        node_id: graphState.node || nodeId,
        saas_agent_id: graphState.active_saas_agent_id || saasAgentId,
        operation_id: input.operation_id,
        args: input.args || {},
        projection_version: currentState.projection.projection_version || 1,
      })
      return corpusActionToDispatchResult(response, input.operation_id)
    },
  })
}

function corpusStateToRouteDeckState(response: CorpusStateResponse): RouteDeckClientState {
  return {
    projection: response.projection,
    status: 'idle',
    graph_state: response.state as unknown as Record<string, unknown>,
    location: response.replace_path || null,
  }
}

function corpusActionToDispatchResult(
  response: CorpusActionResponse,
  operationId: string,
): RouteDeckDispatchResult {
  return {
    operation_id: operationId,
    accepted: true,
    state: corpusStateToRouteDeckState({
      state: response.state,
      projection: response.projection,
      replace_path: response.replace_path,
    }),
    active_surface: response.active_surface || null,
    messages: response.messages.map((message) => ({ ...message })),
    events: [],
    metadata: {},
  }
}

function graphStateFromRouteDeckState(state: RouteDeckClientState): AppGraphState | null {
  const graphState = state.graph_state
  if (!graphState || typeof graphState.node !== 'string') return null
  return graphState as unknown as AppGraphState
}

function replaceBrowserPath(nextPath: string) {
  window.history.replaceState(window.history.state, '', nextPath)
}

function makeAgentMessage(role: 'user' | 'assistant', content: string): ChatUIMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: Date.now(),
    source: 'agent',
  }
}

function WorkbenchTopbar({
  projection,
  contextLens,
  status,
  user,
  onLogout,
}: {
  projection: RouteDeckProjection
  contextLens: AppGraphContextLens | null
  status: WorkbenchStatus
  user: { email?: string; display_name?: string | null } | null
  onLogout: () => void
}) {
  const currentWork = displayWork(contextLens?.working_on || projection.current_context)
  return (
    <header className="relative z-20 p-4 pb-3">
      <div className="workbench-topbar flex min-h-[3.9rem] items-center justify-between gap-4 px-4 sm:px-5">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-[0_16px_34px_-22px_hsl(var(--primary)/0.9)]">
            <Bot className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-base font-semibold tracking-[-0.01em]">SaaStoAgent</div>
            <div className="mt-0.5 flex min-w-0 items-center gap-2 text-sm text-muted-foreground">
              <span className="truncate">Corpus</span>
              <span>/</span>
              <span className="truncate">{currentWork}</span>
            </div>
          </div>
        </div>

        <div className="flex min-w-0 items-center gap-2">
          <StatusPill status={status} testId="corpus-status" />
          {user ? (
            <div className="flex min-w-0 max-w-[12rem] items-center gap-2 rounded-full border border-border/20 bg-muted/70 px-3 py-2 text-sm text-foreground shadow-sm dark:border-white/10" data-testid="auth-user-pill">
              <User className="h-4 w-4 shrink-0" />
              <span className="max-w-48 truncate">{user.email || user.display_name || 'Signed in'}</span>
            </div>
          ) : (
            <div className="hidden rounded-full border border-border/20 bg-muted/70 px-3 py-2 text-sm text-muted-foreground shadow-sm md:block dark:border-white/10">Not signed in</div>
          )}
          <button type="button" className="surface-outline-button hidden md:inline-flex">Profile</button>
          {user && (
            <button type="button" onClick={onLogout} className="surface-outline-button inline-flex items-center gap-2" data-testid="auth-logout">
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          )}
          <ThemeToggleButton />
        </div>
      </div>
    </header>
  )
}

function StatusPill({ status, testId }: { status: WorkbenchStatus; testId?: string }) {
  const active = ['Thinking', 'Navigating', 'Opening surface', 'Preparing proposal', 'Committing', 'Running diagnostics'].includes(status)
  return (
    <div className="inline-flex min-h-10 items-center gap-2 rounded-[0.8rem] border border-border/20 bg-muted/75 px-3 py-2 text-sm font-medium text-foreground shadow-sm dark:border-white/10" data-testid={testId}>
      {active ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-300" />}
      <span>{status}</span>
    </div>
  )
}

function AgentConversation({
  messages,
  draft,
  busy,
  composerDisabled,
  composerPlaceholder,
  status,
  error,
  pendingProposal,
  pendingSurfaceOpening,
  quickActions,
  activeSurfacePanel,
  activeSurfaceKey,
  onDraftChange,
  onSend,
  onQuickAction,
  onProposalAccept,
  onProposalDismiss,
}: {
  messages: ChatUIMessage[]
  draft: string
  busy: boolean
  composerDisabled: boolean
  composerPlaceholder: string
  status: WorkbenchStatus
  error: unknown
  pendingProposal: CorpusProposal | null
  pendingSurfaceOpening: CorpusSurfaceOpening | null
  quickActions: CorpusQuickAction[]
  activeSurfacePanel: ReactNode
  activeSurfaceKey: string
  onDraftChange: (value: string) => void
  onSend: () => void
  onQuickAction: (action: CorpusQuickAction) => void
  onProposalAccept: (args: Record<string, unknown>) => void
  onProposalDismiss: () => void
}) {
  const workspaceRef = useRef<HTMLDivElement>(null)
  let latestAssistantMessageId: string | null = null
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index]
    if (!message) continue
    if (message.role === 'assistant' && !message.isStreaming) {
      latestAssistantMessageId = message.id
      break
    }
  }

  useEffect(() => {
    const workspace = workspaceRef.current
    if (!workspace) return undefined
    const frame = window.requestAnimationFrame(() => {
      workspace.scrollTo({ top: workspace.scrollHeight, behavior: 'smooth' })
    })
    return () => window.cancelAnimationFrame(frame)
  }, [messages.length, busy, pendingSurfaceOpening?.operation_id, pendingProposal?.operation_id, activeSurfaceKey, error])

  return (
    <section className="corpus-workbench flex h-[calc(100vh-8.75rem)] min-h-0 flex-col dark:!bg-[rgba(26,27,30,0.9)] lg:h-full" data-testid="app-agent-chat">
      <div className="flex min-h-0 w-full flex-1 flex-col px-5 pt-5 sm:px-6">
        <div className="flex shrink-0 items-center justify-between gap-3 pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-[-0.01em]">Corpus Workspace</h1>
            <p className="mt-1 text-sm text-muted-foreground">Tell Corpus what to set up, inspect, or run.</p>
          </div>
          <div className="hidden sm:block"><StatusPill status={status} testId="corpus-inline-status" /></div>
        </div>

        <div ref={workspaceRef} className="min-h-0 flex-1 overflow-y-auto py-4 pr-1">
          <FrameSurfacePanel />

          <div className="py-3">
            {messages.map((message) => (
              <div key={message.id}>
                <MessageBubble message={message} />
                {message.id === latestAssistantMessageId && (
                  <QuickActionChips
                    actions={quickActions}
                    onAction={onQuickAction}
                    className="-mt-1 mb-3 pl-16 pr-4"
                  />
                )}
              </div>
            ))}
            {busy && (
              <MessageBubble
                message={{
                  id: 'corpus-busy',
                  role: 'assistant',
                  content: '',
                  timestamp: Date.now(),
                  isStreaming: true,
                }}
              />
            )}
            {pendingSurfaceOpening && <SurfaceOpeningNotice opening={pendingSurfaceOpening} />}
          </div>

          {activeSurfacePanel}

          {pendingProposal && (
            <ProposalPanel
              proposal={pendingProposal}
              busy={busy}
              onAccept={onProposalAccept}
              onDismiss={onProposalDismiss}
            />
          )}

          {error && (
            <div className="mb-3 rounded-[0.625rem] bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
              {error instanceof Error ? error.message : 'Corpus could not complete that step.'}
            </div>
          )}
        </div>

        <div className="shrink-0 border-t border-border/10 bg-transparent py-4 dark:border-white/10">
          <CommandComposer
            value={draft}
            onChange={onDraftChange}
            onSend={onSend}
            placeholder={composerPlaceholder}
            disabled={composerDisabled}
          />
        </div>
      </div>
    </section>
  )
}

function QuickActionChips({
  actions,
  onAction,
  className = '',
}: {
  actions: CorpusQuickAction[]
  onAction: (action: CorpusQuickAction) => void
  className?: string
}) {
  if (actions.length === 0) return null
  return (
    <div className={`flex flex-wrap gap-2 ${className}`} data-testid="corpus-quick-actions">
      {actions.map((action) => (
        <button
          key={action.operation.id}
          type="button"
          onClick={() => onAction(action)}
          className={[
            'inline-flex min-h-10 items-center gap-2 rounded-[0.8rem] px-4 py-2 text-sm font-semibold transition-all duration-300 active:scale-95',
            action.tone === 'primary'
              ? 'bg-primary text-primary-foreground shadow-[0_14px_28px_-19px_hsl(var(--primary)/0.9)] hover:bg-primary/90 hover:shadow-[0_20px_36px_-20px_hsl(var(--primary)/0.95)]'
              : action.tone === 'outline'
                ? 'border border-border/25 bg-card/90 text-primary shadow-sm hover:border-primary/25 hover:bg-muted'
                : 'border border-border/20 bg-muted/75 text-foreground shadow-sm hover:bg-card/90',
          ].join(' ')}
          title={action.description || action.label}
        >
          {action.icon}
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  )
}

function CapabilityRail({
  projection,
  graphState,
  contextLens,
  onSelect,
}: {
  projection: RouteDeckProjection
  graphState: AppGraphState | null
  contextLens: AppGraphContextLens | null
  onSelect: (item: CapabilityItem, action: CorpusQuickAction | null, state: 'active' | 'ready' | 'locked') => void
}) {
  const operationsById = new Map(projection.legal_operations.map((operation) => [operation.id, operation]))
  const currentNode = graphState?.node || projection.graph_node
  const items = capabilityItems()
  return (
    <nav className="workbench-panel hidden min-w-0 p-3 dark:!bg-[rgba(26,27,30,0.8)] lg:block" aria-label="RouteDeck node switcher" data-testid="capability-rail">
      <div className="mb-3 px-3 pt-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">RouteDeck Nodes</div>
      <div className="space-y-2">
        {items.map((item) => {
          const operation = item.operationId ? operationsById.get(item.operationId) : undefined
          const active = item.nodes.includes(currentNode)
          const available = !item.operationId || Boolean(operation)
          const status = active ? 'active' : available ? 'ready' : 'locked'
          const action = operation ? operationToQuickAction(operation) : null
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item, action, status)}
              className={[
                'group flex min-h-12 w-full items-center gap-3 rounded-[0.7rem] px-3 text-left text-sm font-medium transition-all duration-300 active:scale-95',
                active
                  ? 'bg-primary text-primary-foreground shadow-[0_16px_30px_-22px_hsl(var(--primary)/0.95)]'
                  : available
                    ? 'text-foreground hover:bg-muted/80'
                    : 'text-muted-foreground opacity-90 hover:bg-muted/60',
              ].join(' ')}
              title={status === 'locked' ? lockedCapabilityReason(item, contextLens) : item.label}
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-background/60 text-current shadow-sm dark:bg-background/30">
                {item.icon}
              </span>
              <span className="min-w-0 flex-1 truncate">{item.label}</span>
              <CapabilityStatusIcon status={status} />
            </button>
          )
        })}
      </div>
    </nav>
  )
}

function CapabilityStatusIcon({ status }: { status: 'active' | 'ready' | 'locked' }) {
  if (status === 'active') return <Activity className="h-4 w-4" />
  if (status === 'ready') return <Circle className="h-3.5 w-3.5 fill-emerald-500 text-emerald-500" />
  return <Lock className="h-4 w-4" />
}

function SurfaceOpeningNotice({ opening }: { opening: CorpusSurfaceOpening }) {
  return (
    <div className="flex gap-3 px-4 py-3" data-testid="surface-opening-loader">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-secondary">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
      <div className="max-w-[75%] rounded-[0.75rem] bg-muted px-4 py-2.5 text-sm text-foreground shadow-sm">
        Opening {opening.label}...
      </div>
    </div>
  )
}

function FrameSurfacePanel() {
  const projection = useRouteDeckProjection()
  const surface = useRouteDeckSurface('main')
  const contextLens = contextLensFromProjection(projection)
  if (!surface) return null

  if (surface.component === 'CorpusLoungeSurface') {
    return (
      <div className="md3-surface-low p-5">
        <div className="flex items-center gap-2 text-sm font-semibold"><Sparkles className="h-4 w-4 text-primary" />{String(surface.props?.title || 'Explore SaaStoAgent')}</div>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {String(
            surface.props?.subtitle ||
              'Ask about the platform, then let Corpus guide you into the next graph node when needed.',
          )}
        </p>
      </div>
    )
  }

  if (surface.component === 'CorpusDashboardSurface') {
    const saasAgents = Array.isArray(surface.props?.saas_agents)
      ? (surface.props?.saas_agents as SaaSAgent[])
      : []
    return (
      <div className="relative overflow-hidden rounded-[0.9rem] border border-border/20 bg-gradient-to-br from-card via-muted/75 to-card p-5 shadow-[0_22px_52px_-42px_hsl(var(--foreground)/0.68)] dark:border-white/10 dark:from-muted/80 dark:via-card dark:to-muted/50">
        <div className="pointer-events-none absolute -right-16 -top-24 h-56 w-56 rounded-full bg-secondary/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-28 left-1/4 h-52 w-52 rounded-full bg-primary/10 blur-3xl" />
        <div className="flex items-start justify-between gap-4">
          <div className="relative min-w-0">
            <div className="text-sm font-semibold">Dashboard</div>
            <p className="mt-2 text-sm text-muted-foreground">
              Corpus stays in the center. The dashboard remains contextual until you ask to open or create an agent.
            </p>
          </div>
          <div className="relative shrink-0 whitespace-nowrap rounded-full bg-secondary px-3 py-1 text-[11px] font-semibold text-secondary-foreground shadow-[0_12px_26px_-18px_hsl(var(--secondary)/0.9)]">
            {saasAgents.length} agents
          </div>
        </div>
        {saasAgents.length > 0 && (
          <div className="relative mt-4 grid gap-2 sm:grid-cols-2">
            {saasAgents.slice(0, 4).map((agent) => (
              <div key={agent.id} className="rounded-[0.75rem] border border-border/20 bg-card/90 p-3 text-sm shadow-[0_16px_32px_-28px_hsl(var(--foreground)/0.55)] dark:border-white/10 dark:bg-background/30">
                <div className="font-semibold">{agent.name}</div>
                <div className="mt-1 text-xs text-muted-foreground">Ready to configure</div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="md3-surface-low p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-semibold">{String(surface.props?.title || contextLens?.working_on || displayWork(projection.graph_node))}</div>
        <span className="shrink-0 whitespace-nowrap rounded-full bg-secondary px-3 py-1 text-[11px] font-semibold text-secondary-foreground shadow-sm">
          Current node
        </span>
      </div>
      <div className="mt-2 text-sm text-muted-foreground">
        {contextLens?.selected_saas_agent_name
          ? `Focused on ${contextLens.selected_saas_agent_name}.`
          : 'Context is graph-owned and can change when Corpus commits the next legal operation.'}
      </div>
    </div>
  )
}

function ProposalPanel({
  proposal,
  busy,
  onAccept,
  onDismiss,
}: {
  proposal: CorpusProposal
  busy: boolean
  onAccept: (args: Record<string, unknown>) => void
  onDismiss: () => void
}) {
  const fields = proposalFields(proposal)
  const [values, setValues] = useState<Record<string, unknown>>(() => proposalDefaults(proposal))

  useEffect(() => {
    setValues(proposalDefaults(proposal))
  }, [proposal])

  const submit = () => onAccept(values)

  return (
    <div
      className="mb-4 rounded-[0.9rem] border border-border/30 bg-card p-5 shadow-[0_26px_64px_-42px_hsl(var(--foreground)/0.65)] dark:border-white/15 dark:bg-muted dark:shadow-black/40"
      data-testid="corpus-proposal-surface"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{proposal.label}</div>
          {proposal.description && <p className="mt-1 text-sm text-muted-foreground">{proposal.description}</p>}
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="surface-outline-button px-3 py-1 text-xs"
        >
          Dismiss
        </button>
      </div>

      {fields.length > 0 && (
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {fields.map((field) => (
            <label key={field.key} className="grid gap-1.5 text-sm">
              <span className="text-xs font-medium text-muted-foreground">{field.label}</span>
              {field.field_type === 'select' ? (
                <select
                  value={String(values[field.key] ?? field.default ?? '')}
                  onChange={(event) => setValues((current) => ({ ...current, [field.key]: event.target.value }))}
                  className="md3-field"
                >
                  {(field.options || []).map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.sensitive ? 'password' : field.field_type === 'url' ? 'url' : 'text'}
                  value={String(values[field.key] ?? field.default ?? '')}
                  placeholder={field.placeholder || ''}
                  onChange={(event) => handleProposalFieldChange(field.key, event, setValues)}
                  className="md3-field"
                />
              )}
            </label>
          ))}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={submit}
          disabled={busy}
          className="surface-solid-button disabled:cursor-not-allowed disabled:opacity-50"
        >
          Continue
        </button>
      </div>
    </div>
  )
}

function ActiveSurfacePanel({
  projection,
  graphState,
}: {
  projection: RouteDeckProjection
  graphState: AppGraphState | null
}) {
  const contextLens = contextLensFromProjection(projection)
  const activeSurface = useMemo(
    () => activeSurfaceFromProjection(projection),
    [projection.surfaces],
  )

  if (!activeSurface) return null

  return (
    <section className="py-4" data-testid="active-surface-panel">
      <div className="rounded-[0.9rem] border border-border/30 bg-card p-5 shadow-[0_26px_64px_-42px_hsl(var(--foreground)/0.65)] dark:border-white/15 dark:bg-muted dark:shadow-black/40">
        <div className="mb-4 flex items-center justify-between gap-3 pb-3">
          <div>
            <h2 className="text-base font-semibold">{surfaceTitle(activeSurface, contextLens)}</h2>
            <p className="mt-1 text-sm text-muted-foreground">Opened from committed graph state.</p>
          </div>
          <span className="shrink-0 whitespace-nowrap rounded-full bg-secondary px-3 py-1 text-[11px] font-semibold text-secondary-foreground shadow-sm">
            Active surface
          </span>
        </div>
        <SurfaceRenderer surface={activeSurface} contextLens={contextLens} graphState={graphState} />
      </div>
    </section>
  )
}

function SurfaceRenderer({
  surface,
  contextLens,
  graphState,
}: {
  surface: RouteDeckSurface
  contextLens: AppGraphContextLens | null
  graphState: AppGraphState | null
}) {
  if (surface.component === 'CorpusAuthSurface') {
    return <AuthSurfaceCard surface={surface} />
  }
  if (surface.component === 'EntitiesSurface') return <EntitiesCanvas />
  if (surface.component === 'ActionsSurface') return <ActionsCanvas />
  if (surface.component === 'KnowledgeSurface') return <AttachmentsPanel />
  if (surface.component === 'LearningSurface') return <LearningPanel />
  if (surface.component === 'QASurface') return <QAAgentPanel onResetRuntime={async () => undefined} />
  if (surface.component === 'MemorySurface') {
    const agents = Array.isArray(surface.props?.saas_agents) ? (surface.props?.saas_agents as SaaSAgent[]) : []
    const activeAgent = agents.find((agent) => agent.id === graphState?.active_saas_agent_id)
    return <AdminPanel saasAgent={activeAgent} />
  }
  if (surface.component === 'SchemaPreviewSurface') {
    const preview = surface.props?.schema_preview as Record<string, unknown> | undefined
    return (
      <InfoSurface title="Schema preview" description="Review the detected API shape before activation." icon={<FileText className="h-5 w-5" />}>
        <dl className="grid gap-2 text-sm sm:grid-cols-3">
          <Fact label="Title" value={String(preview?.title || 'Pending preview')} />
          <Fact label="Version" value={String(preview?.version || 'Unknown')} />
          <Fact label="Endpoints" value={String(preview?.endpoint_count || 0)} />
        </dl>
      </InfoSurface>
    )
  }
  if (surface.component === 'CatalogSurface') {
    const activationEvents = Array.isArray(surface.props?.activation_events)
      ? (surface.props?.activation_events as unknown[])
      : []
    return (
      <InfoSurface title="Catalog" description="Activated API capabilities and generated tools appear here as they become available." icon={<Boxes className="h-5 w-5" />}>
        <div className="grid gap-3 sm:grid-cols-3">
          <Metric label="Ready APIs" value={contextLens?.ready_connection_count || 0} icon={<KeyRound className="h-4 w-4" />} />
          <Metric label="Actions" value={contextLens?.action_count || 0} icon={<Play className="h-4 w-4" />} />
          <Metric label="Tools" value={contextLens?.tool_count || 0} icon={<ShieldCheck className="h-4 w-4" />} />
        </div>
        {activationEvents.length > 0 && (
          <p className="mt-3 text-sm text-slate-500">{activationEvents.length} activation events captured for diagnostics.</p>
        )}
      </InfoSurface>
    )
  }
  if (surface.component === 'ConnectionSetupSurface') {
    return (
      <InfoSurface title="Connect an API" description="Use Corpus proposals to preview a schema and activate a connection from this node." icon={<KeyRound className="h-5 w-5" />} />
    )
  }
  if (surface.component === 'ExecutionSurface') {
    return (
      <InfoSurface title="Execution" description="Corpus will propose execution inputs or approvals when the graph requires them." icon={<Play className="h-5 w-5" />} />
    )
  }
  if (surface.component === 'RecoverySurface') {
    return (
      <InfoSurface title="Recovery" description="This path needs a different prerequisite. Diagnostics can explain why it is blocked." icon={<AlertTriangle className="h-5 w-5" />} />
    )
  }
  return (
    <InfoSurface title={surfaceTitle(surface, contextLens)} description="This surface is available from the current node." icon={<Boxes className="h-5 w-5" />} />
  )
}

function AuthSurfaceCard({ surface }: { surface: RouteDeckSurface }) {
  const intent = surface.variant === 'auth_register' ? 'register' : 'login'
  const { login, register } = useAuth()
  const routeDeckStore = useRouteDeckStore()
  const firstFieldRef = useRef<HTMLInputElement>(null)
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    firstFieldRef.current?.focus()
  }, [intent])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    const cleanedEmail = email.trim()
    if (!isValidEmail(cleanedEmail)) {
      setError('Enter a full email address.')
      return
    }
    if (intent === 'register' && password.length < 8) {
      setError('Use at least 8 characters for the password.')
      return
    }

    setSubmitting(true)
    try {
      if (intent === 'register') {
        await register(cleanedEmail, password, displayName.trim() || undefined)
      } else {
        await login(cleanedEmail, password)
      }
      await routeDeckStore.dispatch({
        operation_id: 'navigate.home',
        args: {},
      })
    } catch (authError: unknown) {
      setError(authError instanceof Error ? authError.message : 'Authentication failed.')
    } finally {
      setSubmitting(false)
    }
  }

  const title = intent === 'register' ? 'Create account' : 'Sign in'
  const description =
    intent === 'register'
      ? 'Create the platform account here. Corpus will continue from the authenticated graph after this succeeds.'
      : 'Sign in here. Corpus will keep the graph context and continue after authentication succeeds.'

  return (
    <form className="grid gap-4" onSubmit={submit} data-testid="corpus-auth-surface">
      <div>
        <h3 className="text-xl font-medium">{title}</h3>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{description}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {intent === 'register' && (
          <label className="grid gap-1.5 text-sm sm:col-span-2">
            <span className="text-xs font-medium text-muted-foreground">Display name</span>
            <input
              ref={firstFieldRef}
              type="text"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              placeholder="Optional"
              className="md3-field"
              data-testid="corpus-auth-display-name"
            />
          </label>
        )}

        <label className="grid gap-1.5 text-sm">
          <span className="text-xs font-medium text-muted-foreground">Email</span>
          <input
            ref={intent === 'login' ? firstFieldRef : undefined}
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            className="md3-field"
            data-testid="corpus-auth-email"
          />
        </label>

        <label className="grid gap-1.5 text-sm">
          <span className="text-xs font-medium text-muted-foreground">Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={intent === 'register' ? 'At least 8 characters' : 'Password'}
            className="md3-field"
            data-testid="corpus-auth-password"
          />
        </label>
      </div>

      {error && (
        <div className="rounded-[0.625rem] bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="surface-solid-button inline-flex items-center gap-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
          {title}
        </button>
        <button
          type="button"
          disabled={submitting}
          onClick={() => {
            void routeDeckStore.dispatch({ operation_id: 'navigate.home', args: {} })
          }}
          className="surface-outline-button disabled:cursor-not-allowed disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

function ContextPanel({
  projection,
  status,
  railNotice,
}: {
  projection: RouteDeckProjection
  status: WorkbenchStatus
  railNotice: RailSelectionNotice | null
}) {
  const lens = contextLensFromProjection(projection)
  return (
    <section>
      <h2 className="text-sm font-medium">Context / Evidence</h2>
      <div className="mt-3"><StatusPill status={status} testId="corpus-sidebar-status" /></div>
      {railNotice && (
          <div className="mt-3 rounded-[0.75rem] bg-secondary px-4 py-3 text-sm text-secondary-foreground shadow-sm" data-testid="rail-node-notice">
          <div className="flex items-center gap-2 font-medium">
            {railNotice.state === 'locked' ? <Lock className="h-4 w-4" /> : <Activity className="h-4 w-4" />}
            Node switcher: {railNotice.label}
          </div>
          <p className="mt-2 leading-5 text-secondary-foreground/90">{railNotice.message}</p>
        </div>
      )}
      <dl className="mt-4 grid gap-2 text-xs">
        <LensRow label="Agent" value={lens?.selected_saas_agent_name || 'No agent selected'} />
        <LensRow label="Current work" value={displayWork(lens?.working_on || projection.current_context)} />
        <LensRow label="API readiness" value={`${lens?.ready_connection_count || 0}/${lens?.connection_count || 0} ready`} />
        <LensRow label="Tools" value={String(lens?.tool_count || 0)} />
        <LensRow label="Recent event" value={displayWork(projection.graph_node)} />
        {lens?.pending_trace_id && <LensRow label="Pending approval" value={lens.pending_trace_status || 'Waiting'} />}
      </dl>
    </section>
  )
}

function DiagnosticsPanel({
  projection,
  graphState,
}: {
  projection: RouteDeckProjection
  graphState: AppGraphState | null
}) {
  const theme = useThemeStore((state) => state.theme)
  const [open, setOpen] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(projection.graph_node)
  const [snapshot, setSnapshot] = useState<CorpusDiagnosticsSnapshot | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    setSelectedNodeId(projection.graph_node)
  }, [projection.graph_node])

  useEffect(() => {
    if (!open) return
    setLoadError(null)
    const params = new URLSearchParams()
    if (graphState?.node) params.set('node_id', graphState.node)
    if (graphState?.active_saas_agent_id) params.set('saas_agent_id', graphState.active_saas_agent_id)
    params.set('projection_version', String(projection.projection_version))
    void api
      .getStream(`/diagnostics/stream?${params.toString()}`, (eventType, data) => {
        if (eventType === 'diagnostic_event') {
          const payload = (data.snapshot || null) as CorpusDiagnosticsSnapshot | null
          setSnapshot(payload)
        }
      })
      .catch((error) => {
        setLoadError(error instanceof Error ? error.message : 'Diagnostics failed to load.')
      })
  }, [open, projection])

  useEffect(() => {
    if (open) return
    setFullscreen(false)
  }, [open])

  useEffect(() => {
    if (!fullscreen) return undefined
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setFullscreen(false)
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [fullscreen])

  const diagnosticsContent = (
    <div
      className={
        fullscreen
          ? 'flex h-full w-full flex-col rounded-[0.95rem] border border-border/25 bg-card/95 p-4 text-xs shadow-[0_32px_80px_-48px_hsl(var(--foreground)/0.72)] dark:border-white/10 dark:bg-[#1c1d20]/95 dark:shadow-black/50'
          : 'mt-3 max-h-[calc(100vh-13rem)] overflow-y-auto rounded-xl border border-border/25 bg-card/90 p-4 text-xs shadow-inner dark:border-white/10 dark:bg-muted/90'
      }
      data-testid={fullscreen ? 'diagnostics-fullscreen' : 'diagnostics-panel'}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <div className="font-medium text-foreground">RouteDeck diagnostics</div>
          <div className="mt-1 font-mono text-[11px] text-muted-foreground">
            {projection.current_context} / {projection.graph_node} / v{projection.projection_version}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {fullscreen && (
            <button
              type="button"
              onClick={() => setFullscreen(false)}
              className="surface-outline-button inline-flex items-center gap-2 px-3 py-1 text-xs"
            >
              <Minimize2 className="h-3.5 w-3.5" />
              Docked
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              setFullscreen(false)
              setOpen(false)
            }}
            className="surface-outline-button px-3 py-1 text-xs"
          >
            Close
          </button>
        </div>
      </div>

      <div className={fullscreen ? 'min-h-0 flex-1 overflow-y-auto pr-1' : ''}>
        {loadError && (
          <div className="mb-4 rounded-[0.625rem] bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
            {loadError}
          </div>
        )}

        {snapshot ? (
          <>
            <RouteDeckDebugger
              graphManifest={snapshot.graph_manifest as never}
              snapshot={snapshot.runtime_snapshot as never}
              selectedNodeId={selectedNodeId}
              onSelectedNodeChange={setSelectedNodeId}
              themeMode={theme}
              canvasClassName={fullscreen ? 'h-[calc(100vh-21rem)] min-h-[28rem]' : 'h-[30rem]'}
            />

            <details className="mt-4 rounded-[0.625rem] bg-slate-950 p-3 text-[11px] text-slate-100">
              <summary className="cursor-pointer font-semibold">Raw RouteDeck JSON</summary>
              <pre className="mt-3 max-h-96 overflow-auto">
                {JSON.stringify(snapshot, null, 2)}
              </pre>
            </details>
          </>
        ) : (
          <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading diagnostics
          </div>
        )}
      </div>
    </div>
  )

  return (
    <section className="mt-6" data-testid="diagnostics-sidebar">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="surface-outline-button inline-flex items-center gap-2 text-xs"
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          Diagnostics
        </button>
        {open && !fullscreen && (
          <button
            type="button"
            onClick={() => setFullscreen(true)}
            className="surface-outline-button inline-flex items-center gap-2 px-3 py-1 text-xs"
          >
            <Maximize2 className="h-3.5 w-3.5" />
            Full screen
          </button>
        )}
      </div>
      {open && !fullscreen && diagnosticsContent}
      {open && fullscreen && typeof document !== 'undefined'
        ? createPortal(
            <div className="fixed inset-0 z-[90] bg-background/72 p-4 backdrop-blur-sm">
              <div className="mx-auto h-full max-w-[120rem]">
                {diagnosticsContent}
              </div>
            </div>,
            document.body,
          )
        : null}
    </section>
  )
}

function LensRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[0.625rem] border border-border/10 bg-background/40 p-3 shadow-sm dark:border-white/5 dark:bg-background/30">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words font-medium">{value}</dd>
    </div>
  )
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/25 bg-card p-3 shadow-sm dark:border-white/10 dark:bg-muted">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  )
}

function Metric({ label, value, icon }: { label: string; value: number; icon: ReactNode }) {
  return (
    <div className="rounded-xl border border-border/25 bg-card p-4 shadow-sm dark:border-white/10 dark:bg-muted">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <div className="mt-2 text-2xl font-medium">{value}</div>
    </div>
  )
}

function InfoSurface({
  title,
  description,
  icon,
  children,
}: {
  title: string
  description: string
  icon: ReactNode
  children?: ReactNode
}) {
  return (
    <div>
      <div className="flex items-start gap-3">
        <div className="rounded-[0.625rem] bg-secondary p-2 text-secondary-foreground">
          {icon}
        </div>
        <div className="min-w-0">
          <h3 className="text-lg font-medium">{title}</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p>
        </div>
      </div>
      {children && <div className="mt-5">{children}</div>}
    </div>
  )
}

function surfaceTitle(surface: RouteDeckSurface, contextLens: AppGraphContextLens | null) {
  if (surface.component === 'CorpusAuthSurface') {
    return surface.variant === 'auth_register' ? 'Create account' : 'Sign in'
  }
  return String(surface.props?.title || contextLens?.working_on || surface.variant || surface.component)
}

function contextLensFromProjection(projection: RouteDeckProjection): AppGraphContextLens | null {
  const sideSurface = projection.surfaces.side
  if (!sideSurface?.props || typeof sideSurface.props !== 'object') return null
  return sideSurface.props as unknown as AppGraphContextLens
}

function activeSurfaceFromProjection(projection: RouteDeckProjection): RouteDeckSurface | null {
  return Object.values(projection.surfaces).find((surface) => surface.role === 'active') || null
}

function corpusQuickActions(projection: RouteDeckProjection): CorpusQuickAction[] {
  return projection.legal_operations
    .filter((operation) => operation.id !== 'navigate.home')
    .slice(0, 5)
    .map(operationToQuickAction)
}

function operationToQuickAction(operation: RouteDeckOperation): CorpusQuickAction {
  return {
    operation,
    label: corpusActionLabel(operation),
    description: operation.description,
    icon: operationIcon(operation.id),
    tone: operation.emphasis === 'primary' ? 'primary' : operation.execution_mode === 'review' ? 'outline' : 'tonal',
  }
}

function operationToProposal(operation: RouteDeckOperation): CorpusProposal {
  return {
    operation_id: operation.id,
    label: corpusActionLabel(operation),
    description: operation.description,
    args: operation.payload || {},
    execution_mode: operation.execution_mode || 'review',
    safety_class: operation.safety_class,
    input_schema: operation.input_schema,
    target_node: operation.target_node,
  }
}

function corpusActionLabel(operation: RouteDeckOperation) {
  const labels: Record<string, string> = {
    'auth.sign_in': 'Sign in',
    'auth.register': 'Create account',
    'saas_agent.create': 'Create SaaS Agent',
    'saas_agent.open': 'Open SaaS Agent',
    'navigate.connection_configure': 'Connect API',
    'connection.preview': 'Preview schema',
    'connection.activate': 'Activate API',
    'catalog.open': 'Catalog',
    'entities.open': 'Entities',
    'actions.open': 'Actions',
    'execution.open': 'Execution',
    'execution.plan': 'Plan execution',
    'knowledge.open': 'Knowledge',
    'memory.open': 'Memory',
    'learning.open': 'Learning',
    'qa.open': 'Run QA',
  }
  return labels[operation.id] || operation.label
}

function operationIcon(operationId: string): ReactNode {
  if (operationId.includes('auth')) return <User className="h-4 w-4" />
  if (operationId.includes('saas_agent.create')) return <PlusCircleIcon />
  if (operationId.includes('saas_agent.open')) return <Home className="h-4 w-4" />
  if (operationId.includes('connection')) return <Plug className="h-4 w-4" />
  if (operationId.includes('catalog')) return <Database className="h-4 w-4" />
  if (operationId.includes('entities')) return <Boxes className="h-4 w-4" />
  if (operationId.includes('actions')) return <ListIcon />
  if (operationId.includes('execution')) return <Play className="h-4 w-4" />
  if (operationId.includes('knowledge')) return <BookOpen className="h-4 w-4" />
  if (operationId.includes('memory')) return <Brain className="h-4 w-4" />
  if (operationId.includes('learning')) return <GraduationCap className="h-4 w-4" />
  if (operationId.includes('qa')) return <ClipboardCheck className="h-4 w-4" />
  return <Sparkles className="h-4 w-4" />
}

function PlusCircleIcon() {
  return <Sparkles className="h-4 w-4" />
}

function ListIcon() {
  return <Wrench className="h-4 w-4" />
}

function lockedCapabilityReason(item: CapabilityItem, lens: AppGraphContextLens | null) {
  if (item.id === 'agent') {
    return 'Create Agent is available after authentication. Use the auth action chips in Corpus first.'
  }
  if (item.id === 'connect') {
    return 'Connect API needs an active SaaS Agent. Create or open an agent first.'
  }
  if (item.id === 'catalog' || item.id === 'actions') {
    return lens?.connection_count
      ? `${item.label} is waiting for the current connection to be activated.`
      : `${item.label} unlocks after Corpus connects and activates an API schema.`
  }
  if (item.id === 'execution') {
    return lens?.tool_count
      ? 'Execution is waiting for a valid execution plan from Corpus.'
      : 'Execution unlocks after activated API actions have generated runnable tools.'
  }
  if (item.id === 'knowledge' || item.id === 'memory' || item.id === 'learning' || item.id === 'qa') {
    return `${item.label} needs an active SaaS Agent context before RouteDeck can switch there.`
  }
  return `${item.label} is not legal from the current RouteDeck node. Corpus can move there once the graph prerequisites are met.`
}

function capabilityItems(): CapabilityItem[] {
  return [
    { id: 'home', label: 'Home', icon: <Home className="h-4 w-4" />, nodes: ['home'], operationId: 'navigate.home' },
    { id: 'agent', label: 'Create Agent', icon: <Sparkles className="h-4 w-4" />, nodes: ['saas_agent_select', 'saas_agent_create', 'agent_home'], operationId: 'saas_agent.create' },
    { id: 'connect', label: 'Connect API', icon: <Plug className="h-4 w-4" />, nodes: ['connection_configure', 'schema_preview'], operationId: 'navigate.connection_configure' },
    { id: 'catalog', label: 'Catalog', icon: <Database className="h-4 w-4" />, nodes: ['catalog_activation', 'catalog'], operationId: 'catalog.open' },
    { id: 'actions', label: 'Actions', icon: <Wrench className="h-4 w-4" />, nodes: ['entities', 'actions'], operationId: 'actions.open' },
    { id: 'execution', label: 'Execution', icon: <Play className="h-4 w-4" />, nodes: ['execution_planning', 'needs_input', 'approval_required', 'executing', 'result_review'], operationId: 'execution.open' },
    { id: 'knowledge', label: 'Knowledge', icon: <BookOpen className="h-4 w-4" />, nodes: ['knowledge'], operationId: 'knowledge.open' },
    { id: 'memory', label: 'Memory', icon: <Brain className="h-4 w-4" />, nodes: ['memory'], operationId: 'memory.open' },
    { id: 'learning', label: 'Learning', icon: <GraduationCap className="h-4 w-4" />, nodes: ['learning'], operationId: 'learning.open' },
    { id: 'qa', label: 'QA', icon: <ClipboardCheck className="h-4 w-4" />, nodes: ['qa'], operationId: 'qa.open' },
  ]
}

function surfaceMatchesExpected(
  surface: RouteDeckSurface | null,
  expected?: CorpusExpectedActiveSurface | null,
) {
  if (!surface || !expected) return false
  if (expected.name && surface.name !== expected.name) return false
  if (expected.component && surface.component !== expected.component) return false
  if (expected.variant && surface.variant !== expected.variant) return false
  if (expected.role && surface.role !== expected.role) return false
  return true
}

function proposalFields(proposal: CorpusProposal): ProposalField[] {
  const fields = proposal.input_schema?.fields
  return Array.isArray(fields) ? (fields as ProposalField[]) : []
}

function proposalDefaults(proposal: CorpusProposal) {
  const values = { ...(proposal.args || {}) }
  for (const field of proposalFields(proposal)) {
    if (!(field.key in values) && field.default !== undefined) {
      values[field.key] = field.default
    }
  }
  return values
}

function handleProposalFieldChange(
  key: string,
  event: ChangeEvent<HTMLInputElement>,
  setValues: React.Dispatch<React.SetStateAction<Record<string, unknown>>>,
) {
  setValues((current) => ({ ...current, [key]: event.target.value }))
}

function displayWork(value: string) {
  const labels: Record<string, string> = {
    home: 'Home',
    auth_sign_in: 'Sign in',
    auth_register: 'Create account',
    saas_agent_select: 'Select SaaS Agent',
    saas_agent_create: 'Create SaaS Agent',
    agent_home: 'SaaS Agent Home',
    connection_configure: 'Connect API',
    schema_preview: 'Schema Preview',
    catalog_activation: 'Catalog Activation',
    catalog: 'Catalog',
    entities: 'Entities',
    actions: 'Actions',
    execution_planning: 'Execution Planning',
    needs_input: 'Needs Input',
    approval_required: 'Approval Required',
    executing: 'Executing',
    result_review: 'Result Review',
    knowledge: 'Knowledge',
    memory: 'Memory',
    learning: 'Learning',
    qa: 'QA',
    recovery: 'Recovery',
    lounge: 'Lounge',
  }
  if (labels[value]) return labels[value]
  return value
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}
