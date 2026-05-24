import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import {
  useRouteDeckStore,
  type RouteDeckOperation,
  type RouteDeckProjection,
  type RouteDeckSurface,
} from '@routedeck/react'
import {
  AlertTriangle,
  Boxes,
  FileText,
  KeyRound,
  Loader2,
  Play,
  ShieldCheck,
} from 'lucide-react'

import { AdminPanel } from '@/components/agent/AdminPanel'
import { AttachmentsPanel } from '@/components/agent/AttachmentsPanel'
import { LearningPanel } from '@/components/agent/LearningPanel'
import { ActionsCanvas } from '@/components/saasAgent/ActionsCanvas'
import { EntitiesCanvas } from '@/components/saasAgent/EntitiesCanvas'
import { QAAgentPanel } from '@/components/qa/QAAgentPanel'
import { useAuth } from '@/context/AuthContext'
import { isValidEmail } from '@/lib/entryGraph'
import { api } from '@/lib/api'
import { useSaaSAgentUiStore } from '@/stores/saasAgentUiStore'
import type { AppGraphContextLens, AppGraphState } from '@/types/appGraph'
import type { CorpusExpectedActiveSurface } from '@/types/corpus'
import type { SaaSAgent } from '@/types/domain'

import {
  corpusActionLabel,
  handleProposalFieldChange,
  operationToProposal,
  proposalDefaults,
  proposalFields,
} from './corpusOperations'
import { graphStateFromRouteDeckState, syncBrowserPathWithoutNavigation } from './corpusRouteDeckClient'
import { corpusOperationIds, corpusSurfaceComponents } from './corpusRouteDeckCatalog'
import { displayWork } from './workbenchDisplay'
export function OperationForm({
  operation,
  busy,
  submitLabel,
  onSubmit,
}: {
  operation: RouteDeckOperation
  busy: boolean
  submitLabel?: string
  onSubmit: (args: Record<string, unknown>) => void
}) {
  const proposal = operationToProposal(operation)
  const fields = proposalFields(proposal)
  const [values, setValues] = useState<Record<string, unknown>>(() => proposalDefaults(proposal))

  useEffect(() => {
    setValues(proposalDefaults(proposal))
  }, [operation.id])

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit(values)
  }

  return (
    <form className="grid gap-4" onSubmit={submit}>
      {fields.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {fields.map((field) => (
            <label key={field.key} className="grid gap-1.5 text-sm">
              <span className="text-xs font-medium text-muted-foreground">
                {field.label}
                {field.required ? ' *' : ''}
              </span>
              {field.field_type === 'select' ? (
                <select
                  value={String(values[field.key] ?? field.default ?? '')}
                  required={field.required}
                  onChange={(event) => setValues((current) => ({ ...current, [field.key]: event.target.value }))}
                  className="md3-field"
                  data-qa-field={field.key}
                >
                  {(field.options || []).map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : field.field_type === 'textarea' ? (
                <textarea
                  value={String(values[field.key] ?? field.default ?? '')}
                  required={field.required}
                  placeholder={field.placeholder || ''}
                  onChange={(event) => handleProposalFieldChange(field.key, event, setValues)}
                  className="md3-field min-h-40 font-mono text-xs"
                  data-qa-field={field.key}
                />
              ) : (
                <input
                  type={field.sensitive ? 'password' : field.field_type === 'url' ? 'url' : 'text'}
                  value={String(values[field.key] ?? field.default ?? '')}
                  required={field.required}
                  placeholder={field.placeholder || ''}
                  onChange={(event) => handleProposalFieldChange(field.key, event, setValues)}
                  className="md3-field"
                  data-qa-field={field.key}
                />
              )}
            </label>
          ))}
        </div>
      )}
      <div>
        <button
          type="submit"
          disabled={busy}
          className="surface-solid-button disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitLabel || corpusActionLabel(operation)}
        </button>
      </div>
    </form>
  )
}

export function ConnectionSetupSurface({
  projection,
  busy,
  onOperationSubmit,
}: {
  projection: RouteDeckProjection
  busy: boolean
  onOperationSubmit: (operationId: string, args: Record<string, unknown>) => void
}) {
  const previewOperation = projection.legal_operations.find((operation) => operation.id === 'connection.preview')
  const activateOperation = projection.legal_operations.find((operation) => operation.id === 'connection.activate')

  return (
    <InfoSurface
      title="Connect an API"
      description="Enter the SaaS API connection details here. Preview validates the OpenAPI schema; save and activate creates the connection, generated actions, tools, and catalog context."
      icon={<KeyRound className="h-5 w-5" />}
    >
      <div className="grid gap-4" data-testid="connection-setup-surface">
        {previewOperation && (
          <div className="rounded-[0.85rem] border border-border/35 bg-background/70 p-4">
            <div className="mb-3">
              <h4 className="text-sm font-semibold">Preview schema</h4>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                Use this first when you only want to verify the OpenAPI URL and endpoint count.
              </p>
            </div>
            <OperationForm
              operation={previewOperation}
              busy={busy}
              submitLabel="Preview schema"
              onSubmit={(args) => onOperationSubmit(previewOperation.id, args)}
            />
          </div>
        )}

        {activateOperation && (
          <div className="rounded-[0.85rem] border border-secondary/35 bg-secondary/5 p-4">
            <div className="mb-3">
              <h4 className="text-sm font-semibold">Save and activate API</h4>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                Provide the base URL, OpenAPI URL, and auth metadata. Credentials are stored separately from visitor auth.
              </p>
            </div>
            <OperationForm
              operation={activateOperation}
              busy={busy}
              submitLabel="Save and activate API"
              onSubmit={(args) => onOperationSubmit(activateOperation.id, args)}
            />
          </div>
        )}

        {!previewOperation && !activateOperation && (
          <p className="text-sm text-muted-foreground">
            Connection actions are not currently available from this graph node.
          </p>
        )}
      </div>
    </InfoSurface>
  )
}

export function ActiveSurfacePanel({
  projection,
  graphState,
  busy,
  onOperationSubmit,
}: {
  projection: RouteDeckProjection
  graphState: AppGraphState | null
  busy: boolean
  onOperationSubmit: (operationId: string, args: Record<string, unknown>) => void
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
        <SurfaceRenderer
          surface={activeSurface}
          contextLens={contextLens}
          graphState={graphState}
          projection={projection}
          busy={busy}
          onOperationSubmit={onOperationSubmit}
        />
      </div>
    </section>
  )
}

export function SurfaceRenderer({
  surface,
  contextLens,
  graphState,
  projection,
  busy,
  onOperationSubmit,
}: {
  surface: RouteDeckSurface
  contextLens: AppGraphContextLens | null
  graphState: AppGraphState | null
  projection: RouteDeckProjection
  busy: boolean
  onOperationSubmit: (operationId: string, args: Record<string, unknown>) => void
}) {
  if (surface.component === corpusSurfaceComponents.auth) {
    return <AuthSurfaceCard surface={surface} />
  }
  const activeSaaSAgentId = graphState?.active_saas_agent_id || null
  if (surface.component === corpusSurfaceComponents.entities) return <EntitiesCanvas saasAgentId={activeSaaSAgentId} />
  if (surface.component === corpusSurfaceComponents.actions) return <ActionsCanvas saasAgentId={activeSaaSAgentId} />
  if (surface.component === corpusSurfaceComponents.knowledge) return <AttachmentsPanel saasAgentId={activeSaaSAgentId} />
  if (surface.component === corpusSurfaceComponents.learning) return <LearningPanel saasAgentId={activeSaaSAgentId} />
  if (surface.component === corpusSurfaceComponents.qa) return <QAAgentPanel onResetRuntime={async () => undefined} />
  if (surface.component === corpusSurfaceComponents.instructions) {
    return <InstructionsSurface saasAgentId={activeSaaSAgentId} />
  }
  if (surface.component === corpusSurfaceComponents.memory) {
    const agents = Array.isArray(surface.props?.saas_agents) ? (surface.props?.saas_agents as SaaSAgent[]) : []
    const activeAgent = agents.find((agent) => agent.id === activeSaaSAgentId)
    return <AdminPanel saasAgent={activeAgent} saasAgentId={activeSaaSAgentId} />
  }
  if (surface.component === corpusSurfaceComponents.schemaPreview) {
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
  if (surface.component === corpusSurfaceComponents.catalog) {
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
  if (surface.component === corpusSurfaceComponents.connectionSetup) {
    return <ConnectionSetupSurface projection={projection} busy={busy} onOperationSubmit={onOperationSubmit} />
  }
  if (surface.component === corpusSurfaceComponents.saaSAgentList) {
    const agents = Array.isArray(surface.props?.saas_agents) ? (surface.props?.saas_agents as SaaSAgent[]) : []
    return <SaaSAgentListSurface agents={agents} />
  }
  if (surface.component === corpusSurfaceComponents.execution) {
    return (
      <InfoSurface title="Execution" description="Corpus will propose execution inputs or approvals when the graph requires them." icon={<Play className="h-5 w-5" />} />
    )
  }
  if (surface.component === corpusSurfaceComponents.recovery) {
    return (
      <InfoSurface title="Recovery" description="This path needs a different prerequisite. Diagnostics can explain why it is blocked." icon={<AlertTriangle className="h-5 w-5" />} />
    )
  }
  return (
    <InfoSurface title={surfaceTitle(surface, contextLens)} description="This surface is available from the current node." icon={<Boxes className="h-5 w-5" />} />
  )
}

export function InstructionsSurface({ saasAgentId }: { saasAgentId: string | null }) {
  const [systemPrompt, setSystemPrompt] = useState('')
  const [instructions, setInstructions] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!saasAgentId) return
    let cancelled = false
    setLoading(true)
    setError(null)
    api.get<SaaSAgent>(`/saas-agents/${saasAgentId}/instructions`)
      .then((agent) => {
        if (cancelled) return
        setSystemPrompt(agent.system_prompt || '')
        setInstructions(agent.instructions || '')
      })
      .catch((loadError: unknown) => {
        if (cancelled) return
        setError(loadError instanceof Error ? loadError.message : 'Failed to load instructions.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [saasAgentId])

  const save = async () => {
    if (!saasAgentId) return
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      const agent = await api.put<SaaSAgent>(`/saas-agents/${saasAgentId}/instructions`, {
        system_prompt: systemPrompt,
        instructions,
      })
      setSystemPrompt(agent.system_prompt || '')
      setInstructions(agent.instructions || '')
      setSaved(true)
      window.setTimeout(() => setSaved(false), 1800)
    } catch (saveError: unknown) {
      setError(saveError instanceof Error ? saveError.message : 'Failed to save instructions.')
    } finally {
      setSaving(false)
    }
  }

  if (!saasAgentId) {
    return <InfoSurface title="Instructions" description="Open a SaaS Agent before editing instructions." icon={<FileText className="h-5 w-5" />} />
  }

  return (
    <div className="grid gap-4" data-testid="instructions-surface">
      <div className="grid gap-3 lg:grid-cols-2">
        <label className="grid gap-1.5 text-sm">
          <span className="text-xs font-medium text-muted-foreground">System prompt</span>
          <textarea
            value={systemPrompt}
            disabled={loading || saving}
            onChange={(event) => setSystemPrompt(event.target.value)}
            className="md3-field min-h-64 resize-y font-mono text-xs"
            placeholder="High-level identity, role, and boundaries for this SaaS Agent"
            data-testid="saas-agent-system-prompt"
          />
        </label>
        <label className="grid gap-1.5 text-sm">
          <span className="text-xs font-medium text-muted-foreground">Operating instructions</span>
          <textarea
            value={instructions}
            disabled={loading || saving}
            onChange={(event) => setInstructions(event.target.value)}
            className="md3-field min-h-64 resize-y font-mono text-xs"
            placeholder="Workflow guidance, tone, policies, and store-specific behavior"
            data-testid="saas-agent-instructions"
          />
        </label>
      </div>

      {error && (
        <div className="rounded-[0.625rem] bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          {error}
        </div>
      )}
      {saved && (
        <div className="rounded-[0.625rem] bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300">
          Saved.
        </div>
      )}

      <div>
        <button
          type="button"
          onClick={() => void save()}
          disabled={loading || saving}
          className="surface-solid-button inline-flex items-center gap-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving && <Loader2 className="h-4 w-4 animate-spin" />}
          Save instructions
        </button>
      </div>
    </div>
  )
}

export function SaaSAgentListSurface({ agents }: { agents: SaaSAgent[] }) {
  const routeDeckStore = useRouteDeckStore()
  const setMirroredSaaSAgentId = useSaaSAgentUiStore((state) => state.setMirroredSaaSAgentId)
  const [search, setSearch] = useState('')
  const [openingAgentId, setOpeningAgentId] = useState<string | null>(null)
  const filteredAgents = agents.filter((agent) => {
    const query = search.trim().toLowerCase()
    if (!query) return true
    return `${agent.name} ${agent.slug}`.toLowerCase().includes(query)
  })

  const openAgent = async (agent: SaaSAgent) => {
    setOpeningAgentId(agent.id)
    try {
      const response = await routeDeckStore.dispatch({
        operation_id: corpusOperationIds.openSaaSAgent,
        args: { saas_agent_id: agent.id },
      })
      const nextGraphState = graphStateFromRouteDeckState(response.state)
      setMirroredSaaSAgentId(nextGraphState?.active_saas_agent_id || agent.id)
      const nextPath = response.state.location || null
      if (nextPath && nextPath !== window.location.pathname) {
        syncBrowserPathWithoutNavigation(nextPath)
      }
    } finally {
      setOpeningAgentId(null)
    }
  }

  return (
    <div className="grid gap-4" data-testid="saas-agent-list-surface">
      <div>
        <h3 className="text-xl font-medium">List agents</h3>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Search existing SaaS Agents, then open one with its RouteDeck-bound agent id.
        </p>
      </div>
      <label className="grid gap-1.5 text-sm">
        <span className="text-xs font-medium text-muted-foreground">Search</span>
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by name or slug"
          className="md3-field"
        />
      </label>
      <div className="rounded-[0.9rem] border border-border/30 bg-card shadow-sm dark:border-white/10 dark:bg-muted/40">
        {filteredAgents.length === 0 ? (
          <div className="p-4 text-sm text-muted-foreground">No matching SaaS Agents.</div>
        ) : (
          <div className="divide-y divide-border/30 dark:divide-white/10">
            {filteredAgents.map((agent) => (
              <div key={agent.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
                <div className="min-w-0">
                  <div className="font-semibold">{agent.name}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{agent.slug}</div>
                </div>
                <button
                  type="button"
                  onClick={() => void openAgent(agent)}
                  disabled={openingAgentId === agent.id}
                  className="rounded-full bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-sm transition hover:bg-primary/90 disabled:opacity-60"
                >
                  {openingAgentId === agent.id ? 'Opening' : 'Open'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export function AuthSurfaceCard({ surface }: { surface: RouteDeckSurface }) {
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
        operation_id: corpusOperationIds.navigateHome,
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
            void routeDeckStore.dispatch({ operation_id: corpusOperationIds.navigateHome, args: {} })
          }}
          className="surface-outline-button disabled:cursor-not-allowed disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}


export function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/25 bg-card p-3 shadow-sm dark:border-white/10 dark:bg-muted">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  )
}

export function Metric({ label, value, icon }: { label: string; value: number; icon: ReactNode }) {
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

export function InfoSurface({
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

export function surfaceTitle(surface: RouteDeckSurface, contextLens: AppGraphContextLens | null) {
  if (surface.component === corpusSurfaceComponents.auth) {
    return surface.variant === 'auth_register' ? 'Create account' : 'Sign in'
  }
  return String(surface.props?.title || contextLens?.working_on || surface.variant || surface.component)
}

export function contextLensFromProjection(projection: RouteDeckProjection): AppGraphContextLens | null {
  const sideSurface = projection.surfaces.side
  if (!sideSurface?.props || typeof sideSurface.props !== 'object') return null
  return sideSurface.props as unknown as AppGraphContextLens
}

export function activeSurfaceFromProjection(projection: RouteDeckProjection): RouteDeckSurface | null {
  return Object.values(projection.surfaces).find((surface) => surface.role === 'active') || null
}


export function surfaceMatchesExpected(
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

