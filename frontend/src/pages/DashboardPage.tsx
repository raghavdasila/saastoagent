import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { WorkspaceCreateModal } from '@/components/workspace/WorkspaceCreateModal'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import type { Workspace } from '@/types/domain'

export function DashboardPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const currentWorkspaceId = useWorkspaceStore((state) => state.workspaceId)
  const workspaceModalOpen = useWorkspaceStore((state) => state.workspaceModalOpen)
  const openWorkspaceCreate = useWorkspaceStore((state) => state.openWorkspaceCreate)
  const closeWorkspaceCreate = useWorkspaceStore((state) => state.closeWorkspaceCreate)
  const setWorkspaceId = useWorkspaceStore((state) => state.setWorkspaceId)
  const [error, setError] = useState('')

  const { data: workspaces, isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: () => api.get<Workspace[]>('/workspaces'),
  })

  useEffect(() => {
    if (isLoading || !workspaces || workspaceModalOpen) {
      return
    }

    if (workspaces.length === 1) {
      setWorkspaceId(workspaces[0].id)
      navigate(`/w/${workspaces[0].id}`, { replace: true })
    }
  }, [isLoading, navigate, setWorkspaceId, workspaceModalOpen, workspaces])

  const createWorkspace = useMutation({
    mutationFn: (body: { name: string; slug: string }) => api.post<Workspace>('/workspaces', body),
    onSuccess: async (workspace) => {
      await queryClient.invalidateQueries({ queryKey: ['workspaces'] })
      setError('')
      closeWorkspaceCreate()
      setWorkspaceId(workspace.id)
      navigate(`/w/${workspace.id}`)
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create workspace')
    },
  })

  const subtitle = useMemo(() => {
    if (!workspaces || workspaces.length === 0) {
      return 'Create your first agent workspace.'
    }
    if (workspaces.length === 1) {
      return 'Opening your agent workspace.'
    }
    return `You have ${workspaces.length} agent workspaces ready.`
  }, [workspaces])

  const workspacesList = workspaces || []
  const primaryWorkspace = useMemo(() => {
    if (workspacesList.length === 0) {
      return null
    }

    return workspacesList.find((workspace) => workspace.id === currentWorkspaceId) || workspacesList[0]
  }, [currentWorkspaceId, workspacesList])
  const otherWorkspaces = useMemo(
    () => workspacesList.filter((workspace) => workspace.id !== primaryWorkspace?.id),
    [primaryWorkspace?.id, workspacesList],
  )

  if (!isLoading && workspacesList.length === 0) {
    return (
      <>
        <div className="surface-card mx-auto max-w-4xl rounded-3xl p-8 sm:p-10">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">Agent desk</div>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl">
            Start with the agent you want to work through
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-400">
            Create a workspace-owned agent, connect its REST surface, and use conversation as the control plane for planning, execution, QA, and learnings.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <button
              className="surface-solid-button inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium"
              onClick={() => {
                setError('')
                openWorkspaceCreate()
              }}
              type="button"
            >
              Create first agent
              <Plus className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            <div className="surface-muted rounded-2xl p-4">
              <div className="text-sm font-semibold text-slate-950 dark:text-white">1. Define the job</div>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">Anchor the workspace around the outcome the agent should own, not around generic configuration.</p>
            </div>
            <div className="surface-muted rounded-2xl p-4">
              <div className="text-sm font-semibold text-slate-950 dark:text-white">2. Connect the API</div>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">Activate a REST source so the agent can inspect actions, infer entities, and prepare workflows.</p>
            </div>
            <div className="surface-muted rounded-2xl p-4">
              <div className="text-sm font-semibold text-slate-950 dark:text-white">3. Work through chat</div>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">Use the thread as the control surface for intent, execution, QA, and later learnings.</p>
            </div>
          </div>
        </div>

        <WorkspaceCreateModal
          error={error}
          isOpen={workspaceModalOpen}
          isPending={createWorkspace.isPending}
          onClose={closeWorkspaceCreate}
          onCreate={(body) => createWorkspace.mutate(body)}
        />
      </>
    )
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
      <section className="space-y-6">
        <div className="surface-card rounded-3xl p-8 sm:p-10">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">Agent desk</div>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl">
            {primaryWorkspace ? `Continue with ${primaryWorkspace.name}` : user?.display_name ? `Welcome, ${user.display_name}` : 'Choose an agent'}
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-400">
            {primaryWorkspace
              ? 'Use the workspace agent as the operating surface. Open it, state the outcome you want, and let the agent drive setup, action discovery, and later execution.'
              : subtitle}
          </p>

          {primaryWorkspace && (
            <div className="mt-6 flex flex-wrap gap-3 text-sm text-slate-600 dark:text-slate-400">
              <div className="rounded-full bg-slate-100 px-3 py-1 dark:bg-white/[0.06]">/{primaryWorkspace.slug}</div>
              <div className="rounded-full bg-slate-100 px-3 py-1 dark:bg-white/[0.06]">Role: {primaryWorkspace.role || 'member'}</div>
            </div>
          )}

          {primaryWorkspace && (
            <div className="mt-8 flex flex-wrap gap-3">
              <button
                className="surface-solid-button inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium"
                onClick={() => navigate(`/w/${primaryWorkspace.id}`)}
                type="button"
              >
                Open agent
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </button>
              <button
                className="surface-outline-button inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium"
                onClick={() => {
                  setError('')
                  openWorkspaceCreate()
                }}
                type="button"
              >
                Create another agent
                <Plus className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          )}
        </div>

        {otherWorkspaces.length > 0 && (
          <section className="surface-card rounded-3xl p-6 sm:p-8">
            <h2 className="text-xl font-semibold text-slate-950 dark:text-white">Other agents</h2>
            <div className="mt-5 space-y-3">
              {otherWorkspaces.map((workspace) => (
                <button
                  key={workspace.id}
                  className="surface-muted flex w-full items-center justify-between rounded-2xl px-4 py-4 text-left transition hover:border-sky-300 dark:hover:border-white/20"
                  onClick={() => navigate(`/w/${workspace.id}`)}
                  type="button"
                >
                  <div>
                    <div className="text-sm font-semibold text-slate-950 dark:text-white">{workspace.name}</div>
                    <div className="mt-1 text-sm text-slate-500 dark:text-slate-500">/{workspace.slug}</div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-400 dark:text-slate-500" aria-hidden="true" />
                </button>
              ))}
            </div>
          </section>
        )}
      </section>

      <aside className="space-y-6">
        <section className="surface-card rounded-3xl p-6 sm:p-8">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">Create agent</div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">Start another workspace agent</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-400">
            Create a new agent when you need a separate SaaS operating boundary, not just another admin container.
          </p>
          <button
            className="surface-solid-button mt-6 inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium"
            onClick={() => {
              setError('')
              openWorkspaceCreate()
            }}
            type="button"
          >
            New agent
            <Plus className="h-4 w-4" aria-hidden="true" />
          </button>
        </section>

        <section className="surface-card rounded-3xl p-6 sm:p-8">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">How this works</div>
          <div className="mt-4 space-y-4 text-sm leading-6 text-slate-600 dark:text-slate-400">
            <p><span className="font-semibold text-slate-950 dark:text-white">1.</span> Anchor the workspace around the job the agent should own.</p>
            <p><span className="font-semibold text-slate-950 dark:text-white">2.</span> Connect the REST API that gives the agent real actions.</p>
            <p><span className="font-semibold text-slate-950 dark:text-white">3.</span> Use chat as the control plane for execution, QA, and learnings.</p>
          </div>
        </section>
      </aside>

      <WorkspaceCreateModal
        error={error}
        isOpen={workspaceModalOpen}
        isPending={createWorkspace.isPending}
        onClose={closeWorkspaceCreate}
        onCreate={(body) => createWorkspace.mutate(body)}
      />
    </div>
  )
}
