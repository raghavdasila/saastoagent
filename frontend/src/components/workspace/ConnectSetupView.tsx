import { ArrowRight, MessageSquareText, PlugZap, Sparkles } from 'lucide-react'

import { formatWorkspaceDisplayName } from '@/lib/entryGraph'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import type { Workspace, WorkspaceStats } from '@/types/domain'

interface ConnectSetupViewProps {
  workspace?: Workspace
  stats?: WorkspaceStats
}

export function ConnectSetupView({ workspace, stats }: ConnectSetupViewProps) {
  const setActiveView = useWorkspaceStore((state) => state.setActiveView)
  const workspaceName = formatWorkspaceDisplayName(workspace?.name) || 'This workspace'
  const connectionCount = stats?.connections_count ?? 0

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 px-4 py-6 dark:bg-background sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="surface-card rounded-lg p-6 sm:p-8">
          <div className="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">
            <span>Operator setup</span>
            <span className="rounded-full bg-slate-100 px-2 py-1 tracking-normal text-slate-600 dark:bg-white/[0.06] dark:text-slate-400">{connectionCount} connected APIs</span>
          </div>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
            Connect the first API this operator will use
          </h1>
          <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600 dark:text-slate-400">
            {workspaceName} should be configured around the SaaS work you want done, not around generic admin steps. Choose the product this operator should run, then activate its REST surface so the thread can move from intent to action.
          </p>
          <button
            className="surface-solid-button mt-6 inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium"
            onClick={() => setActiveView('chat')}
            type="button"
          >
            Back to operator chat
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <div className="surface-card rounded-lg p-5">
            <PlugZap className="h-5 w-5 text-sky-600" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold text-slate-950 dark:text-white">1. Choose the product</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
              Start with the SaaS product this workspace should actually operate. The operator needs a real API surface before it can plan or act.
            </p>
          </div>
          <div className="surface-card rounded-lg p-5">
            <Sparkles className="h-5 w-5 text-sky-600" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold text-slate-950 dark:text-white">2. Activate the catalog</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
              This slice is supposed to ingest the OpenAPI source, generate actions, and infer the first useful entities without sending you into a graph debugger.
            </p>
          </div>
          <div className="surface-card rounded-lg p-5">
            <MessageSquareText className="h-5 w-5 text-sky-600" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold text-slate-950 dark:text-white">3. Direct through chat</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
              Once connected, the main surface becomes a goal-driven operator console where the system chooses actions, executes safely, and shows its trace in context.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
