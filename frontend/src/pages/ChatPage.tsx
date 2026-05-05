import { useWorkspace } from '@/context/WorkspaceContext'

export function ChatPage() {
  const { workspaceId } = useWorkspace()

  return (
    <div className="mx-auto max-w-4xl rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-600">Chat shell placeholder</div>
      <h1 className="mt-3 text-3xl font-semibold text-slate-900">Chat route reserved for later slices</h1>
      <p className="mt-3 text-base leading-7 text-slate-600">
        This route exists now so the workspace shell stays stable. Workspace <span className="font-medium text-slate-900">{workspaceId}</span> will gain retrieval chat in Slice 4 and agentic execution in Slice 5.
      </p>
    </div>
  )
}
