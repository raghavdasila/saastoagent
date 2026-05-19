import { useEffect, useMemo, useState } from 'react'
import type { ChangeEvent, ReactNode } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
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
  type RouteDeckProjection,
  type RouteDeckStore,
  type RouteDeckSurface,
} from '@routedeck/react'
import {
  Activity,
  AlertTriangle,
  Bot,
  Boxes,
  FileText,
  KeyRound,
  Loader2,
  Play,
  ShieldCheck,
} from 'lucide-react'

import { AdminPanel } from '@/components/agent/AdminPanel'
import { AttachmentsPanel } from '@/components/agent/AttachmentsPanel'
import { CommandComposer } from '@/components/agent/CommandComposer'
import { LearningPanel } from '@/components/agent/LearningPanel'
import { MessageBubble } from '@/components/agent/MessageBubble'
import { AuthAgentDesk } from '@/components/auth/AuthAgentDesk'
import { ActionsCanvas } from '@/components/saasAgent/ActionsCanvas'
import { EntitiesCanvas } from '@/components/saasAgent/EntitiesCanvas'
import { QAAgentPanel } from '@/components/qa/QAAgentPanel'
import { ThemeToggleButton } from '@/components/theme/ThemeToggleButton'
import { api } from '@/lib/api'
import { useSaaSAgentStore } from '@/stores/saasAgentStore'
import type { ChatUIMessage } from '@/types/agent'
import type { AppGraphContextLens, AppGraphState } from '@/types/appGraph'
import type { CorpusActionResponse, CorpusDiagnosticsSnapshot, CorpusProposal, CorpusStateResponse } from '@/types/corpus'
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

  useEffect(() => {
    if (!projection || !graphState) return
    setSaaSAgentId(graphState.active_saas_agent_id || null)
    if (replacePath && replacePath !== window.location.pathname) {
      replaceBrowserPath(replacePath)
    }
  }, [graphState, projection, replacePath, setSaaSAgentId])

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
      const params = new URLSearchParams({ user_input: userInput })
      if (nodeId) params.set('node_id', nodeId)
      if (saasAgentId) params.set('saas_agent_id', saasAgentId)
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

      setPendingProposal(null)

      await api.getStream(`/corpus/stream?${params.toString()}`, (eventType, eventData) => {
        const payload = (eventData.payload || {}) as Record<string, unknown>
        if (eventType === 'corpus_status') {
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
          setPendingProposal(payload as unknown as CorpusProposal)
          finishStreamingMessage()
        }
        if (eventType === 'operation_completed') {
          const nextProjection = payload.projection as RouteDeckProjection | undefined
          if (nextProjection) {
            const nextState = payload.state as AppGraphState | undefined
            routeDeckStore.receiveEvent(eventData as unknown as RouteDeckEvent)
            setSaaSAgentId(nextState?.active_saas_agent_id || null)
          }
          const nextPath = typeof payload.replace_path === 'string' ? payload.replace_path : null
          if (nextPath && nextPath !== window.location.pathname) {
            replaceBrowserPath(nextPath)
          }
          finishStreamingMessage()
        }
        if (eventType === 'projection_update') {
          routeDeckStore.receiveEvent(eventData as unknown as RouteDeckEvent)
        }
        if (eventType === 'corpus_done') {
          finishStreamingMessage()
        }
        if (eventType === 'corpus_error') {
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

  const sendChatTurn = () => {
    const value = draft.trim()
    if (!value || turn.isPending || executeOperation.isPending) return
    setDraft('')
    setChatMessages((current) => [...current, makeAgentMessage('user', value)])
    turn.mutate(value)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 dark:bg-background dark:text-white">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-white/10 dark:bg-[#09090b]/90">
        <div className="flex min-h-14 items-center justify-between gap-3 px-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <Bot className="h-5 w-5 shrink-0 text-sky-600" />
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold">SaaStoAgent</div>
              <div className="truncate text-xs text-slate-500">
                {displayWork(contextLensFromProjection(projection)?.working_on || projection.current_context)}
              </div>
            </div>
          </div>
          <ThemeToggleButton />
        </div>
      </header>

      <div className="grid min-h-[calc(100vh-3.5rem)] lg:grid-cols-[minmax(0,1fr)_22rem]">
        <main className="min-w-0">
          <AgentConversation
            messages={chatMessages}
            draft={draft}
            busy={executeOperation.isPending || (turn.isPending && !hasStreamingCorpusMessage)}
            error={turn.error || executeOperation.error}
            pendingProposal={pendingProposal}
            onDraftChange={setDraft}
            onSend={sendChatTurn}
            onProposalAccept={(args) =>
              pendingProposal &&
              executeOperation.mutate({ operationId: pendingProposal.operation_id, args })
            }
            onProposalDismiss={() => setPendingProposal(null)}
          />
          <ActiveSurfacePanel projection={projection} graphState={graphState} />
        </main>

        <aside className="border-t border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-[#09090b] lg:border-l lg:border-t-0">
          <ContextPanel projection={projection} />
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
        node_id: nodeId || graphState.node,
        saas_agent_id: saasAgentId || graphState.active_saas_agent_id,
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

function AgentConversation({
  messages,
  draft,
  busy,
  error,
  pendingProposal,
  onDraftChange,
  onSend,
  onProposalAccept,
  onProposalDismiss,
}: {
  messages: ChatUIMessage[]
  draft: string
  busy: boolean
  error: unknown
  pendingProposal: CorpusProposal | null
  onDraftChange: (value: string) => void
  onSend: () => void
  onProposalAccept: (args: Record<string, unknown>) => void
  onProposalDismiss: () => void
}) {
  return (
    <section className="border-b border-slate-200 bg-slate-50 dark:border-white/10 dark:bg-[#08080a]" data-testid="app-agent-chat">
      <div className="mx-auto flex min-h-[28rem] max-w-5xl flex-col px-4 py-4 sm:px-6">
        <div className="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 dark:border-white/10">
          <div>
            <h1 className="text-lg font-semibold">Corpus</h1>
            <p className="mt-1 text-sm text-slate-500">Tell Corpus what to set up, inspect, or run.</p>
          </div>
          <Activity className="h-5 w-5 text-slate-400" />
        </div>

        <div className="py-4">
          <FrameSurfacePanel />
        </div>

        <div className="flex-1 overflow-y-auto py-3">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
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

        {pendingProposal && (
          <ProposalPanel
            proposal={pendingProposal}
            busy={busy}
            onAccept={onProposalAccept}
            onDismiss={onProposalDismiss}
          />
        )}

        {error && (
          <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
            {error instanceof Error ? error.message : 'Corpus could not complete that step.'}
          </div>
        )}

        <CommandComposer
          value={draft}
          onChange={onDraftChange}
          onSend={onSend}
          placeholder="Message Corpus"
          disabled={busy}
        />
      </div>
    </section>
  )
}

function FrameSurfacePanel() {
  const projection = useRouteDeckProjection()
  const surface = useRouteDeckSurface('main')
  const contextLens = contextLensFromProjection(projection)
  if (!surface) return null

  if (surface.component === 'CorpusLoungeSurface') {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
        <div className="text-sm font-semibold">{String(surface.props?.title || 'Explore SaaStoAgent')}</div>
        <p className="mt-2 text-sm leading-6 text-slate-500">
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
      <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm font-semibold">Dashboard</div>
            <p className="mt-2 text-sm text-slate-500">
              Corpus stays in the center. The dashboard remains contextual until you ask to open or create an agent.
            </p>
          </div>
          <div className="rounded-full border border-slate-200 px-2.5 py-1 text-[11px] font-medium text-slate-500 dark:border-white/10">
            {saasAgents.length} agents
          </div>
        </div>
        {saasAgents.length > 0 && (
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {saasAgents.slice(0, 4).map((agent) => (
              <div key={agent.id} className="rounded-md border border-slate-200 p-3 text-sm dark:border-white/10">
                <div className="font-medium">{agent.name}</div>
                <div className="mt-1 text-xs text-slate-500">{agent.slug}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-semibold">{String(surface.props?.title || contextLens?.working_on || projection.graph_node)}</div>
        <span className="rounded-full border border-slate-200 px-2.5 py-1 text-[11px] font-medium text-slate-500 dark:border-white/10">
          {projection.graph_node}
        </span>
      </div>
      <div className="mt-2 text-sm text-slate-500">
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
    <div className="mb-3 rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{proposal.label}</div>
          {proposal.description && <p className="mt-1 text-sm text-slate-500">{proposal.description}</p>}
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 transition hover:bg-slate-100 dark:border-white/10 dark:hover:bg-white/5"
        >
          Dismiss
        </button>
      </div>

      {fields.length > 0 && (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {fields.map((field) => (
            <label key={field.key} className="grid gap-1.5 text-sm">
              <span className="text-xs font-medium text-slate-500">{field.label}</span>
              {field.field_type === 'select' ? (
                <select
                  value={String(values[field.key] ?? field.default ?? '')}
                  onChange={(event) => setValues((current) => ({ ...current, [field.key]: event.target.value }))}
                  className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#09090b]"
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
                  className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#09090b]"
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
          className="inline-flex items-center rounded-full border border-sky-300 bg-sky-50 px-3.5 py-1.5 text-xs font-medium text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-300 dark:hover:bg-sky-500/20"
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
    () => Object.values(projection.surfaces).find((surface) => surface.role === 'active') || null,
    [projection.surfaces],
  )

  if (!activeSurface) return null

  return (
    <section className="px-4 py-6 sm:px-6">
      <div className="mx-auto max-w-5xl rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
        <div className="mb-4 flex items-center justify-between gap-3 border-b border-slate-200 pb-3 dark:border-white/10">
          <div>
            <h2 className="text-base font-semibold">{surfaceTitle(activeSurface, contextLens)}</h2>
            <p className="mt-1 text-sm text-slate-500">Opened from committed graph state.</p>
          </div>
          <span className="rounded-full border border-slate-200 px-2.5 py-1 text-[11px] font-medium text-slate-500 dark:border-white/10">
            {activeSurface.variant}
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
    return <AuthAgentDesk initialIntent={surface.variant === 'auth_register' ? 'register' : 'login'} />
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

function ContextPanel({ projection }: { projection: RouteDeckProjection }) {
  const lens = contextLensFromProjection(projection)
  return (
    <section>
      <h2 className="text-sm font-semibold">Working on</h2>
      <dl className="mt-3 grid gap-2 text-xs">
        <LensRow label="Agent" value={lens?.selected_saas_agent_name || 'No agent selected'} />
        <LensRow label="Current work" value={displayWork(lens?.working_on || projection.current_context)} />
        <LensRow label="API readiness" value={`${lens?.ready_connection_count || 0}/${lens?.connection_count || 0} ready`} />
        <LensRow label="Tools" value={String(lens?.tool_count || 0)} />
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
  const [open, setOpen] = useState(false)
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

  return (
    <section className="mt-6">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
      >
        <AlertTriangle className="h-3.5 w-3.5" />
        Diagnostics
      </button>
      {open && (
        <div className="fixed inset-y-16 right-4 z-40 w-[min(44rem,calc(100vw-2rem))] overflow-y-auto rounded-lg border border-slate-200 bg-white p-4 text-xs shadow-2xl dark:border-white/10 dark:bg-[#09090b]">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <div className="font-semibold text-slate-950 dark:text-white">RouteDeck diagnostics</div>
              <div className="mt-1 font-mono text-[11px] text-slate-500">
                {projection.current_context} / {projection.graph_node} / v{projection.projection_version}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-600 transition hover:bg-slate-100 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
            >
              Close
            </button>
          </div>

          {loadError && (
            <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
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
              />

              <details className="mt-4 rounded-lg border border-slate-200 bg-slate-950 p-3 text-[11px] text-slate-100 dark:border-white/10">
                <summary className="cursor-pointer font-semibold">Raw RouteDeck JSON</summary>
                <pre className="mt-3 max-h-96 overflow-auto">
                  {JSON.stringify(snapshot, null, 2)}
                </pre>
              </details>
            </>
          ) : (
            <div className="flex items-center gap-2 py-6 text-sm text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading diagnostics
            </div>
          )}
        </div>
      )}
    </section>
  )
}

function LensRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 p-2 dark:border-white/10">
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-1 break-words font-medium">{value}</dd>
    </div>
  )
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3 dark:border-white/10 dark:bg-white/[0.03]">
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  )
}

function Metric({ label, value, icon }: { label: string; value: number; icon: ReactNode }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
      <div className="flex items-center gap-2 text-sm text-slate-500">
        {icon}
        <span>{label}</span>
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
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
        <div className="rounded-md border border-slate-200 bg-white p-2 text-sky-600 dark:border-white/10 dark:bg-white/[0.03]">
          {icon}
        </div>
        <div className="min-w-0">
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{description}</p>
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
  return value
}
