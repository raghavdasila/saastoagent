import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
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
import { EntryActionCards, type EntryActionCard } from '@/components/entry/EntryActionCards'
import { ActionsCanvas } from '@/components/saasAgent/ActionsCanvas'
import { EntitiesCanvas } from '@/components/saasAgent/EntitiesCanvas'
import { QAAgentPanel } from '@/components/qa/QAAgentPanel'
import { ThemeToggleButton } from '@/components/theme/ThemeToggleButton'
import { api } from '@/lib/api'
import { useSaaSAgentStore } from '@/stores/saasAgentStore'
import type { ChatUIMessage } from '@/types/agent'
import type { AppGraphResponse } from '@/types/appGraph'

interface AppGraphShellProps {
  nodeId?: string
  saasAgentId?: string
}

export function AppGraphShell({ nodeId, saasAgentId }: AppGraphShellProps) {
  const navigate = useNavigate()
  const setSaaSAgentId = useSaaSAgentStore((state) => state.setSaaSAgentId)
  const [snapshot, setSnapshot] = useState<AppGraphResponse | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatUIMessage[]>(() => [
    makeAgentMessage(
      'assistant',
      'Hi. I can help you create or open a SaaS Agent, connect its API, inspect the catalog, and run approved actions.',
    ),
  ])
  const [draft, setDraft] = useState('')
  const [activeFormAction, setActiveFormAction] = useState<EntryActionCard | null>(null)

  const snapshotPath = useMemo(() => {
    const params = new URLSearchParams()
    if (nodeId) params.set('node_id', nodeId)
    if (saasAgentId) params.set('saas_agent_id', saasAgentId)
    const query = params.toString()
    return `/app/graph/snapshot${query ? `?${query}` : ''}`
  }, [nodeId, saasAgentId])

  const query = useQuery({
    queryKey: ['app-graph-snapshot', nodeId || 'home', saasAgentId || 'none'],
    queryFn: () => api.get<AppGraphResponse>(snapshotPath),
  })

  useEffect(() => {
    if (!query.data) return
    setSnapshot(query.data)
    setSaaSAgentId(query.data.state.active_saas_agent_id || null)
    if (query.data.replace_path && query.data.replace_path !== window.location.pathname) {
      navigate(query.data.replace_path, { replace: true })
    }
  }, [navigate, query.data, setSaaSAgentId])

  const applyGraphResponse = (next: AppGraphResponse) => {
    setSnapshot(next)
    setActiveFormAction(null)
    setSaaSAgentId(next.state.active_saas_agent_id || null)
    if (next.messages.length > 0) {
      setChatMessages((current) => [
        ...current,
        ...next.messages.map((message) => makeAgentMessage('assistant', message.content)),
      ])
    }
    if (next.replace_path && next.replace_path !== window.location.pathname) {
      navigate(next.replace_path, { replace: true })
    }
  }

  const action = useMutation({
    mutationFn: ({ card, payload }: { card: EntryActionCard; payload?: Record<string, unknown> }) =>
      api.post<AppGraphResponse>('/app/graph/action', {
        state: snapshot?.state,
        selected_action_id: card.id,
        action_payload: { ...(card.payload || {}), ...(payload || {}) },
      }),
    onSuccess: applyGraphResponse,
  })

  const turn = useMutation({
    mutationFn: (userInput: string) =>
      api.post<AppGraphResponse>('/app/graph/turn', {
        state: snapshot?.state,
        user_input: userInput,
      }),
    onSuccess: applyGraphResponse,
  })

  const data = snapshot || query.data
  if (query.isLoading && !data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-slate-500">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        Loading SaaS Agent desk
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-6">
        <div className="max-w-md rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
          The SaaS Agent desk could not load.
        </div>
      </div>
    )
  }

  const visibleActions = dedupeActions([...data.available_actions, ...data.persistent_actions])

  const handleActionIntent = (card: EntryActionCard, payload?: Record<string, unknown>) => {
    if (card.kind === 'form' && !payload) {
      setActiveFormAction(card)
      setChatMessages((current) => [
        ...current,
        makeAgentMessage('assistant', `Sure. I need a few details for ${card.label}.`),
      ])
      return
    }
    action.mutate({ card, payload })
  }

  const sendChatTurn = () => {
    const value = draft.trim()
    if (!value || action.isPending || turn.isPending) return
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
              <div className="truncate text-xs text-slate-500">{displayWork(data.context_lens.working_on)}</div>
            </div>
          </div>
          <ThemeToggleButton />
        </div>
      </header>

      <div className="grid min-h-[calc(100vh-3.5rem)] lg:grid-cols-[minmax(0,1fr)_22rem]">
        <main className="min-w-0">
          <AgentConversation
            messages={chatMessages}
            actions={visibleActions}
            draft={draft}
            busy={action.isPending || turn.isPending}
            actionBusy={action.isPending}
            error={turn.error || action.error}
            activeFormAction={activeFormAction}
            onDraftChange={setDraft}
            onSend={sendChatTurn}
            onAction={handleActionIntent}
            onFormSubmit={(card, payload) => action.mutate({ card, payload })}
            onCancelForm={() => setActiveFormAction(null)}
          />
          <WorkSurface snapshot={data} onAction={handleActionIntent} />
        </main>

        <aside className="border-t border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-[#09090b] lg:border-l lg:border-t-0">
          <ContextPanel snapshot={data} />
          <DiagnosticsPanel snapshot={data} />
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

function AgentConversation({
  messages,
  actions,
  draft,
  busy,
  actionBusy,
  error,
  activeFormAction,
  onDraftChange,
  onSend,
  onAction,
  onFormSubmit,
  onCancelForm,
}: {
  messages: ChatUIMessage[]
  actions: EntryActionCard[]
  draft: string
  busy: boolean
  actionBusy: boolean
  error: unknown
  activeFormAction: EntryActionCard | null
  onDraftChange: (value: string) => void
  onSend: () => void
  onAction: (action: EntryActionCard, payload?: Record<string, unknown>) => void
  onFormSubmit: (action: EntryActionCard, payload?: Record<string, unknown>) => void
  onCancelForm: () => void
}) {
  return (
    <section className="border-b border-slate-200 bg-slate-50 dark:border-white/10 dark:bg-[#08080a]" data-testid="app-agent-chat">
      <div className="mx-auto flex min-h-[32rem] max-w-5xl flex-col px-4 py-4 sm:px-6">
        <div className="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 dark:border-white/10">
          <div>
            <h1 className="text-lg font-semibold">Agent desk</h1>
            <p className="mt-1 text-sm text-slate-500">Tell the agent what to set up, inspect, or run.</p>
          </div>
          <Activity className="h-5 w-5 text-slate-400" />
        </div>

        <div className="flex-1 overflow-y-auto py-3">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {busy && (
            <MessageBubble
              message={{
                id: 'agent-desk-busy',
                role: 'assistant',
                content: '',
                timestamp: Date.now(),
                isStreaming: true,
                thinking: 'Working',
              }}
            />
          )}
        </div>

        {actions.length > 0 && (
          <div className="border-t border-slate-200 py-3 dark:border-white/10">
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">Suggestions</div>
            <ActionSuggestionDock actions={actions} busy={actionBusy} onSelect={onAction} />
            {activeFormAction && (
              <div className="mt-3 rounded-lg border border-slate-200 bg-white p-3 dark:border-white/10 dark:bg-white/[0.03]">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold">{activeFormAction.label}</div>
                  <button
                    type="button"
                    onClick={onCancelForm}
                    className="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 transition hover:bg-slate-100 dark:border-white/10 dark:hover:bg-white/5"
                  >
                    Cancel
                  </button>
                </div>
                <EntryActionCards actions={[activeFormAction]} busy={actionBusy} onSelect={onFormSubmit} />
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
            {error instanceof Error ? error.message : 'The agent could not complete that step.'}
          </div>
        )}

        <CommandComposer
          value={draft}
          onChange={onDraftChange}
          onSend={onSend}
          placeholder="Message the SaaS Agent"
          disabled={busy}
        />
      </div>
    </section>
  )
}

function ActionSuggestionDock({
  actions,
  busy,
  onSelect,
}: {
  actions: EntryActionCard[]
  busy: boolean
  onSelect: (action: EntryActionCard) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {actions.map((action) => {
        const isPrimary = action.emphasis === 'primary'
        return (
          <button
            key={action.id}
            type="button"
            disabled={busy || !!action.disabled_reason}
            title={action.description ?? undefined}
            onClick={() => onSelect(action)}
            className={[
              'inline-flex items-center rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50',
              isPrimary
                ? 'border-sky-300 bg-sky-50 text-sky-700 hover:bg-sky-100 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-300 dark:hover:bg-sky-500/20'
                : 'border-border bg-background text-muted-foreground hover:bg-accent hover:text-accent-foreground',
            ].join(' ')}
          >
            {action.label}
          </button>
        )
      })}
    </div>
  )
}

function WorkSurface({
  snapshot,
  onAction,
}: {
  snapshot: AppGraphResponse
  onAction: (action: EntryActionCard, payload?: Record<string, unknown>) => void
}) {
  const renderer = snapshot.active_surface.renderer
  if (renderer === 'auth_sign_in') return <AuthAgentDesk initialIntent="login" />
  if (renderer === 'auth_register') return <AuthAgentDesk initialIntent="register" />
  if (renderer === 'home') return snapshot.saas_agents.length > 0 ? <HomeSurface snapshot={snapshot} onAction={onAction} /> : null
  if (renderer === 'agent_home') return <AgentHomeSurface snapshot={snapshot} />
  if (renderer === 'connection_configure') return <ConnectionSurface snapshot={snapshot} />
  if (renderer === 'schema_preview') return <SchemaPreviewSurface snapshot={snapshot} />
  if (renderer === 'catalog_activation' || renderer === 'catalog') return <CatalogSurface snapshot={snapshot} />
  if (renderer === 'entities') return <EntitiesCanvas />
  if (renderer === 'actions') return <ActionsCanvas />
  if (renderer === 'knowledge') return <AttachmentsPanel />
  if (renderer === 'memory') return <AdminPanel saasAgent={snapshot.saas_agents.find((agent) => agent.id === snapshot.state.active_saas_agent_id)} />
  if (renderer === 'learning') return <LearningPanel />
  if (renderer === 'qa') return <QAAgentPanel onResetRuntime={async () => undefined} />
  return <RecoverySurface />
}

function HomeSurface({
  snapshot,
  onAction,
}: {
  snapshot: AppGraphResponse
  onAction: (action: EntryActionCard, payload?: Record<string, unknown>) => void
}) {
  const openAction = [...snapshot.available_actions, ...snapshot.persistent_actions].find((action) => action.id === 'saas_agent.open')
  return (
    <div className="px-4 py-6 sm:px-6">
      <div className="mx-auto max-w-5xl">
        <h2 className="text-xl font-semibold">Your SaaS Agents</h2>
        <p className="mt-2 text-sm text-slate-500">Open an existing agent or create a new one from the next steps above.</p>
        <div className="mt-5 grid gap-3">
          {snapshot.saas_agents.map((agent) => (
            <button
              key={agent.id}
              type="button"
              onClick={() => openAction && onAction(openAction, { saas_agent_id: agent.id })}
              className="rounded-lg border border-slate-200 bg-white p-4 text-left transition hover:border-sky-300 hover:bg-sky-50 dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-sky-500/40 dark:hover:bg-sky-500/10"
            >
              <div className="font-semibold">{agent.name}</div>
              <div className="mt-1 text-xs text-slate-500">{agent.slug} / {agent.role}</div>
            </button>
          ))}
          {snapshot.saas_agents.length === 0 && (
            <div className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-white/10">
              No SaaS Agents are visible for this session.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function AgentHomeSurface({ snapshot }: { snapshot: AppGraphResponse }) {
  return (
    <div className="px-4 py-6 sm:px-6">
      <div className="mx-auto grid max-w-6xl gap-3 md:grid-cols-4">
        <Metric label="Connections" value={snapshot.context_lens.connection_count} icon={<KeyRound className="h-4 w-4" />} />
        <Metric label="Ready APIs" value={snapshot.context_lens.ready_connection_count} icon={<Boxes className="h-4 w-4" />} />
        <Metric label="Actions" value={snapshot.context_lens.action_count} icon={<Play className="h-4 w-4" />} />
        <Metric label="Tools" value={snapshot.context_lens.tool_count} icon={<ShieldCheck className="h-4 w-4" />} />
      </div>
      <div className="mx-auto mt-5 max-w-6xl">
        <h2 className="text-xl font-semibold">{snapshot.context_lens.selected_saas_agent_name || 'SaaS Agent'}</h2>
        <p className="mt-2 text-sm text-slate-500">
          This agent is ready for API setup, catalog inspection, execution, knowledge, memory, learning, and QA.
        </p>
      </div>
    </div>
  )
}

function ConnectionSurface({ snapshot }: { snapshot: AppGraphResponse }) {
  const activate = snapshot.available_actions.find((action) => action.id === 'connection.activate')
  const targetField = activate?.fields.find((field) => field.key === 'api_target')
  return (
    <InfoSurface
      title="Connect an API"
      description="Choose the API this SaaS Agent should learn from. Medusa Storefront is prefilled for local setup, Medusa Admin and Custom API are available as options."
      icon={<KeyRound className="h-5 w-5" />}
    >
      <div className="grid gap-2 sm:grid-cols-3">
        {(targetField?.options || []).map((option) => (
          <div key={option.value} className="rounded-md border border-slate-200 bg-white p-3 text-sm dark:border-white/10 dark:bg-white/[0.03]">
            {option.label}
          </div>
        ))}
      </div>
    </InfoSurface>
  )
}

function SchemaPreviewSurface({ snapshot }: { snapshot: AppGraphResponse }) {
  const preview = snapshot.active_surface.payload.schema_preview as Record<string, unknown> | undefined
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

function CatalogSurface({ snapshot }: { snapshot: AppGraphResponse }) {
  const events = Array.isArray(snapshot.active_surface.payload.activation_events)
    ? snapshot.active_surface.payload.activation_events
    : []
  return (
    <InfoSurface title="Catalog" description="Activated API capabilities and generated tools appear here as they become available." icon={<Boxes className="h-5 w-5" />}>
      <div className="grid gap-3 sm:grid-cols-3">
        <Metric label="Ready APIs" value={snapshot.context_lens.ready_connection_count} icon={<KeyRound className="h-4 w-4" />} />
        <Metric label="Actions" value={snapshot.context_lens.action_count} icon={<Play className="h-4 w-4" />} />
        <Metric label="Tools" value={snapshot.context_lens.tool_count} icon={<ShieldCheck className="h-4 w-4" />} />
      </div>
      {events.length > 0 && (
        <p className="mt-3 text-sm text-slate-500">{events.length} activation events captured for diagnostics.</p>
      )}
    </InfoSurface>
  )
}

function RecoverySurface() {
  return (
    <InfoSurface title="Recovery" description="That step is not available from the current state. Return home or choose one of the visible next steps." icon={<AlertTriangle className="h-5 w-5" />} />
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
    <div className="px-4 py-6 sm:px-6">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-start gap-3">
          <div className="rounded-md border border-slate-200 bg-white p-2 text-sky-600 dark:border-white/10 dark:bg-white/[0.03]">
            {icon}
          </div>
          <div className="min-w-0">
            <h2 className="text-xl font-semibold">{title}</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">{description}</p>
          </div>
        </div>
        {children && <div className="mt-5">{children}</div>}
      </div>
    </div>
  )
}

function ContextPanel({ snapshot }: { snapshot: AppGraphResponse }) {
  const lens = snapshot.context_lens
  return (
    <section>
      <h2 className="text-sm font-semibold">Working on</h2>
      <dl className="mt-3 grid gap-2 text-xs">
        <LensRow label="Agent" value={lens.selected_saas_agent_name || 'No agent selected'} />
        <LensRow label="Current work" value={displayWork(lens.working_on)} />
        <LensRow label="API readiness" value={`${lens.ready_connection_count}/${lens.connection_count} ready`} />
        <LensRow label="Tools" value={String(lens.tool_count)} />
        {lens.pending_trace_id && <LensRow label="Pending approval" value={lens.pending_trace_status || 'Waiting'} />}
      </dl>
    </section>
  )
}

function DiagnosticsPanel({ snapshot }: { snapshot: AppGraphResponse }) {
  const [open, setOpen] = useState(false)
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
        <div className="mt-3 rounded-lg border border-slate-200 bg-slate-950 p-3 text-[11px] text-slate-100 dark:border-white/10">
          <div className="mb-2 font-semibold">RouteDeck diagnostics</div>
          <pre className="max-h-96 overflow-auto">
            {JSON.stringify(
              {
                graph_version: snapshot.graph_version,
                current_node: snapshot.state.node,
                reachable_nodes: snapshot.route_deck_snapshot.reachable_nodes,
                valid_actions: snapshot.route_deck_snapshot.valid_actions,
                evidence: snapshot.evidence,
                diagnostics: snapshot.diagnostics,
              },
              null,
              2,
            )}
          </pre>
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
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
      <div className="flex items-center justify-between gap-2">
        <div className="text-2xl font-semibold">{value}</div>
        <div className="text-slate-400">{icon}</div>
      </div>
      <div className="mt-1 text-xs text-slate-500">{label}</div>
    </div>
  )
}

function dedupeActions(actions: EntryActionCard[]) {
  const seen = new Set<string>()
  return actions.filter((action) => {
    if (seen.has(action.id)) return false
    seen.add(action.id)
    return true
  })
}

function displayWork(value: string) {
  if (value === 'Home') return 'Starting a SaaS Agent'
  if (value === 'SaaS Agent Home') return 'SaaS Agent overview'
  if (value === 'Connection Configure') return 'Connecting an API'
  if (value === 'Schema Preview') return 'Reviewing API schema'
  if (value === 'Catalog Activation') return 'Activating API catalog'
  if (value === 'Execution Planning') return 'Planning an API action'
  if (value === 'Needs Input') return 'Collecting missing inputs'
  if (value === 'Approval Required') return 'Waiting for approval'
  if (value === 'Result Review') return 'Reviewing result'
  return value
}
