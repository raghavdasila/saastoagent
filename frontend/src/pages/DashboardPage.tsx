import { type FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { Workspace } from '@/types/domain'

export function DashboardPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [error, setError] = useState('')

  const { data: workspaces, isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: () => api.get<Workspace[]>('/workspaces'),
  })

  const createWorkspace = useMutation({
    mutationFn: (body: { name: string; slug: string }) => api.post<Workspace>('/workspaces', body),
    onSuccess: async (workspace) => {
      await queryClient.invalidateQueries({ queryKey: ['workspaces'] })
      setName('')
      setSlug('')
      setError('')
      navigate(`/w/${workspace.id}`)
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create workspace')
    },
  })

  const subtitle = useMemo(() => {
    if (!workspaces || workspaces.length === 0) {
      return 'Create your first workspace agent to begin Slice 1.'
    }
    if (workspaces.length === 1) {
      return 'You have 1 workspace agent ready.'
    }
    return `You have ${workspaces.length} workspace agents ready.`
  }, [workspaces])

  const handleNameChange = (value: string) => {
    setName(value)
    setSlug(
      value
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .trim()
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-'),
    )
  }

  const handleCreate = (event: FormEvent) => {
    event.preventDefault()
    createWorkspace.mutate({ name, slug })
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
      <section>
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-600">Slice 1</div>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">
            {user?.display_name ? `Welcome, ${user.display_name}` : 'Workspace agents'}
          </h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">{subtitle}</p>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {(workspaces || []).map((workspace) => (
              <button
                key={workspace.id}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-left transition hover:-translate-y-0.5 hover:border-sky-300 hover:bg-white"
                onClick={() => navigate(`/w/${workspace.id}`)}
                type="button"
              >
                <div className="text-lg font-semibold text-slate-900">{workspace.name}</div>
                <div className="mt-1 text-sm text-slate-500">/{workspace.slug}</div>
                <div className="mt-4 inline-flex rounded-full bg-sky-100 px-3 py-1 text-xs font-medium text-sky-800">
                  {workspace.role || 'member'}
                </div>
              </button>
            ))}

            {!isLoading && (!workspaces || workspaces.length === 0) && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 p-6 text-sm text-slate-600">
                No workspaces yet. Use the form to create the first workspace-owned agent shell.
              </div>
            )}
          </div>
        </div>
      </section>

      <aside>
        <form className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm" onSubmit={handleCreate}>
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-600">Create workspace</div>
          <h2 className="mt-3 text-2xl font-semibold text-slate-900">Start a workspace agent</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Slice 1 creates the workspace shell that later slices will fill with REST onboarding, chat, entity exploration, and QA.
          </p>

          {error && <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

          <div className="mt-6 space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="workspace-name">
                Name
              </label>
              <input
                id="workspace-name"
                className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-sky-500"
                value={name}
                onChange={(event) => handleNameChange(event.target.value)}
                placeholder="Acme Support Agent"
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="workspace-slug">
                Slug
              </label>
              <input
                id="workspace-slug"
                className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-sky-500"
                value={slug}
                onChange={(event) => setSlug(event.target.value)}
                placeholder="acme-support-agent"
                pattern="^[a-z0-9][a-z0-9\-]*$"
                required
              />
            </div>
          </div>

          <button
            className="mt-6 w-full rounded-md bg-slate-950 px-4 py-2.5 font-medium text-white hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-70"
            disabled={createWorkspace.isPending}
            type="submit"
          >
            {createWorkspace.isPending ? 'Creating workspace...' : 'Create workspace'}
          </button>
        </form>
      </aside>
    </div>
  )
}
