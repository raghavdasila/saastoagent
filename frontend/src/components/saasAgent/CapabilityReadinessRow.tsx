import { capabilityItems, type CapabilityStatus } from '@/stores/saasAgentStore'
import type { SaaSAgentStats } from '@/types/domain'

const statusLabel: Record<CapabilityStatus, string> = {
  active: 'Active',
  ready: 'Ready',
  pending: 'Next',
  locked: 'Locked',
}

const statusClass: Record<CapabilityStatus, string> = {
  active: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  ready: 'border-sky-200 bg-sky-50 text-sky-700',
  pending: 'border-amber-200 bg-amber-50 text-amber-700',
  locked: 'border-slate-200 bg-slate-50 text-slate-500 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-400',
}

interface CapabilityReadinessRowProps {
  stats?: SaaSAgentStats
}

export function CapabilityReadinessRow({ stats }: CapabilityReadinessRowProps) {
  const counts = {
    connect: stats?.connections_count ?? 0,
    entities: 0,
    actions: stats?.tools_count ?? 0,
    chat: 1,
    qa: stats?.learnings_count ?? 0,
  }

  return (
    <div className="grid gap-3 md:grid-cols-5" aria-label="Agent capability readiness">
      {capabilityItems.map((item) => (
        <div key={item.id} className="surface-card rounded-lg p-4">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-semibold text-slate-900 dark:text-white">{item.shortLabel}</span>
            <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${statusClass[item.status]}`}>
              {statusLabel[item.status]}
            </span>
          </div>
          <div className="mt-3 text-2xl font-semibold text-slate-950 dark:text-white">{counts[item.id]}</div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-500">{item.slice}</div>
        </div>
      ))}
    </div>
  )
}
