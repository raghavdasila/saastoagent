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
  FileText,
  KeyRound,
  Loader2,
} from 'lucide-react'

import { useAuth } from '@/context/AuthContext'
import { isValidEmail } from '@/lib/entryGraph'
import { api } from '@/lib/api'
import { useSaaSAgentUiStore } from '@/stores/saasAgentUiStore'
import type { AppGraphContextLens } from '@/types/appGraph'
import type { SaaSAgent } from '@/types/domain'

import {
  corpusActionLabel,
  handleProposalFieldChange,
  operationToProposal,
  proposalDefaults,
  proposalFields,
} from './corpusOperations'
import { graphStateFromRouteDeckState } from './corpusRouteDeckClient'
import { corpusOperationIds, corpusSurfaceComponents } from './corpusRouteDeckCatalog'

export interface ActiveSurfaceDirtyState {
  surfaceId: string
  dirty: boolean
  save?: () => Promise<boolean>
}

export function OperationForm({
  operation,
  busy,
  initialArgs,
  submitLabel,
  onSubmit,
}: {
  operation: RouteDeckOperation
  busy: boolean
  initialArgs?: Record<string, unknown>
  submitLabel?: string
  onSubmit: (args: Record<string, unknown>) => void
}) {
  const proposal = operationToProposal(operation)
  const fields = proposalFields(proposal)
  const normalizedInitialArgs = useMemo(() => initialArgs || {}, [initialArgs])
  const resetKey = useMemo(
    () => JSON.stringify({ operationId: operation.id, initialArgs: normalizedInitialArgs }),
    [normalizedInitialArgs, operation.id],
  )
  const [values, setValues] = useState<Record<string, unknown>>(() => ({
    ...proposalDefaults(proposal),
    ...normalizedInitialArgs,
  }))

  useEffect(() => {
    setValues({
      ...proposalDefaults(proposal),
      ...normalizedInitialArgs,
    })
  }, [resetKey])

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

export function OperationReviewSurface({
  projection,
  surface,
  busy,
  onOperationSubmit,
}: {
  projection: RouteDeckProjection
  surface: RouteDeckSurface
  busy: boolean
  onOperationSubmit: (operationId: string, args: Record<string, unknown>) => void
}) {
  const routeDeckStore = useRouteDeckStore()
  const operationId = String(surface.props?.operation_id || '')
  const operation = projection.legal_operations.find((candidate) => candidate.id === operationId)
  const initialArgs = useMemo(
    () =>
      surface.props?.operation_args && typeof surface.props.operation_args === 'object'
        ? (surface.props.operation_args as Record<string, unknown>)
        : undefined,
    [surface.props?.operation_args],
  )

  if (!operation) {
    return (
      <InfoSurface
        title="Review next step"
        description="The requested step is no longer available from the committed graph state."
        icon={<AlertTriangle className="h-5 w-5" />}
      />
    )
  }

  return (
    <div className="grid gap-4" data-testid="corpus-operation-review-surface">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{operation.label}</div>
          {operation.description && <p className="mt-1 text-sm text-muted-foreground">{operation.description}</p>}
        </div>
        <button
          type="button"
          onClick={() => {
            void routeDeckStore.cancel()
          }}
          className="surface-outline-button px-3 py-1 text-xs"
        >
          Dismiss
        </button>
      </div>

      <OperationForm
        operation={operation}
        busy={busy}
        initialArgs={initialArgs}
        onSubmit={(args) => onOperationSubmit(operation.id, args)}
      />
    </div>
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

export function InstructionsSurface({
  saasAgentId,
  surfaceId,
  onDirtyStateChange,
}: {
  saasAgentId: string | null
  surfaceId: string
  onDirtyStateChange?: (state: ActiveSurfaceDirtyState | null) => void
}) {
  const routeDeckStore = useRouteDeckStore()
  const [systemPrompt, setSystemPrompt] = useState('')
  const [instructions, setInstructions] = useState('')
  const [lastSaved, setLastSaved] = useState({ systemPrompt: '', instructions: '' })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const dirty = systemPrompt !== lastSaved.systemPrompt || instructions !== lastSaved.instructions

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
        setLastSaved({ systemPrompt: agent.system_prompt || '', instructions: agent.instructions || '' })
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
    if (!saasAgentId) return false
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      await routeDeckStore.dispatch({
        operation_id: corpusOperationIds.instructionsSave,
        args: {
          system_prompt: systemPrompt,
          instructions,
        },
      })
      setLastSaved({ systemPrompt, instructions })
      setSaved(true)
      window.setTimeout(() => setSaved(false), 1800)
      return true
    } catch (saveError: unknown) {
      setError(saveError instanceof Error ? saveError.message : 'Failed to save instructions.')
      return false
    } finally {
      setSaving(false)
    }
  }

  useEffect(() => {
    if (!onDirtyStateChange || !saasAgentId) return undefined
    if (dirty) {
      onDirtyStateChange({ surfaceId, dirty: true, save })
    } else {
      onDirtyStateChange(null)
    }
    return () => onDirtyStateChange(null)
  }, [dirty, onDirtyStateChange, saasAgentId, save, surfaceId])

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
          disabled={loading || saving || !dirty}
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
  const currentSurfaceId = projection.navigation?.current?.surface_id
  if (currentSurfaceId) {
    const exact = Object.values(projection.surfaces).find((surface) => surface.surface_id === currentSurfaceId)
    if (exact) return exact
  }
  return Object.values(projection.surfaces).find((surface) => surface.role === 'active') || null
}
