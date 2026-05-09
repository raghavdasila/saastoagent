import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { WorkspaceLaunchPad } from '@/components/workspace/WorkspaceLaunchPad'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import type { Workspace } from '@/types/domain'

function WorkspaceListItem({
  workspace,
  isCurrent,
  onOpen,
}: {
  workspace: Workspace
  isCurrent: boolean
  onOpen: () => void
}) {
  return (
    <button
      className={[
        'surface-card flex w-full items-center justify-between rounded-3xl px-5 py-5 text-left transition',
        isCurrent
          ? 'border-sky-400 shadow-[0_0_0_1px_rgba(56,189,248,0.35)] dark:border-sky-500/40'
          : 'hover:border-slate-300 dark:hover:border-white/15',
      ].join(' ')}
      onClick={onOpen}
      type="button"
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <div className="truncate text-base font-semibold text-slate-950 dark:text-white">{workspace.name}</div>
          {isCurrent && (
            <span className="rounded-full bg-sky-100 px-2 py-0.5 text-[11px] font-medium text-sky-700 dark:bg-sky-500/10 dark:text-sky-300">
              Current
            </span>
          )}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <span>/{workspace.slug}</span>
          <span className="h-1 w-1 rounded-full bg-slate-300 dark:bg-slate-600" />
          <span className="capitalize">{workspace.role || 'member'}</span>
        </div>
      </div>
      <ArrowRight className="h-4 w-4 shrink-0 text-slate-400 dark:text-slate-500" aria-hidden="true" />
    </button>
  )
}

export function DashboardPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const currentWorkspaceId = useWorkspaceStore((state) => state.workspaceId)
  const setWorkspaceId = useWorkspaceStore((state) => state.setWorkspaceId)
  const [error, setError] = useState('')

  const { data: workspaces, isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: () => api.get<Workspace[]>('/workspaces'),
  })

  useEffect(() => {
    if (isLoading || !workspaces) {
      return
    }

    if (workspaces.length === 1) {
      setWorkspaceId(workspaces[0].id)
      navigate(`/w/${workspaces[0].id}`, { replace: true })
    }
  }, [isLoading, navigate, setWorkspaceId, workspaces])

  const createWorkspace = useMutation({
    mutationFn: (body: { name: string; slug: string }) => api.post<Workspace>('/workspaces', body),
    onSuccess: async (workspace) => {
      await queryClient.invalidateQueries({ queryKey: ['workspaces'] })
      setError('')
      setWorkspaceId(workspace.id)
      navigate(`/w/${workspace.id}`)
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create workspace')
    },
  })

  const workspacesList = workspaces || []
  const primaryWorkspace = useMemo(() => {
    if (workspacesList.length === 0) {
      return null
    }

    return workspacesList.find((workspace) => workspace.id === currentWorkspaceId) || workspacesList[0]
  }, [currentWorkspaceId, workspacesList])

  return (
    <div className="grid gap-6 xl:grid-cols-[22rem_1fr]">
      <aside className="space-y-6">
        <section className="surface-card rounded-3xl p-6 sm:p-8">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">Operator navigation</div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            {workspacesList.length === 0 ? 'Launch your first operator' : 'SaaSToAgent Operator'}
          </h1>
          <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-400">
            {workspacesList.length === 0
              ? 'Start with a focused SaaS operating job. The launch flow stays in the sidebar and the workspace list stays clean.'
              : primaryWorkspace
                ? `Current workspace: ${primaryWorkspace.name}. Pick a workspace from the list or launch another operator here.`
                : 'Pick a workspace from the list or launch another operator here.'}
          </p>

          {primaryWorkspace && (
            <button
              className="surface-solid-button mt-6 inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium"
              onClick={() => navigate(`/w/${primaryWorkspace.id}`)}
              type="button"
            >
              Open current operator
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </section>

        <WorkspaceLaunchPad
          title={workspacesList.length === 0 ? 'Launch SaaSToAgent Operator' : 'Launch another SaaSToAgent Operator'}
          description={
            workspacesList.length === 0
              ? 'Describe the first SaaS operating job this operator should own.'
              : 'Describe the next SaaS operating job when a separate operator should own it.'
          }
          error={error}
          isPending={createWorkspace.isPending}
          onCreate={(body) => createWorkspace.mutate(body)}
        />
      </aside>

      <section className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">Workspace list</div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
              {user?.display_name ? `${user.display_name}'s operators` : 'Operator workspaces'}
            </h2>
          </div>

          {!isLoading && workspacesList.length > 0 && (
            <div className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600 dark:bg-white/[0.06] dark:text-slate-400">
              {workspacesList.length} workspace{workspacesList.length === 1 ? '' : 's'}
            </div>
          )}
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((item) => (
              <div key={item} className="surface-card h-24 rounded-3xl animate-pulse" />
            ))}
          </div>
        ) : workspacesList.length > 0 ? (
          <div className="space-y-3">
            {workspacesList.map((workspace) => (
              <WorkspaceListItem
                key={workspace.id}
                workspace={workspace}
                isCurrent={workspace.id === primaryWorkspace?.id}
                onOpen={() => {
                  setWorkspaceId(workspace.id)
                  navigate(`/w/${workspace.id}`)
                }}
              />
            ))}
          </div>
        ) : (
          <section className="surface-card rounded-3xl p-6 sm:p-8">
            <div className="text-sm font-semibold text-slate-950 dark:text-white">No operators launched yet</div>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
              Once you create an operator, it will appear here with its slug and access role.
            </p>
          </section>
        )}
      </section>
    </div>
  )
}
