import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { useWorkspace } from '@/context/WorkspaceContext'
import { api } from '@/lib/api'
import type { Workspace, WorkspaceStats } from '@/types/domain'

function StatCard({ label, value, hint }: { label: string; value: string | number; hint: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm font-medium text-slate-500">{label}</div>
      <div className="mt-3 text-3xl font-semibold text-slate-900">{value}</div>
      <div className="mt-2 text-sm text-slate-500">{hint}</div>
    </div>
  )
}

export function WorkspaceOverviewPage() {
  const navigate = useNavigate()
  const { workspaceId } = useWorkspace()

  const { data: workspace } = useQuery({
    queryKey: ['workspace', workspaceId],
    queryFn: () => api.get<Workspace>(`/workspaces/${workspaceId}`),
    enabled: !!workspaceId,
  })

  const { data: stats } = useQuery({
    queryKey: ['workspace-stats', workspaceId],
    queryFn: () => api.get<WorkspaceStats>(`/workspaces/${workspaceId}/stats`),
    enabled: !!workspaceId,
  })

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-600">Workspace agent</div>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">
          {workspace?.name || 'Workspace'}
        </h1>
        <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600">
          Slice 1 is now live: this workspace is the visible agent container. Later slices will attach REST connections, action catalogs, entity exploration, chat, execution, and QA directly to this workspace.
        </p>

        <div className="mt-6 flex flex-wrap gap-3 text-sm text-slate-600">
          <div className="rounded-full bg-slate-100 px-3 py-1">Slug: {workspace?.slug || 'loading'}</div>
          <div className="rounded-full bg-slate-100 px-3 py-1">Role: {workspace?.role || 'member'}</div>
          <div className="rounded-full bg-slate-100 px-3 py-1">Workspace ID: {workspaceId}</div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Connections" value={stats?.connections_count ?? 0} hint="Starts in Slice 2" />
        <StatCard label="Tools" value={stats?.tools_count ?? 0} hint="Generated after onboarding" />
        <StatCard label="Learnings" value={stats?.learnings_count ?? 0} hint="Improvement loop lands later" />
        <StatCard label="Maturity" value={`${Math.round((stats?.maturity ?? 0) * 100)}%`} hint="Tracks readiness over time" />
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Quick actions</h2>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <button
              className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-left transition hover:border-sky-300 hover:bg-white"
              onClick={() => navigate(`/w/${workspaceId}/connections`)}
              type="button"
            >
              <div className="text-lg font-semibold text-slate-900">Open connections</div>
              <div className="mt-2 text-sm text-slate-600">Reserved for REST onboarding in Slice 2</div>
            </button>

            <button
              className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-left transition hover:border-sky-300 hover:bg-white"
              onClick={() => navigate(`/w/${workspaceId}/chat`)}
              type="button"
            >
              <div className="text-lg font-semibold text-slate-900">Open chat shell</div>
              <div className="mt-2 text-sm text-slate-600">Placeholder route to keep the shell stable for later slices</div>
            </button>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Slice roadmap</h2>
          <ol className="mt-5 space-y-3 text-sm leading-6 text-slate-600">
            <li><span className="font-semibold text-slate-900">1.</span> Workspace-as-agent shell</li>
            <li><span className="font-semibold text-slate-900">2.</span> REST onboarding and action catalog</li>
            <li><span className="font-semibold text-slate-900">3.</span> Simplified entity explorer</li>
            <li><span className="font-semibold text-slate-900">4.</span> REST tool-finder chat</li>
            <li><span className="font-semibold text-slate-900">5.</span> Agentic REST execution</li>
            <li><span className="font-semibold text-slate-900">6.</span> QA, tuning, and self-learning loop</li>
          </ol>
        </div>
      </section>
    </div>
  )
}
