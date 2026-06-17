import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, CheckCircle2, Loader2, PlugZap, SearchCheck, ShieldCheck } from 'lucide-react'

import { api, ApiError } from '@/lib/api'
import { formatSaaSAgentDisplayName } from '@/lib/entryGraph'
import { useSaaSAgentUiStore } from '@/stores/saasAgentUiStore'
import type { ConnectionPreview, ConnectionRead, SaaSAgent, SaaSAgentStats } from '@/types/domain'

interface ConnectSetupViewProps {
  saasAgent?: SaaSAgent
  stats?: SaaSAgentStats
  saasAgentId?: string | null
}

const authOptions = [
  { value: 'none', label: 'No auth' },
  { value: 'bearer', label: 'Bearer token' },
  { value: 'api_key_header', label: 'API key header' },
  { value: 'api_key_query', label: 'API key query param' },
  { value: 'basic', label: 'Basic auth' },
  { value: 'custom_header', label: 'Custom header' },
]

export function ConnectSetupView({ saasAgent, stats, saasAgentId: saasAgentIdProp }: ConnectSetupViewProps) {
  const saasAgentId = saasAgentIdProp || saasAgent?.id || null
  const agentApi = api.withSaaSAgent(saasAgentId)
  const setActiveView = useSaaSAgentUiStore((state) => state.setActiveView)
  const queryClient = useQueryClient()
  const [name, setName] = useState('Primary API')
  const [baseUrl, setBaseUrl] = useState('')
  const [specUrl, setSpecUrl] = useState('')
  const [rawSpec, setRawSpec] = useState('')
  const [authType, setAuthType] = useState('none')
  const [credential, setCredential] = useState('')
  const [headerName, setHeaderName] = useState('')
  const [queryParamName, setQueryParamName] = useState('')
  const [activationLog, setActivationLog] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const saasAgentName = formatSaaSAgentDisplayName(saasAgent?.name) || 'This saasAgent'
  const connectionCount = stats?.connections_count ?? 0
  const toolCount = stats?.tools_count ?? 0

  const { data: connections = [] } = useQuery({
    queryKey: ['connections', saasAgentId],
    queryFn: () => agentApi.get<ConnectionRead[]>(`/saas-agents/${saasAgentId}/connections`),
    enabled: !!saasAgentId,
  })

  const readyConnections = useMemo(
    () => connections.filter((connection) => connection.activation_status === 'ready'),
    [connections],
  )

  const preview = useMutation({
    mutationFn: () =>
      agentApi.post<ConnectionPreview>(`/saas-agents/${saasAgentId}/connections/preview`, {
        spec_url: specUrl,
        raw_spec: rawSpec,
      }),
    onSuccess: () => setError(null),
    onError: (e) => setError(e instanceof ApiError ? e.message : 'Preview failed'),
  })

  const createConnection = useMutation({
    mutationFn: () =>
      agentApi.post<ConnectionRead>(`/saas-agents/${saasAgentId}/connections`, {
        name,
        type: 'rest_api',
        provider: 'rest_api',
        auth_type: authType,
        config: { base_url: baseUrl, spec_url: specUrl, raw_spec: rawSpec, auth_type: authType },
        credentials: credential
          ? {
              credential_value: credential,
              header_name: headerName,
              query_param_name: queryParamName,
            }
          : undefined,
      }),
    onSuccess: async (connection) => {
      setError(null)
      setActivationLog(['Connection saved. Starting catalog activation...'])
      await activateConnection(connection.id)
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : 'Connection save failed'),
  })

  async function activateConnection(connectionId: string) {
    try {
      await agentApi.postStream(`/saas-agents/${saasAgentId}/connections/${connectionId}/activate`, (eventType, data) => {
        const label = typeof data.message === 'string' ? data.message : eventType
        const suffix =
          eventType === 'step' && data.step === 'router_index' && data.status === 'done'
            ? ` (${String(data.router_documents_count || 0)} references, ${String(data.router_endpoint_count || 0)} endpoints)`
            : ''
        setActivationLog((prev) => [...prev, `${eventType}: ${label}${suffix}`])
      })
      queryClient.invalidateQueries({ queryKey: ['connections', saasAgentId] })
      queryClient.invalidateQueries({ queryKey: ['saasAgent-stats', saasAgentId] })
      queryClient.invalidateQueries({ queryKey: ['saasAgent-catalog', saasAgentId] })
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Activation failed')
    }
  }

  const canSubmit = Boolean(saasAgentId && name.trim() && baseUrl.trim() && (specUrl.trim() || rawSpec.trim()))

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 px-4 py-6 dark:bg-background sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(24rem,0.85fr)]">
        <section className="surface-card rounded-lg p-6 sm:p-7">
          <div className="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">
            <span>Connections</span>
            <span className="rounded-full bg-slate-100 px-2 py-1 tracking-normal text-slate-600 dark:bg-white/[0.06] dark:text-slate-400">
              {connectionCount} APIs · {toolCount} tools
            </span>
          </div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Connect the REST surface Corpus can operate
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-400">
            {saasAgentName} becomes useful when its OpenAPI catalog is tested, activated, and exposed as actions. This view handles the operator setup path without sending the user into the graph debugger.
          </p>
          {error && (
            <div className="mt-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
              {error}
            </div>
          )}

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <label className="grid gap-1 text-sm">
              <span className="font-medium text-slate-700 dark:text-slate-200">Connection name</span>
              <input className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/[0.04]" value={name} onChange={(e) => setName(e.target.value)} data-qa-field="connection-name" />
            </label>
            <label className="grid gap-1 text-sm">
              <span className="font-medium text-slate-700 dark:text-slate-200">Auth type</span>
              <select className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/[0.04]" value={authType} onChange={(e) => setAuthType(e.target.value)} data-qa-field="auth-type">
                {authOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-sm md:col-span-2">
              <span className="font-medium text-slate-700 dark:text-slate-200">Base URL</span>
              <input className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/[0.04]" placeholder="https://api.example.com" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} data-qa-field="base-url" />
            </label>
            <label className="grid gap-1 text-sm md:col-span-2">
              <span className="font-medium text-slate-700 dark:text-slate-200">OpenAPI URL</span>
              <input className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/[0.04]" placeholder="https://api.example.com/openapi.json" value={specUrl} onChange={(e) => setSpecUrl(e.target.value)} data-qa-field="spec-url" />
            </label>
            <label className="grid gap-1 text-sm md:col-span-2">
              <span className="font-medium text-slate-700 dark:text-slate-200">Paste OpenAPI schema</span>
              <textarea className="min-h-36 rounded-md border border-slate-200 bg-white px-3 py-2 font-mono text-xs dark:border-white/10 dark:bg-white/[0.04]" placeholder="Paste OpenAPI JSON or YAML when the schema is not publicly hosted." value={rawSpec} onChange={(e) => setRawSpec(e.target.value)} data-qa-field="raw-spec" />
            </label>
            {authType !== 'none' && (
              <>
                <label className="grid gap-1 text-sm md:col-span-2">
                  <span className="font-medium text-slate-700 dark:text-slate-200">Credential</span>
                  <input className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/[0.04]" type="password" value={credential} onChange={(e) => setCredential(e.target.value)} data-qa-field="credential" />
                </label>
                {authType === 'api_key_header' || authType === 'custom_header' ? (
                  <label className="grid gap-1 text-sm">
                    <span className="font-medium text-slate-700 dark:text-slate-200">Header name</span>
                    <input className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/[0.04]" placeholder="X-API-Key" value={headerName} onChange={(e) => setHeaderName(e.target.value)} data-qa-field="header-name" />
                  </label>
                ) : null}
                {authType === 'api_key_query' ? (
                  <label className="grid gap-1 text-sm">
                    <span className="font-medium text-slate-700 dark:text-slate-200">Query param</span>
                    <input className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/[0.04]" placeholder="api_key" value={queryParamName} onChange={(e) => setQueryParamName(e.target.value)} data-qa-field="query-param-name" />
                  </label>
                ) : null}
              </>
            )}
          </div>

          <div className="mt-6 flex flex-wrap gap-2">
            <button
              className="surface-outline-button inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium"
              disabled={(!specUrl && !rawSpec) || preview.isPending}
              onClick={() => preview.mutate()}
              type="button"
              data-qa-action="preview-api"
            >
              {preview.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <SearchCheck className="h-4 w-4" />}
              Preview API
            </button>
            <button
              className="surface-solid-button inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium disabled:opacity-50"
              disabled={!canSubmit || createConnection.isPending}
              onClick={() => createConnection.mutate()}
              type="button"
              data-qa-action="save-and-activate"
            >
              {createConnection.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlugZap className="h-4 w-4" />}
              Save and activate
            </button>
            {toolCount > 0 && (
              <button className="surface-outline-button inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium" onClick={() => setActiveView('actions')} type="button" data-qa-action="inspect-actions">
                Inspect actions
                <ArrowRight className="h-4 w-4" />
              </button>
            )}
          </div>
        </section>

        <aside className="space-y-4">
          <section className="surface-card rounded-lg p-5">
            <h2 className="text-sm font-semibold text-slate-950 dark:text-white">Catalog preview</h2>
            {!preview.data ? (
              <p className="mt-2 text-sm leading-6 text-slate-500">Preview an OpenAPI URL to see methods, tags, and sample actions before activation.</p>
            ) : (
              <div className="mt-3 space-y-3 text-sm">
                <div>
                  <div className="font-semibold text-slate-900 dark:text-white">{preview.data.title}</div>
                  <div className="text-xs text-slate-500">{preview.data.endpoint_count} endpoints · version {preview.data.version || 'unknown'}</div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(preview.data.methods).map(([method, count]) => (
                    <span key={method} className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold dark:bg-white/[0.06]">{method} {count}</span>
                  ))}
                </div>
                <div className="max-h-64 overflow-y-auto rounded-md border border-slate-200 dark:border-white/10">
                  {preview.data.sample_actions.map((action, index) => (
                    <div key={index} className="border-b border-slate-100 p-3 last:border-0 dark:border-white/5">
                      <div className="text-xs font-semibold uppercase text-sky-600">{String(action.method)} {String(action.path)}</div>
                      <div className="mt-1 text-xs text-slate-500">{String(action.name || '')}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <section className="surface-card rounded-lg p-5">
            <h2 className="text-sm font-semibold text-slate-950 dark:text-white">Activation</h2>
            {activationLog.length === 0 ? (
              <p className="mt-2 text-sm leading-6 text-slate-500">Activation will parse OpenAPI, create actions, generate callable tools, and prepare request matching.</p>
            ) : (
              <ul className="mt-3 space-y-2 text-xs text-slate-600 dark:text-slate-300">
                {activationLog.map((line, index) => (
                  <li key={`${line}-${index}`} className="flex gap-2">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" />
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="surface-card rounded-lg p-5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <h2 className="text-sm font-semibold text-slate-950 dark:text-white">Ready connections</h2>
            </div>
            <div className="mt-3 space-y-2">
              {readyConnections.length === 0 ? (
                <p className="text-sm text-slate-500">No activated APIs yet.</p>
              ) : readyConnections.map((connection) => (
                <div key={connection.id} className="rounded-md bg-slate-50 p-3 text-sm dark:bg-white/[0.04]">
                  <div className="font-medium text-slate-900 dark:text-white">{connection.name}</div>
                  <div className="text-xs text-slate-500">{connection.action_nodes_count} actions · {connection.tools_count} tools</div>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}
