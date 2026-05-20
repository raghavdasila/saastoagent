import { useMemo } from 'react'
import type { ReactNode } from 'react'

import type { EntryUIArtifact } from '@/types/entry'

const ALLOWED_TAGS = new Set([
  'a', 'b', 'br', 'circle', 'code', 'div', 'em', 'g', 'h1', 'h2', 'h3', 'line',
  'li', 'ol', 'p', 'path', 'polyline', 'rect', 'small', 'span', 'strong', 'svg',
  'text', 'ul',
])

const ALLOWED_ATTRS = new Set([
  'aria-label', 'class', 'cx', 'cy', 'd', 'fill', 'font-family', 'font-size',
  'font-weight', 'height', 'href', 'role', 'rx', 'stroke', 'stroke-linecap',
  'stroke-width', 'viewBox', 'viewbox', 'width', 'x', 'x1', 'x2', 'xmlns', 'y', 'y1', 'y2',
])

function sanitizeMarkup(markup: string): string {
  if (typeof window === 'undefined') return ''
  const parser = new DOMParser()
  const doc = parser.parseFromString(`<div>${markup}</div>`, 'text/html')
  const root = doc.body.firstElementChild
  if (!root) return ''

  const visit = (node: Element) => {
    for (const child of Array.from(node.children)) {
      if (!ALLOWED_TAGS.has(child.tagName.toLowerCase())) {
        child.remove()
        continue
      }
      for (const attr of Array.from(child.attributes)) {
        const attrName = attr.name
        const lower = attrName.toLowerCase()
        const value = attr.value.trim()
        const isUnsafeUrl = ['href', 'src'].includes(lower) && !value.startsWith('#') && !value.startsWith('/')
        if (lower.startsWith('on') || lower === 'style' || isUnsafeUrl || !ALLOWED_ATTRS.has(attrName)) {
          child.removeAttribute(attrName)
        }
      }
      visit(child)
    }
  }

  visit(root)
  return root.innerHTML
}

export function EntryArtifactRenderer({ artifact, compact = false }: { artifact: EntryUIArtifact; compact?: boolean }) {
  if (artifact.kind === 'markup') {
    return <MarkupArtifact artifact={artifact} compact={compact} />
  }

  switch (artifact.widget_type) {
    case 'platform_overview':
      return <PlatformOverview artifact={artifact} compact={compact} />
    case 'onboarding_checklist':
      return <OnboardingChecklist artifact={artifact} compact={compact} />
    case 'setup_draft_summary':
      return <SetupDraftSummary artifact={artifact} compact={compact} />
    case 'api_connection_preview':
      return <SetupDraftSummary artifact={artifact} compact={compact} />
    case 'knowledge_citations':
      return <KnowledgeCitations artifact={artifact} compact={compact} />
    case 'readiness_summary':
      return <ReadinessSummary artifact={artifact} compact={compact} />
    case 'tool_candidate_list':
      return <ToolCandidateList artifact={artifact} compact={compact} />
    case 'execution_plan':
      return <ExecutionPlan artifact={artifact} compact={compact} />
    case 'approval_request':
      return <ApprovalRequest artifact={artifact} compact={compact} />
    case 'trace_summary':
      return <TraceSummary artifact={artifact} compact={compact} />
    case 'learning_candidate':
      return <LearningCandidate artifact={artifact} compact={compact} />
    default:
      return <UnsupportedArtifact artifact={artifact} />
  }
}

function ArtifactFrame({
  title,
  children,
  compact,
}: {
  title?: string | null
  children: ReactNode
  compact?: boolean
}) {
  return (
    <section className={['min-w-0 rounded-lg border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#0b0b0d]', compact ? 'p-3' : 'p-4'].join(' ')}>
      {title && <h3 className="text-sm font-semibold text-slate-950 dark:text-white">{title}</h3>}
      <div className={title ? 'mt-3 min-w-0' : 'min-w-0'}>{children}</div>
    </section>
  )
}

function PlatformOverview({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const cards = Array.isArray(artifact.payload?.cards) ? artifact.payload.cards : []
  return (
    <ArtifactFrame title={artifact.title} compact={compact}>
      <div className="grid min-w-0 grid-cols-[repeat(auto-fit,minmax(min(100%,13rem),1fr))] gap-3">
        {cards.map((card, index) => {
          const item = card as { title?: string; body?: string }
          return (
            <div key={index} className="min-w-0 rounded-md border border-slate-100 bg-slate-50 p-3 dark:border-white/10 dark:bg-white/5">
              <div className="text-xs font-semibold uppercase tracking-wide text-sky-600 dark:text-sky-300">{item.title}</div>
              <p className="mt-2 text-xs leading-5 text-slate-600 dark:text-slate-300">{item.body}</p>
            </div>
          )
        })}
      </div>
    </ArtifactFrame>
  )
}

function OnboardingChecklist({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const items = Array.isArray(artifact.payload?.items) ? artifact.payload.items : []
  return (
    <ArtifactFrame title={artifact.title} compact={compact}>
      <div className="space-y-2">
        {items.map((item, index) => {
          const row = item as { label?: string; status?: string }
          const active = row.status === 'active'
          return (
            <div key={index} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200">
              <span className={['h-2.5 w-2.5 rounded-full', active ? 'bg-sky-500' : 'bg-slate-300 dark:bg-slate-700'].join(' ')} />
              <span>{row.label}</span>
            </div>
          )
        })}
      </div>
    </ArtifactFrame>
  )
}

function SetupDraftSummary({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const rawDraft = (artifact.payload?.draft || artifact.payload || {}) as Record<string, unknown>
  const apiDraft = (rawDraft.api_draft || rawDraft) as Record<string, unknown>
  const rows: Array<[string, string]> = [
    ['SaaS Agent', rawDraft.saas_agent_name || rawDraft.saas_agent_job],
    ['Connection', apiDraft.name],
    ['Base URL', apiDraft.base_url],
    ['Spec URL', apiDraft.spec_url],
    ['Auth', apiDraft.auth_type],
  ].filter((row): row is [string, string] => typeof row[1] === 'string' && row[1].length > 0)
  return (
    <ArtifactFrame title={artifact.title || 'Setup Draft'} compact={compact}>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">No draft details captured yet.</p>
      ) : (
        <dl className="grid gap-2 text-sm">
          {rows.map(([label, value]) => (
            <div key={String(label)} className="grid gap-1 sm:grid-cols-[8rem_1fr]">
              <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</dt>
              <dd className="break-words text-slate-700 dark:text-slate-200">{String(value)}</dd>
            </div>
          ))}
        </dl>
      )}
    </ArtifactFrame>
  )
}

function KnowledgeCitations({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const sources = Array.isArray(artifact.payload?.sources) ? artifact.payload.sources : []
  return (
    <ArtifactFrame title={artifact.title} compact={compact}>
      <div className="space-y-2">
        {sources.map((source, index) => {
          const row = source as { title?: string; source_path?: string; excerpt?: string }
          return (
            <div key={index} className="rounded-md bg-slate-50 p-3 text-xs dark:bg-white/5">
              <div className="font-semibold text-slate-800 dark:text-slate-100">{row.title}</div>
              <div className="mt-1 text-slate-400">{row.source_path}</div>
              <p className="mt-2 leading-5 text-slate-600 dark:text-slate-300">{row.excerpt}</p>
            </div>
          )
        })}
      </div>
    </ArtifactFrame>
  )
}

function ReadinessSummary({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const checks = Array.isArray(artifact.payload?.checks) ? artifact.payload.checks : []
  return (
    <ArtifactFrame title={artifact.title || 'Operator Readiness'} compact={compact}>
      <div className="space-y-2">
        {checks.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No readiness checks emitted yet.</p>
        ) : checks.map((check, index) => {
          const row = check as { label?: string; status?: string; detail?: string }
          return (
            <div key={index} className="rounded-md border border-slate-100 bg-slate-50 p-3 text-sm dark:border-white/10 dark:bg-white/5">
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium text-slate-800 dark:text-slate-100">{row.label}</span>
                <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:bg-black/20">{row.status || 'unknown'}</span>
              </div>
              {row.detail && <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{row.detail}</p>}
            </div>
          )
        })}
      </div>
    </ArtifactFrame>
  )
}

function ToolCandidateList({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const tools = Array.isArray(artifact.payload?.tools) ? artifact.payload.tools : []
  return (
    <ArtifactFrame title={artifact.title || 'Tool Candidates'} compact={compact}>
      <div className="space-y-2">
        {tools.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No tool candidates selected yet.</p>
        ) : tools.map((tool, index) => {
          const row = tool as { name?: string; reason?: string; risk?: string }
          return (
            <div key={index} className="rounded-md bg-slate-50 p-3 text-sm dark:bg-white/5">
              <div className="font-semibold text-slate-800 dark:text-slate-100">{row.name || `Tool ${index + 1}`}</div>
              {row.reason && <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{row.reason}</p>}
              {row.risk && <div className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-amber-600 dark:text-amber-300">Risk: {row.risk}</div>}
            </div>
          )
        })}
      </div>
    </ArtifactFrame>
  )
}

function ExecutionPlan({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const steps = Array.isArray(artifact.payload?.steps) ? artifact.payload.steps : []
  return (
    <ArtifactFrame title={artifact.title || 'Execution Plan'} compact={compact}>
      <ol className="space-y-2">
        {steps.length === 0 ? (
          <li className="text-sm text-slate-500 dark:text-slate-400">No execution plan emitted yet.</li>
        ) : steps.map((step, index) => {
          const row = step as { title?: string; detail?: string }
          return (
            <li key={index} className="grid grid-cols-[1.5rem_1fr] gap-2 text-sm">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white dark:bg-white dark:text-slate-950">{index + 1}</span>
              <span>
                <span className="block font-semibold text-slate-800 dark:text-slate-100">{row.title || `Step ${index + 1}`}</span>
                {row.detail && <span className="mt-1 block text-xs leading-5 text-slate-500 dark:text-slate-400">{row.detail}</span>}
              </span>
            </li>
          )
        })}
      </ol>
    </ArtifactFrame>
  )
}

function ApprovalRequest({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const reason = typeof artifact.payload?.reason === 'string' ? artifact.payload.reason : 'This action needs explicit user approval before execution.'
  const risk = typeof artifact.payload?.risk === 'string' ? artifact.payload.risk : null
  return (
    <ArtifactFrame title={artifact.title || 'Approval Request'} compact={compact}>
      <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
        <div className="font-semibold">Approval required</div>
        <p className="mt-1 leading-5">{reason}</p>
        {risk && <p className="mt-2 text-xs font-semibold uppercase tracking-wide">Risk: {risk}</p>}
      </div>
    </ArtifactFrame>
  )
}

function TraceSummary({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const events = Array.isArray(artifact.payload?.events) ? artifact.payload.events : []
  return (
    <ArtifactFrame title={artifact.title || 'Trace Summary'} compact={compact}>
      <div className="space-y-2">
        {events.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No trace events emitted yet.</p>
        ) : events.map((event, index) => {
          const row = event as { label?: string; status?: string; at?: string }
          return (
            <div key={index} className="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-xs dark:bg-white/5">
              <span className="font-medium text-slate-700 dark:text-slate-200">{row.label || `Event ${index + 1}`}</span>
              <span className="text-slate-400">{row.status || row.at || 'recorded'}</span>
            </div>
          )
        })}
      </div>
    </ArtifactFrame>
  )
}

function LearningCandidate({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const summary = typeof artifact.payload?.summary === 'string' ? artifact.payload.summary : 'A governed learning candidate can be reviewed before it changes future behavior.'
  return (
    <ArtifactFrame title={artifact.title || 'Learning Candidate'} compact={compact}>
      <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100">
        <div className="font-semibold">Review before saving</div>
        <p className="mt-1 leading-5">{summary}</p>
      </div>
    </ArtifactFrame>
  )
}

function MarkupArtifact({ artifact, compact }: { artifact: EntryUIArtifact; compact?: boolean }) {
  const sanitized = useMemo(() => sanitizeMarkup(artifact.markup || ''), [artifact.markup])
  return (
    <ArtifactFrame title={artifact.title} compact={compact}>
      <div className="overflow-hidden rounded-md bg-slate-950 p-2" dangerouslySetInnerHTML={{ __html: sanitized }} />
    </ArtifactFrame>
  )
}

function UnsupportedArtifact({ artifact }: { artifact: EntryUIArtifact }) {
  return (
    <ArtifactFrame title={artifact.title || 'Unsupported artifact'} compact>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        This artifact type is not available in the current renderer.
      </p>
    </ArtifactFrame>
  )
}
