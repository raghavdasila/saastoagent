import { ChevronDown, ChevronUp, CircleHelp, FileSearch, Gauge, Lock, ShieldCheck, SlidersHorizontal } from 'lucide-react'
import { useMemo, useState } from 'react'

import { EntryArtifactRenderer } from '@/components/entry/EntryArtifactRenderer'
import { cn } from '@/lib/cn'
import { formatWorkspaceDisplayName, OPERATOR_NAME, PRODUCT_MONOGRAM } from '@/lib/entryGraph'
import {
  capabilityStateFor,
  isCapabilitySelectable,
  stateLabel,
  stateTone,
  type CapabilityRuntimeContext,
  type OperatorCapabilityDefinition,
} from '@/lib/operatorExperience'
import type { EntryActionCard, EntryGraphManifest, EntryUIArtifact, GatewayNode, OperatorExperienceMode, OperatorSidebarItem } from '@/types/entry'
import type { Workspace, WorkspaceStats } from '@/types/domain'

export type AutonomyLevel = 'suggest' | 'draft' | 'ask' | 'low_risk_auto' | 'risky_approval'

export interface OperatorReadiness {
  label: string
  detail: string
  tone: 'neutral' | 'ready' | 'setup' | 'blocked'
}

const graphNodeLabels: Record<GatewayNode, string> = {
  bootstrap: 'Bootstrap',
  intent: 'Intent',
  display_name: 'Display name',
  email: 'Email',
  password: 'Password',
  workspace_select: 'Workspace select',
  workspace_job: 'Workspace draft',
  workspace_confirm: 'Workspace confirm',
  setup_intro: 'REST setup',
  connection_confirm: 'Connection confirm',
  operator_ready: 'Workspace ready',
}

const autonomyOptions: Array<{ id: AutonomyLevel; label: string; description: string }> = [
  { id: 'suggest', label: 'Suggest only', description: 'The agent only recommends tools and next steps.' },
  { id: 'draft', label: 'Draft plan', description: 'The agent prepares a plan and waits for direction.' },
  { id: 'ask', label: 'Ask before executing', description: 'Every REST action needs explicit approval.' },
  { id: 'low_risk_auto', label: 'Auto-execute low-risk', description: 'Future mode for safe read-only or low-risk actions.' },
  { id: 'risky_approval', label: 'Require approval for risky', description: 'Future mode with explicit gates around writes and side effects.' },
]

export function buildReadiness({
  mode,
  workspaceId,
  stats,
  isAuthenticated,
  operatorError,
}: {
  mode: OperatorExperienceMode
  workspaceId: string | null
  stats?: WorkspaceStats
  isAuthenticated: boolean
  operatorError?: string | null
}): OperatorReadiness {
  if (operatorError) {
    return { label: 'Needs attention', detail: operatorError, tone: 'blocked' }
  }
  if (mode === 'entry') {
    return {
      label: isAuthenticated ? 'Account ready' : 'Anonymous entry',
      detail: 'Describe the job, ask about the platform, or prepare REST setup.',
      tone: 'neutral',
    }
  }
  if (!workspaceId) {
    return { label: 'No workspace', detail: `Create or select a workspace before ${OPERATOR_NAME} can continue.`, tone: 'blocked' }
  }
  const connections = stats?.connections_count ?? 0
  const tools = stats?.tools_count ?? 0
  if (connections === 0) {
    return { label: 'Setup needed', detail: 'Connect a REST API before this workspace can inspect or execute actions.', tone: 'setup' }
  }
  if (tools === 0) {
    return { label: 'Catalog pending', detail: `${connections} API connected. Generated tools are not ready for chat execution yet.`, tone: 'setup' }
  }
  return { label: 'Ready for tool work', detail: `${connections} API connected, ${tools} generated tools available.`, tone: 'ready' }
}

export function OperatorStatusStrip({
  mode,
  workspace,
  workspaceId,
  stats,
  graphNode,
  graphManifest,
  readiness,
  busy,
}: {
  mode: OperatorExperienceMode
  workspace?: Workspace
  workspaceId: string | null
  stats?: WorkspaceStats
  graphNode?: GatewayNode | null
  graphManifest?: EntryGraphManifest | null
  readiness: OperatorReadiness
  busy: boolean
}) {
  const nodeCount = graphManifest?.nodes.length ?? 0
  const readinessClass = readiness.tone === 'ready'
    ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200'
    : readiness.tone === 'setup'
      ? 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200'
      : readiness.tone === 'blocked'
        ? 'border-red-200 bg-red-50 text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200'
        : 'border-slate-200 bg-white text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200'

  return (
    <section className="rounded-2xl border border-slate-200 bg-white/80 p-3 shadow-sm backdrop-blur dark:border-white/10 dark:bg-[#09090b]/80">
      <div className="grid gap-3 lg:grid-cols-[1.2fr_1fr_1fr]">
        <div className={cn('rounded-xl border px-3 py-2', readinessClass)}>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em]">
            <Gauge className="h-3.5 w-3.5" />
            {OPERATOR_NAME} readiness
          </div>
          <div className="mt-1 text-sm font-semibold">{readiness.label}</div>
          <p className="mt-1 text-xs leading-5 opacity-80">{readiness.detail}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-white/10 dark:bg-white/[0.03]">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Current surface</div>
          <div className="mt-1 text-sm font-semibold text-slate-950 dark:text-white">
            {mode === 'operator' ? formatWorkspaceDisplayName(workspace?.name) || 'Workspace ready' : 'Entry and setup'}
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {workspaceId ? `Workspace ${workspaceId.slice(0, 8)}` : 'No workspace selected'}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-white/10 dark:bg-white/[0.03]">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Flow state</div>
          <div className="mt-1 flex items-center gap-2 text-sm font-semibold text-slate-950 dark:text-white">
            {busy && <span className="h-2 w-2 animate-pulse rounded-full bg-sky-500" />}
            {graphNode ? graphNodeLabels[graphNode] : mode === 'operator' ? 'Workspace chat' : 'Bootstrapping'}
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {nodeCount > 0 ? `${nodeCount} graph nodes visible to the shell` : 'Workspace chat bridge active'}
          </p>
        </div>
      </div>
    </section>
  )
}

export function CapabilityRail({
  capabilities,
  activeItem,
  runtime,
  onSelect,
}: {
  capabilities: OperatorCapabilityDefinition[]
  activeItem: OperatorSidebarItem
  runtime: CapabilityRuntimeContext
  onSelect: (item: OperatorSidebarItem) => void
}) {
  return (
    <aside className="border-b border-slate-200 bg-white md:min-h-[calc(100vh-3.5rem)] md:w-24 md:shrink-0 md:border-b-0 md:border-r dark:border-white/10 dark:bg-[#09090b]">
      <div className="hidden border-b border-slate-200 px-3 py-4 md:flex md:justify-center dark:border-white/10">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-sky-200 bg-sky-50 text-xs font-bold tracking-[0.16em] text-sky-700 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200">
          {PRODUCT_MONOGRAM}
        </div>
      </div>
      <nav className="flex gap-2 overflow-x-auto px-2 py-2 md:flex-col md:items-center md:gap-3 md:px-0 md:py-4" aria-label="Workbench capability rail">
        {capabilities.map((item) => {
          const Icon = item.icon
          const selected = item.id === activeItem
          const state = capabilityStateFor(item, runtime)
          const enabled = isCapabilitySelectable(item, runtime)
          return (
            <button
              key={item.id}
              type="button"
              disabled={!enabled}
              onClick={() => onSelect(item.id)}
              title={`${item.label}: ${stateLabel(state)}. ${enabled ? item.description : item.emptyState}`}
              className={cn(
                'group relative flex min-w-16 shrink-0 flex-col items-center gap-1 rounded-2xl border px-2 py-2 text-[10px] font-medium transition md:h-16 md:w-16 md:min-w-0',
                selected
                  ? 'border-slate-900 bg-slate-950 text-white shadow-sm dark:border-white dark:bg-white dark:text-slate-950'
                  : 'border-transparent text-slate-600 hover:border-slate-200 hover:bg-slate-50 dark:text-slate-400 dark:hover:border-white/10 dark:hover:bg-white/[0.06]',
                enabled ? 'cursor-pointer' : 'cursor-not-allowed opacity-55',
              )}
            >
              <span className={cn('absolute right-1.5 top-1.5 h-2.5 w-2.5 rounded-full ring-2 ring-white dark:ring-[#09090b]', stateTone(state))} />
              <Icon className="h-5 w-5" aria-hidden="true" />
              <span className="max-w-full truncate">{item.shortLabel}</span>
            </button>
          )
        })}
      </nav>
    </aside>
  )
}

export function ActionDock({
  primaryAction,
  actions,
  busy,
  onSelect,
}: {
  primaryAction: EntryActionCard | null
  actions: EntryActionCard[]
  busy: boolean
  onSelect: (action: EntryActionCard) => void
}) {
  const railActions = actions.filter((action) => action.kind !== 'form')
  const secondary = primaryAction ? railActions.filter((action) => action.id !== primaryAction.id) : railActions
  if (!primaryAction && secondary.length === 0) return null

  return (
    <section className="mb-3 rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-white/10 dark:bg-white/[0.03]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Next best action</div>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
            {primaryAction ? primaryAction.description || 'Use this backend-owned action to continue the flow.' : 'No backend action is currently required.'}
          </p>
        </div>
        {primaryAction && (
          <button
            type="button"
            disabled={busy || Boolean(primaryAction.disabled_reason)}
            onClick={() => onSelect(primaryAction)}
            className="inline-flex shrink-0 items-center justify-center rounded-full border border-sky-300 bg-sky-50 px-4 py-2 text-xs font-semibold text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-300"
          >
            {primaryAction.label}
          </button>
        )}
      </div>
      {secondary.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {secondary.map((action) => (
            <button
              key={action.id}
              type="button"
              disabled={busy || Boolean(action.disabled_reason)}
              title={action.description ?? undefined}
              onClick={() => onSelect(action)}
              className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 transition hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-white/[0.05] dark:text-slate-300 dark:hover:border-sky-500/40 dark:hover:bg-sky-500/10"
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </section>
  )
}

export function ContextLens({
  title,
  capability,
  children,
  uiArtifacts,
  onOpenCanvas,
  onClose,
}: {
  title: string
  capability?: OperatorCapabilityDefinition
  children: JSX.Element
  uiArtifacts: EntryUIArtifact[]
  onOpenCanvas: (artifactId: string) => void
  onClose: () => void
}) {
  const canvasArtifact = uiArtifacts.find((artifact) => artifact.surface === 'canvas' || artifact.surface === 'both')
  return (
    <aside className="operator-side-panel flex min-w-0 flex-col rounded-2xl border border-slate-200 bg-white p-3 shadow-2xl dark:border-white/10 dark:bg-[#09090b] lg:shadow-sm">
      <div className="mb-3 flex shrink-0 items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-600 dark:text-sky-300">Context lens</p>
          <h2 className="text-sm font-semibold text-slate-950 dark:text-white">{title}</h2>
          {capability && <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{capability.description}</p>}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {canvasArtifact && (
            <button
              type="button"
              onClick={() => onOpenCanvas(canvasArtifact.id)}
              className="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
            >
              Canvas
            </button>
          )}
          <button type="button" onClick={onClose} className="rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-500 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5">
            Close
          </button>
        </div>
      </div>
      {capability && (
        <div className="mb-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs dark:border-white/10 dark:bg-white/[0.03]">
          <div className="font-semibold text-slate-700 dark:text-slate-200">Evidence surface</div>
          <p className="mt-1 leading-5 text-slate-500 dark:text-slate-400">{capability.evidenceSurface}</p>
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-y-auto lg:max-h-[calc(100vh-13rem)]">{children}</div>
    </aside>
  )
}

export function EvidenceDrawer({
  open,
  onToggle,
  mode,
  graphNode,
  runId,
  sessionId,
  readiness,
  uiArtifacts,
  autonomyLevel,
  onAutonomyChange,
}: {
  open: boolean
  onToggle: () => void
  mode: OperatorExperienceMode
  graphNode?: GatewayNode | null
  runId?: string | null
  sessionId?: string | null
  readiness: OperatorReadiness
  uiArtifacts: EntryUIArtifact[]
  autonomyLevel: AutonomyLevel
  onAutonomyChange: (level: AutonomyLevel) => void
}) {
  const evidenceArtifacts = useMemo(
    () => uiArtifacts.filter((artifact) => artifact.widget_type === 'trace_summary' || artifact.widget_type === 'tool_candidate_list' || artifact.widget_type === 'readiness_summary' || artifact.widget_type === 'learning_candidate'),
    [uiArtifacts],
  )

  return (
    <section className="border-t border-slate-200 bg-white dark:border-white/10 dark:bg-[#09090b]">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-2 text-left text-xs font-semibold uppercase tracking-[0.14em] text-slate-500 transition hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-white/[0.04] sm:px-6"
      >
        <span className="inline-flex items-center gap-2"><FileSearch className="h-3.5 w-3.5" /> Evidence and controls</span>
        {open ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
      </button>
      {open && (
        <div className="grid gap-3 px-4 pb-4 sm:px-6 lg:grid-cols-3">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs dark:border-white/10 dark:bg-white/[0.03]">
            <div className="flex items-center gap-2 font-semibold text-slate-700 dark:text-slate-200">
              <CircleHelp className="h-4 w-4" />
              Runtime trace
            </div>
            <dl className="mt-3 space-y-2 text-slate-500 dark:text-slate-400">
              <div><dt className="font-medium text-slate-700 dark:text-slate-200">Mode</dt><dd>{mode}</dd></div>
              <div><dt className="font-medium text-slate-700 dark:text-slate-200">Stage</dt><dd>{graphNode ? graphNodeLabels[graphNode] : 'Workspace chat'}</dd></div>
              <div><dt className="font-medium text-slate-700 dark:text-slate-200">Run</dt><dd className="break-all">{runId || 'Not emitted yet'}</dd></div>
              <div><dt className="font-medium text-slate-700 dark:text-slate-200">Session</dt><dd className="break-all">{sessionId || 'Not emitted yet'}</dd></div>
              <div><dt className="font-medium text-slate-700 dark:text-slate-200">Graph</dt><dd>{graphNode ? 'RouteDeck entry graph' : 'Workspace bridge'}</dd></div>
            </dl>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs dark:border-white/10 dark:bg-white/[0.03]">
            <div className="flex items-center gap-2 font-semibold text-slate-700 dark:text-slate-200">
              <SlidersHorizontal className="h-4 w-4" />
              Autonomy ladder
            </div>
            <div className="mt-3 space-y-2">
              {autonomyOptions.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => onAutonomyChange(option.id)}
                  className={cn(
                    'block w-full rounded-lg border px-3 py-2 text-left transition',
                    autonomyLevel === option.id
                      ? 'border-sky-300 bg-sky-50 text-sky-800 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-200'
                      : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300 dark:hover:bg-white/[0.07]',
                  )}
                >
                  <span className="block font-semibold">{option.label}</span>
                  <span className="mt-1 block leading-5 opacity-80">{option.description}</span>
                </button>
              ))}
            </div>
            <p className="mt-3 flex items-start gap-2 rounded-lg bg-amber-50 p-2 text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">
              <Lock className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              REST execution still requires backend approval gates until the execution slice is wired.
            </p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs dark:border-white/10 dark:bg-white/[0.03]">
            <div className="flex items-center gap-2 font-semibold text-slate-700 dark:text-slate-200">
              <ShieldCheck className="h-4 w-4" />
              Evidence summary
            </div>
            <p className="mt-2 leading-5 text-slate-500 dark:text-slate-400">{readiness.detail}</p>
            {evidenceArtifacts.length > 0 ? (
              <div className="mt-3 space-y-2">
                {evidenceArtifacts.slice(0, 2).map((artifact) => (
                  <EntryArtifactRenderer key={artifact.id} artifact={artifact} compact />
                ))}
              </div>
            ) : (
              <p className="mt-3 rounded-lg border border-dashed border-slate-200 p-3 text-slate-500 dark:border-white/10 dark:text-slate-400">
                Tool calls, citations, approval requests, and learning candidates will accumulate here as later slices emit them.
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
