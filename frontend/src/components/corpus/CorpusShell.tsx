import { useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  RouteDeckProvider,
  routeDeckOperationInteraction,
  useRouteDeckDispatch,
  useRouteDeckProjection,
  useRouteDeckState,
  useRouteDeckStore,
  type RouteDeckEvent,
  type RouteDeckOperation,
  type RouteDeckProjection,
  type RouteDeckStore,
} from '@routedeck/react'
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Bot,
  Brain,
  CheckCircle2,
  Circle,
  ClipboardCheck,
  Database,
  GraduationCap,
  Home,
  Loader2,
  Lock,
  LogOut,
  Play,
  Plug,
  Sparkles,
  User,
  Wrench,
  X,
} from 'lucide-react'

import { CommandComposer } from '@/components/agent/CommandComposer'
import { MessageBubble } from '@/components/agent/MessageBubble'
import { ThemeToggleButton } from '@/components/theme/ThemeToggleButton'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { useSaaSAgentUiStore } from '@/stores/saasAgentUiStore'
import type { ChatUIMessage } from '@/types/agent'
import type { CorpusContextLens, CorpusGraphState } from '@/types/corpus'
import type { CorpusStateResponse } from '@/types/corpus'
import type { AgentApproval, AgentApprovalDecision, SaaSAgent, SaaSAgentDeployment } from '@/types/domain'
import { CorpusRouteDeckDiagnostics as DiagnosticsPanel } from './CorpusRouteDeckDiagnostics'
import {
  ActiveSurfacePanel,
} from './corpusActiveSurfaces'
import { FrameSurfacePanel } from './corpusFrameSurfaces'
import {
  type ActiveSurfaceDirtyState,
  activeSurfaceFromProjection,
  contextLensFromProjection,
} from './corpusSurfaces'
import {
  corpusQuickActions,
  operationToQuickAction,
  type CorpusQuickAction,
} from './corpusOperations'
import {
  activeSaaSAgentIdFromRouteDeckState,
  corpusLocationFromBrowser,
  corpusPathFromLocation,
  corpusPathFromRouteDeckState,
  corpusStatePath,
  createSaaStoAgentRouteDeckStore,
  graphStateFromRouteDeckState,
  SURFACE_QUERY_KEY,
} from './corpusRouteDeckClient'
import { corpusNodeIds, corpusOperationIds, corpusSurfaceComponents } from './corpusRouteDeckCatalog'
import { displayWork } from './workbenchDisplay'

interface CorpusShellProps {
  nodeId?: string
  saasAgentId?: string
}

type WorkbenchStatus =
  | 'Ready'
  | 'Thinking'
  | 'Navigating'
  | 'Opening surface'
  | 'Committing'
  | 'Running diagnostics'
  | 'Waiting for input'
  | 'Waiting for approval'
  | 'Needs attention'

interface CapabilityItem {
  id: string
  label: string
  icon: ReactNode
  nodes: string[]
  childNodes: string[]
  operationId?: string
}

interface RailSelectionNotice {
  label: string
  state: 'active' | 'locked'
  message: string
}

interface PendingSurfaceTransition {
  nextStatus: WorkbenchStatus
  run: () => void
}

let cachedRouteDeckStore: RouteDeckStore | null = null

function clearCachedRouteDeckStore() {
  cachedRouteDeckStore = null
}

export function CorpusShell({ nodeId, saasAgentId }: CorpusShellProps) {
  const location = useLocation()
  const surfaceId = useMemo(() => new URLSearchParams(location.search).get(SURFACE_QUERY_KEY), [location.search])
  const statePath = useMemo(() => corpusStatePath(nodeId, saasAgentId, surfaceId), [nodeId, saasAgentId, surfaceId])
  const [routeDeckStore, setRouteDeckStore] = useState<RouteDeckStore | null>(() => cachedRouteDeckStore)

  const stateQuery = useQuery({
    queryKey: ['corpus-state', nodeId || 'home', saasAgentId || 'none', surfaceId || 'default'],
    queryFn: () => api.get<CorpusStateResponse>(statePath),
  })

  useEffect(() => {
    if (!stateQuery.data) return
    setRouteDeckStore((current) =>
      current || (() => {
        const store = createSaaStoAgentRouteDeckStore({
          initialState: stateQuery.data,
          statePath,
          nodeId,
          saasAgentId,
        })
        cachedRouteDeckStore = store
        return store
      })(),
    )
  }, [nodeId, saasAgentId, statePath, stateQuery.data])

  useEffect(() => {
    if (routeDeckStore) cachedRouteDeckStore = routeDeckStore
  }, [routeDeckStore])

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
      <CorpusShellRuntime nodeId={nodeId} saasAgentId={saasAgentId} />
    </RouteDeckProvider>
  )
}

function CorpusShellRuntime({ nodeId, saasAgentId }: CorpusShellProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const routeDeckState = useRouteDeckState()
  const routeDeckStore = useRouteDeckStore()
  const dispatchRouteDeck = useRouteDeckDispatch()
  const projection = useRouteDeckProjection()
  const { user, logout } = useAuth()
  const queryClient = useQueryClient()
  const graphState = graphStateFromRouteDeckState(routeDeckState)
  const activeSaaSAgentId = activeSaaSAgentIdFromRouteDeckState(routeDeckState)
  const replacePath = routeDeckState.location || null
  const setMirroredSaaSAgentId = useSaaSAgentUiStore((state) => state.setMirroredSaaSAgentId)
  const [chatMessages, setChatMessages] = useState<ChatUIMessage[]>(() => [
    makeAgentMessage(
      'assistant',
      'Hi. I can explain the platform, help you set up an agent, and open the right workflow when you ask.',
    ),
  ])
  const [draft, setDraft] = useState('')
  const [corpusStatus, setCorpusStatus] = useState<WorkbenchStatus>('Ready')
  const [railNotice, setRailNotice] = useState<RailSelectionNotice | null>(null)
  const [activeSurfaceDirtyState, setActiveSurfaceDirtyState] = useState<ActiveSurfaceDirtyState | null>(null)
  const [pendingSurfaceTransition, setPendingSurfaceTransition] = useState<PendingSurfaceTransition | null>(null)
  const [surfaceTransitionBusy, setSurfaceTransitionBusy] = useState(false)
  const activeSurface = activeSurfaceFromProjection(projection)
  const quickActions = useMemo(() => corpusQuickActions(projection), [projection])
  const contextLens = contextLensFromProjection(projection)
  const activeSurfaceId = activeSurface?.surface_id || 'none'
  const activeNodeDirtyPolicy = dirtyPolicyForNode(projection, projection.graph_node)
  const browserUrl = `${location.pathname}${location.search}`
  const ignoreBrowserLocationRef = useRef<string | null>(null)

  useEffect(() => {
    if (!projection || !graphState) return
    setMirroredSaaSAgentId(activeSaaSAgentId)
  }, [activeSaaSAgentId, graphState, projection, setMirroredSaaSAgentId])

  useEffect(() => {
    setActiveSurfaceDirtyState((current) => (current?.surfaceId === activeSurfaceId ? current : null))
  }, [activeSurfaceId])

  useEffect(() => {
    const nextPath = replacePath || corpusPathFromRouteDeckState(routeDeckState)
    if (!nextPath || nextPath === browserUrl) return
    if (ignoreBrowserLocationRef.current === nextPath) return
    ignoreBrowserLocationRef.current = nextPath
    navigate(nextPath)
  }, [browserUrl, navigate, replacePath, routeDeckState])

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
      setCorpusStatus('Ready')
      setMirroredSaaSAgentId(nextGraphState?.active_saas_agent_id || null)
      if (response.messages && response.messages.length > 0) {
        setChatMessages((current) => [
          ...current,
          ...response.messages.map((message) => makeAgentMessage('assistant', String(message.content || ''))),
        ])
      }
    },
  })

  const turn = useMutation({
    mutationFn: async (userInput: string) => {
      const currentGraphState = graphStateFromRouteDeckState(routeDeckStore.getState()) || graphState
      const params = new URLSearchParams({ user_input: userInput })
      const streamNodeId = currentGraphState?.node === corpusNodeIds.home && saasAgentId
        ? corpusNodeIds.agentHome
        : currentGraphState?.node
      if (streamNodeId) params.set('node_id', streamNodeId)
      if (currentGraphState?.active_saas_agent_id) {
        params.set('saas_agent_id', currentGraphState.active_saas_agent_id)
      } else if (activeSaaSAgentId) {
        params.set('saas_agent_id', activeSaaSAgentId)
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
        if (eventType === 'operation_completed') {
          setCorpusStatus('Committing')
          const nextProjection = payload.projection as RouteDeckProjection | undefined
          if (nextProjection) {
            const nextState = payload.state as CorpusGraphState | undefined
            routeDeckStore.receiveEvent(routeDeckEvent)
            setMirroredSaaSAgentId(nextState?.active_saas_agent_id || null)
            if (payload.operation_id === corpusOperationIds.saveDeployment && nextState?.active_saas_agent_id) {
              void queryClient.invalidateQueries({ queryKey: ['saas-agent-deployment', nextState.active_saas_agent_id] })
            }
          }
          const completedMessages = Array.isArray(payload.messages) ? payload.messages : []
          if (completedMessages.length > 0) {
            setChatMessages((current) => [
              ...current,
              ...completedMessages.map((message) =>
                makeAgentMessage('assistant', String((message as { content?: unknown }).content || '')),
              ),
            ])
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
  const authSurfaceActive = activeSurface?.component === corpusSurfaceComponents.auth
  const reviewSurfaceActive = activeSurface?.component === corpusSurfaceComponents.operationReview
  const composerDisabled = executeOperation.isPending || turn.isPending || authSurfaceActive
  const visibleStatus: WorkbenchStatus = executeOperation.isPending
      ? 'Committing'
      : reviewSurfaceActive
        ? 'Waiting for input'
        : contextLens?.pending_trace_id
          ? 'Waiting for approval'
          : corpusStatus
  const composerPlaceholder = authSurfaceActive
    ? 'Complete authentication in the active surface'
    : 'Message Corpus'

  const sendChatTurn = () => {
    const value = draft.trim()
    if (!value || composerDisabled) return
    setDraft('')
    setChatMessages((current) => [...current, makeAgentMessage('user', value)])
    turn.mutate(value)
  }

  const requestSurfaceTransition = (run: () => void, nextStatus: WorkbenchStatus) => {
    if (
      activeNodeDirtyPolicy === 'confirm' &&
      activeSurfaceDirtyState?.dirty &&
      activeSurfaceDirtyState.surfaceId === activeSurfaceId
    ) {
      setPendingSurfaceTransition({ nextStatus, run })
      return
    }
    setCorpusStatus(nextStatus)
    run()
  }

  const confirmSurfaceTransition = async (mode: 'save' | 'discard') => {
    const transition = pendingSurfaceTransition
    if (!transition) return
    if (mode === 'save' && activeSurfaceDirtyState?.save) {
      setSurfaceTransitionBusy(true)
      const saved = await activeSurfaceDirtyState.save()
      setSurfaceTransitionBusy(false)
      if (!saved) return
    }
    setPendingSurfaceTransition(null)
    setCorpusStatus(transition.nextStatus)
    transition.run()
  }

  const openReviewSurface = (operation: CorpusQuickAction['operation']) => {
    requestSurfaceTransition(() => {
      executeOperation.mutate({ operationId: operation.id, args: operation.payload || {} })
    }, 'Opening surface')
  }

  useEffect(() => {
    if (!graphState) return
    if (ignoreBrowserLocationRef.current === browserUrl) {
      ignoreBrowserLocationRef.current = null
      return
    }
    if (ignoreBrowserLocationRef.current) return
    const currentPath = replacePath || corpusPathFromRouteDeckState(routeDeckState)
    if (!currentPath || browserUrl === currentPath) return

    const currentAgentId = graphState.active_saas_agent_id || null
    const backLocation = projection.navigation.back_stack.at(-1)
    const forwardLocation = projection.navigation.forward_stack[0]
    const backPath = backLocation ? corpusPathFromLocation(backLocation, currentAgentId) : null
    const forwardPath = forwardLocation ? corpusPathFromLocation(forwardLocation, currentAgentId) : null

    const dispatchBrowserLocation = () => {
      if (browserUrl === backPath) {
        void routeDeckStore.back().finally(() => setCorpusStatus('Ready'))
        return
      }
      if (browserUrl === forwardPath) {
        void routeDeckStore.forward().finally(() => setCorpusStatus('Ready'))
        return
      }
      const nextLocation = corpusLocationFromBrowser(location.pathname, location.search)
      if (!nextLocation) return
      void dispatchRouteDeck({
        operation_id: 'route.open_node',
        args: {
          node_id: nextLocation.node_id,
          surface_id: nextLocation.surface_id,
          params: {
            ...(projection.navigation.current.params || {}),
            ...(nextLocation.params || {}),
          },
        },
      }).finally(() => setCorpusStatus('Ready'))
    }

    if (
      activeNodeDirtyPolicy === 'confirm' &&
      activeSurfaceDirtyState?.dirty &&
      activeSurfaceDirtyState.surfaceId === activeSurfaceId
    ) {
      ignoreBrowserLocationRef.current = currentPath
      navigate(currentPath, { replace: true })
      setPendingSurfaceTransition({ nextStatus: 'Navigating', run: dispatchBrowserLocation })
      return
    }

    dispatchBrowserLocation()
  }, [
    activeNodeDirtyPolicy,
    activeSurfaceDirtyState,
    activeSurfaceId,
    browserUrl,
    dispatchRouteDeck,
    graphState,
    location.pathname,
    location.search,
    navigate,
    projection.navigation.back_stack,
    projection.navigation.current.params,
    projection.navigation.forward_stack,
    replacePath,
    routeDeckState,
    routeDeckStore,
  ])

  const handleQuickAction = (action: CorpusQuickAction) => {
    setRailNotice(null)
    const operation = action.operation
    if (operation.can_dispatch_now === false) {
      const interaction = routeDeckOperationInteraction(operation)
      if (interaction === 'form') {
        openReviewSurface(operation)
        return
      }
      setChatMessages((current) => [
        ...current,
        makeAgentMessage(
          'assistant',
          interaction === 'entity_selector'
            ? 'Choose a SaaS Agent from the dashboard first, then I can open it.'
            : 'That action needs one more detail before I can run it.',
        ),
      ])
      setCorpusStatus('Ready')
      return
    }
    if (operation.execution_mode === 'review' || operation.kind === 'form') {
      openReviewSurface(operation)
      return
    }
    requestSurfaceTransition(
      () => executeOperation.mutate({ operationId: operation.id, args: operation.payload || {} }),
      operation.target_node && operation.target_node !== projection.graph_node ? 'Navigating' : 'Committing',
    )
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
          ? `${item.label} is already the active workflow. Corpus will keep working in the current surface.`
          : lockedCapabilityReason(item, contextLens),
    })
  }

  const handleLogout = () => {
    logout()
    clearCachedRouteDeckStore()
    setMirroredSaaSAgentId(null)
    void routeDeckStore.refresh().catch(() => undefined)
  }

  return (
    <div className="workbench-canvas">
      <WorkbenchTopbar
        projection={projection}
        contextLens={contextLens}
        status={visibleStatus}
        user={user}
        onBack={() =>
          requestSurfaceTransition(
            () => {
              void routeDeckStore.back().finally(() => setCorpusStatus('Ready'))
            },
            'Navigating',
          )
        }
        onForward={() =>
          requestSurfaceTransition(
            () => {
              void routeDeckStore.forward().finally(() => setCorpusStatus('Ready'))
            },
            'Navigating',
          )
        }
        onCancel={() =>
          requestSurfaceTransition(
            () => {
              void routeDeckStore.cancel().finally(() => setCorpusStatus('Ready'))
            },
            'Navigating',
          )
        }
        onLogout={handleLogout}
      />

      <div className="relative grid min-h-[calc(100vh-5.25rem)] gap-4 px-4 pb-4 lg:h-[calc(100vh-5.25rem)] lg:grid-cols-[16rem_minmax(0,1fr)_22rem] lg:overflow-hidden">
        <CapabilityRail projection={projection} graphState={graphState} contextLens={contextLens} onSelect={handleRailSelect} />

        <main className="min-w-0 lg:min-h-0 lg:overflow-hidden">
          <AgentConversation
            messages={chatMessages}
            draft={draft}
            busy={executeOperation.isPending || (turn.isPending && !hasStreamingCorpusMessage)}
            composerDisabled={composerDisabled}
            composerPlaceholder={composerPlaceholder}
            status={visibleStatus}
            error={turn.error || executeOperation.error}
            quickActions={quickActions}
            activeSurfacePanel={
              <ActiveSurfacePanel
                projection={projection}
                graphState={graphState}
                busy={executeOperation.isPending}
                onOperationSubmit={(operationId, args) => executeOperation.mutate({ operationId, args })}
                onDirtyStateChange={setActiveSurfaceDirtyState}
              />
            }
            activeSurfaceKey={activeSurface ? `${activeSurface.component}:${activeSurface.variant}` : 'none'}
            onDraftChange={setDraft}
            onSend={sendChatTurn}
            onQuickAction={handleQuickAction}
            pendingSurfaceTransition={pendingSurfaceTransition}
            surfaceTransitionBusy={surfaceTransitionBusy}
            onSaveAndContinue={() => void confirmSurfaceTransition('save')}
            onContinueWithoutSaving={() => void confirmSurfaceTransition('discard')}
            onStayOnSurface={() => setPendingSurfaceTransition(null)}
          />
        </main>

        <aside className="workbench-panel min-w-0 p-4 dark:!bg-[rgba(26,27,30,0.8)] lg:min-h-0 lg:overflow-y-auto">
          <ContextPanel
            projection={projection}
            status={visibleStatus}
            railNotice={railNotice}
            operationBusy={executeOperation.isPending}
          />
          <DiagnosticsPanel
            projection={projection}
            graphState={graphState}
          />
        </aside>
      </div>
    </div>
  )
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
  onBack,
  onForward,
  onCancel,
  onLogout,
}: {
  projection: RouteDeckProjection
  contextLens: CorpusContextLens | null
  status: WorkbenchStatus
  user: { email?: string; display_name?: string | null } | null
  onBack: () => void
  onForward: () => void
  onCancel: () => void
  onLogout: () => void
}) {
  const currentWork = displayWork(contextLens?.working_on || projection.current_context)
  const navigation = projection.navigation
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
          <div className="hidden items-center gap-1 md:flex" data-testid="routedeck-global-navigation">
            <button
              type="button"
              onClick={onBack}
              disabled={!navigation.can_back}
              className="surface-outline-button inline-flex h-10 w-10 items-center justify-center p-0 disabled:cursor-not-allowed disabled:opacity-45"
              title="Back"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={onForward}
              disabled={!navigation.can_forward}
              className="surface-outline-button inline-flex h-10 w-10 items-center justify-center p-0 disabled:cursor-not-allowed disabled:opacity-45"
              title="Forward"
            >
              <ArrowRight className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={onCancel}
              disabled={!navigation.can_cancel}
              className="surface-outline-button inline-flex h-10 w-10 items-center justify-center p-0 disabled:cursor-not-allowed disabled:opacity-45"
              title="Cancel"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
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
  const active = ['Thinking', 'Navigating', 'Opening surface', 'Committing', 'Running diagnostics'].includes(status)
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
  quickActions,
  activeSurfacePanel,
  activeSurfaceKey,
  pendingSurfaceTransition,
  surfaceTransitionBusy,
  onDraftChange,
  onSend,
  onQuickAction,
  onSaveAndContinue,
  onContinueWithoutSaving,
  onStayOnSurface,
}: {
  messages: ChatUIMessage[]
  draft: string
  busy: boolean
  composerDisabled: boolean
  composerPlaceholder: string
  status: WorkbenchStatus
  error: unknown
  quickActions: CorpusQuickAction[]
  activeSurfacePanel: ReactNode
  activeSurfaceKey: string
  pendingSurfaceTransition: PendingSurfaceTransition | null
  surfaceTransitionBusy: boolean
  onDraftChange: (value: string) => void
  onSend: () => void
  onQuickAction: (action: CorpusQuickAction) => void
  onSaveAndContinue: () => void
  onContinueWithoutSaving: () => void
  onStayOnSurface: () => void
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
  }, [messages.length, busy, activeSurfaceKey, error])

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
          </div>

          {pendingSurfaceTransition && (
            <SurfaceTransitionPrompt
              busy={surfaceTransitionBusy}
              onSaveAndContinue={onSaveAndContinue}
              onContinueWithoutSaving={onContinueWithoutSaving}
              onStayOnSurface={onStayOnSurface}
            />
          )}

          {activeSurfacePanel}

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
  graphState: CorpusGraphState | null
  contextLens: CorpusContextLens | null
  onSelect: (item: CapabilityItem, action: CorpusQuickAction | null, state: 'active' | 'ready' | 'locked') => void
}) {
  const operationsById = new Map(projection.legal_operations.map((operation) => [operation.id, operation]))
  const currentNode = graphState?.node || projection.graph_node
  const items = capabilityItems(projection)
  return (
    <nav className="workbench-panel hidden min-w-0 p-3 dark:!bg-[rgba(26,27,30,0.8)] lg:block" aria-label="Workflow switcher" data-testid="capability-rail">
      <div className="mb-3 px-3 pt-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">Workflows</div>
      <div className="space-y-2">
        {items.map((item) => {
          const operation = item.operationId ? operationsById.get(item.operationId) : undefined
          const active = item.nodes.includes(currentNode) || item.childNodes.includes(currentNode)
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

function SurfaceTransitionPrompt({
  busy,
  onSaveAndContinue,
  onContinueWithoutSaving,
  onStayOnSurface,
}: {
  busy: boolean
  onSaveAndContinue: () => void
  onContinueWithoutSaving: () => void
  onStayOnSurface: () => void
}) {
  return (
    <div className="mb-4 rounded-[0.9rem] border border-amber-300/60 bg-amber-50/90 p-5 shadow-[0_26px_64px_-42px_hsl(var(--foreground)/0.4)] dark:border-amber-700/50 dark:bg-amber-950/25">
      <div className="text-sm font-semibold text-foreground">Save changes before leaving this surface?</div>
      <p className="mt-2 text-sm text-muted-foreground">
        Your current surface has unsaved changes. Save them now, keep working here, or continue without saving.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onSaveAndContinue}
          disabled={busy}
          className="surface-solid-button disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? 'Saving...' : 'Save and continue'}
        </button>
        <button
          type="button"
          onClick={onContinueWithoutSaving}
          disabled={busy}
          className="surface-outline-button disabled:cursor-not-allowed disabled:opacity-50"
        >
          Continue without saving
        </button>
        <button
          type="button"
          onClick={onStayOnSurface}
          disabled={busy}
          className="surface-outline-button disabled:cursor-not-allowed disabled:opacity-50"
        >
          Stay here
        </button>
      </div>
    </div>
  )
}

function ContextPanel({
  projection,
  status,
  railNotice,
  operationBusy,
}: {
  projection: RouteDeckProjection
  status: WorkbenchStatus
  railNotice: RailSelectionNotice | null
  operationBusy: boolean
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
            Workflow switcher: {railNotice.label}
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
      {lens?.selected_saas_agent_id && lens.selected_saas_agent_slug && (
        <>
          <DeploymentCard
            saasAgentId={lens.selected_saas_agent_id}
            slug={lens.selected_saas_agent_slug}
            busy={operationBusy}
          />
          <PendingApprovalsCard
            saasAgentId={lens.selected_saas_agent_id}
            enabled={true}
          />
        </>
      )}
    </section>
  )
}

function DeploymentCard({
  saasAgentId,
  slug,
  busy,
}: {
  saasAgentId: string
  slug: string
  busy: boolean
}) {
  const agentApi = api.withSaaSAgent(saasAgentId)
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState<SaaSAgentDeployment | null>(null)
  const deployUrl = `${window.location.origin}/a/${slug}`
  const query = useQuery({
    queryKey: ['saas-agent-deployment', saasAgentId],
    queryFn: () => agentApi.get<SaaSAgentDeployment>(`/saas-agents/${saasAgentId}/deployment`),
    enabled: Boolean(saasAgentId),
  })
  const saveDeployment = useMutation({
    mutationFn: (payload: Pick<SaaSAgentDeployment, 'enabled' | 'visitor_auth_mode' | 'execution_mode' | 'default_write_policy' | 'welcome_message'>) =>
      agentApi.put<SaaSAgentDeployment>(`/saas-agents/${saasAgentId}/deployment`, payload),
    onSuccess: (saved) => {
      setDraft(saved)
      void queryClient.invalidateQueries({ queryKey: ['saas-agent-deployment', saasAgentId] })
    },
  })

  useEffect(() => {
    if (query.data) setDraft(query.data)
  }, [query.data])

  if (query.isLoading || !draft) {
    return (
      <div className="mt-4 rounded-xl border border-border/25 bg-card/70 p-3 text-xs text-muted-foreground">
        Loading deployment settings...
      </div>
    )
  }

  return (
    <div className="mt-4 rounded-xl border border-border/25 bg-card/80 p-3 text-xs shadow-sm" data-testid="deployment-settings-card">
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="font-semibold text-foreground">Deployed chat URL</div>
          <a className="mt-1 block truncate font-mono text-[11px] text-primary" href={deployUrl} target="_blank" rel="noreferrer">
            {deployUrl}
          </a>
        </div>
        <label className="flex items-center gap-2 text-muted-foreground">
          <input
            type="checkbox"
            checked={draft.enabled}
            data-qa-field="enabled"
            onChange={(event) => setDraft({ ...draft, enabled: event.target.checked })}
          />
          Enabled
        </label>
      </div>
      <label className="mt-3 block">
        <span className="text-muted-foreground">Access</span>
        <select
          className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1"
          value={draft.visitor_auth_mode}
          data-qa-field="visitor_auth_mode"
          onChange={(event) => setDraft({ ...draft, visitor_auth_mode: event.target.value as SaaSAgentDeployment['visitor_auth_mode'] })}
        >
          <option value="inherit_from_connection">Inherit from connection</option>
          <option value="anonymous">Anonymous allowed</option>
          <option value="login_required">Login required</option>
        </select>
      </label>
      <label className="mt-3 block">
        <span className="text-muted-foreground">Execution mode</span>
        <select
          className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1"
          value={draft.execution_mode}
          data-qa-field="execution_mode"
          onChange={(event) => setDraft({ ...draft, execution_mode: event.target.value as SaaSAgentDeployment['execution_mode'] })}
        >
          <option value="sandbox">Sandbox</option>
          <option value="live">Live</option>
        </select>
      </label>
      <label className="mt-3 block">
        <span className="text-muted-foreground">Write policy</span>
        <select
          className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1"
          value={draft.default_write_policy}
          data-qa-field="default_write_policy"
          onChange={(event) => setDraft({ ...draft, default_write_policy: event.target.value as SaaSAgentDeployment['default_write_policy'] })}
        >
          <option value="confirm">Confirm before writes</option>
          <option value="owner_approval">Owner approval</option>
          <option value="block">Block writes</option>
        </select>
      </label>
      <label className="mt-3 block">
        <span className="text-muted-foreground">Welcome message</span>
        <textarea
          className="mt-1 min-h-16 w-full rounded-md border border-input bg-background px-2 py-1"
          value={draft.welcome_message}
          data-qa-field="welcome_message"
          onChange={(event) => setDraft({ ...draft, welcome_message: event.target.value })}
        />
      </label>
      {saveDeployment.isError && (
        <div className="mt-2 rounded-md bg-destructive/10 px-2 py-1 text-destructive">
          Deployment settings could not be saved.
        </div>
      )}
      <button
        type="button"
        onClick={() => {
          if (!draft) return
          saveDeployment.mutate({
            enabled: draft.enabled,
            visitor_auth_mode: draft.visitor_auth_mode,
            execution_mode: draft.execution_mode,
            default_write_policy: draft.default_write_policy,
            welcome_message: draft.welcome_message,
          })
        }}
        disabled={busy || saveDeployment.isPending}
        className="surface-solid-button mt-3 w-full rounded-md px-3 py-2"
      >
        {busy || saveDeployment.isPending ? 'Saving...' : 'Save deployment'}
      </button>
    </div>
  )
}

function PendingApprovalsCard({ saasAgentId, enabled }: { saasAgentId: string; enabled: boolean }) {
  const agentApi = api.withSaaSAgent(saasAgentId)
  const query = useQuery({
    queryKey: ['saas-agent-approvals', saasAgentId],
    queryFn: () => agentApi.get<AgentApproval[]>(`/saas-agents/${saasAgentId}/approvals/pending`),
    enabled: enabled && Boolean(saasAgentId),
    refetchInterval: enabled ? 2000 : false,
  })
  const decide = useMutation({
    mutationFn: ({ traceId, decision }: { traceId: string; decision: 'approve' | 'cancel' }) => {
      const path =
        decision === 'approve'
          ? `/saas-agents/${saasAgentId}/approvals/${traceId}/approve`
          : `/saas-agents/${saasAgentId}/approvals/${traceId}/cancel`
      return agentApi.post<AgentApprovalDecision>(path)
    },
    onSuccess: () => {
      void query.refetch()
    },
  })

  const approvals = query.data || []
  if (!enabled) return null
  if (query.isLoading || approvals.length === 0) return null

  return (
    <div className="mt-4 rounded-xl border border-amber-300/60 bg-amber-50/80 p-3 text-xs shadow-sm dark:border-amber-700/50 dark:bg-amber-950/20" data-testid="pending-approvals-card">
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="font-semibold text-foreground">Pending owner approvals</div>
          <p className="mt-1 text-muted-foreground">{approvals.length} deployed chat request waiting.</p>
        </div>
        <ClipboardCheck className="h-4 w-4 text-amber-700 dark:text-amber-300" />
      </div>
      <div className="mt-3 space-y-3">
        {approvals.map((approval) => (
          <div key={approval.trace_id} className="rounded-lg border border-border/30 bg-background/80 p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="truncate font-mono text-[11px] text-foreground">
                  {approval.method} {approval.path}
                </div>
                <div className="mt-1 text-muted-foreground">
                  {approval.tool_name} - {approval.risk_level || 'write'} - {approval.trace_token}
                </div>
              </div>
            </div>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                disabled={decide.isPending}
                onClick={() => decide.mutate({ traceId: approval.trace_id, decision: 'approve' })}
                className="surface-solid-button flex-1 rounded-md px-3 py-1.5"
              >
                Approve
              </button>
              <button
                type="button"
                disabled={decide.isPending}
                onClick={() => decide.mutate({ traceId: approval.trace_id, decision: 'cancel' })}
                className="surface-outline-button flex-1 rounded-md px-3 py-1.5"
              >
                Cancel
              </button>
            </div>
          </div>
        ))}
      </div>
      {decide.error && (
        <div className="mt-2 rounded-md bg-red-50 px-2 py-1 text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {decide.error instanceof Error ? decide.error.message : 'Approval update failed.'}
        </div>
      )}
    </div>
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


function lockedCapabilityReason(item: CapabilityItem, lens: CorpusContextLens | null) {
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
    return `${item.label} needs an active SaaS Agent context before Corpus can switch there.`
  }
  return `${item.label} is not available from the current workflow. Corpus can move there once the graph prerequisites are met.`
}

function dirtyPolicyForNode(projection: RouteDeckProjection, nodeId: string) {
  const hierarchy = projection.diagnostics?.node_hierarchy
  if (!hierarchy || typeof hierarchy !== 'object') return 'none'
  const node = (hierarchy as Record<string, unknown>)[nodeId]
  if (!node || typeof node !== 'object') return 'none'
  const dirtyPolicy = (node as Record<string, unknown>).dirty_policy
  return dirtyPolicy === 'confirm' || dirtyPolicy === 'block' ? dirtyPolicy : 'none'
}

function capabilityItems(projection: RouteDeckProjection): CapabilityItem[] {
  const projected = Array.isArray(projection.diagnostics?.capability_rail)
    ? projection.diagnostics.capability_rail
    : []
  return projected
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object')
    .map((item) => {
      const id = String(item.id || '')
      const iconKey = typeof item.icon_key === 'string' ? item.icon_key : id
      return {
        id,
        label: String(item.label || id),
        icon: capabilityIcon(iconKey),
        nodes: Array.isArray(item.nodes) ? item.nodes.map(String) : [],
        childNodes: Array.isArray(item.child_nodes) ? item.child_nodes.map(String) : [],
        operationId: typeof item.operation_id === 'string' ? item.operation_id : undefined,
      }
    })
}

function capabilityIcon(iconKey: string): ReactNode {
  const className = 'h-4 w-4'
  switch (iconKey) {
    case 'home':
      return <Home className={className} />
    case 'sparkles':
      return <Sparkles className={className} />
    case 'plug':
      return <Plug className={className} />
    case 'database':
      return <Database className={className} />
    case 'wrench':
      return <Wrench className={className} />
    case 'play':
      return <Play className={className} />
    case 'book':
      return <BookOpen className={className} />
    case 'brain':
      return <Brain className={className} />
    case 'graduation':
      return <GraduationCap className={className} />
    case 'clipboard':
      return <ClipboardCheck className={className} />
    default:
      return <Circle className={className} />
  }
}
