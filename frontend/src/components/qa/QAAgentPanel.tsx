import { RefreshCw, ShieldCheck } from 'lucide-react'

interface QAAgentPanelProps {
  onResetRuntime: () => Promise<void>
}

export function QAAgentPanel({ onResetRuntime }: QAAgentPanelProps) {
  return (
    <div className="space-y-3 text-sm" data-testid="qa-agent-panel">
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-white/10 dark:bg-white/[0.03]">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-sky-600 dark:text-sky-300" />
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-sky-600 dark:text-sky-300">UI QA agent</div>
            <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
              RouteDeck scenario definitions and evaluators are available through the QA API. The legacy entry runner is no longer mounted in the product shell.
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => { void onResetRuntime() }}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Reset graph
        </button>
      </div>
    </div>
  )
}
