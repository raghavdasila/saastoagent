import { useWorkspace } from '@/context/WorkspaceContext'

export function ConnectionsPage() {
  const { workspaceId } = useWorkspace()

  return (
    <div className="mx-auto max-w-4xl rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-600">Slice 2 placeholder</div>
      <h1 className="mt-3 text-3xl font-semibold text-slate-900">Connections will land here</h1>
      <p className="mt-3 text-base leading-7 text-slate-600">
        Workspace <span className="font-medium text-slate-900">{workspaceId}</span> already owns the agent boundary. The next slice attaches REST onboarding, activation, and generated action catalog to this route.
      </p>
    </div>
  )
}
