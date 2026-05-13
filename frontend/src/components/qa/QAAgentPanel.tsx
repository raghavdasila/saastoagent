import { AlertTriangle, CheckCircle2, Download, Play, RefreshCw, Square, XCircle } from 'lucide-react'

import { useSaaStoAgentQA } from '@/hooks/useSaaStoAgentQA'
import { cn } from '@/lib/cn'

interface QAAgentPanelProps {
  onResetRuntime: () => Promise<void>
}

function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function QAAgentPanel({ onResetRuntime }: QAAgentPanelProps) {
  const qa = useSaaStoAgentQA({ onResetRuntime })
  const running = qa.phase === 'running' || qa.phase === 'evaluating'

  return (
    <div className="space-y-3 text-sm" data-testid="qa-agent-panel">
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-white/10 dark:bg-white/[0.03]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-sky-600 dark:text-sky-300">UI QA agent</div>
            <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
              Drives the visible SaaStoAgent UI and scores behavior from RouteDeck and rendered evidence.
            </p>
          </div>
          <span className={cn(
            'rounded-full border px-2 py-1 text-[11px] font-semibold capitalize',
            qa.summary?.verdict === 'pass'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200'
              : qa.summary?.verdict === 'fail' || qa.summary?.verdict === 'error'
                ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200'
                : 'border-slate-200 bg-white text-slate-500 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300',
          )}>
            {qa.summary?.verdict || qa.phase}
          </span>
        </div>
      </div>

      {qa.loadError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
          {qa.loadError}
        </div>
      )}

      <label className="block space-y-1 text-xs font-medium text-slate-600 dark:text-slate-300">
        <span>Scenario</span>
        <select
          value={qa.selectedScenarioId ?? ''}
          onChange={(event) => qa.setSelectedScenarioId(event.target.value)}
          disabled={running}
          className="h-9 w-full rounded-md border border-slate-200 bg-white px-2 text-sm text-slate-950 outline-none focus:border-sky-400 disabled:opacity-60 dark:border-white/10 dark:bg-[#050506] dark:text-white"
          data-testid="qa-scenario-select"
        >
          {qa.scenarios.map((scenario) => (
            <option key={scenario.id} value={scenario.id}>
              {scenario.name}
            </option>
          ))}
        </select>
      </label>

      {qa.selectedScenario && (
        <div className="rounded-lg border border-slate-200 p-3 text-xs leading-5 text-slate-500 dark:border-white/10 dark:text-slate-400">
          <div className="font-semibold text-slate-800 dark:text-slate-100">{qa.selectedScenario.persona}</div>
          <p className="mt-1">{qa.selectedScenario.pass_criteria}</p>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => { void qa.runScenario() }}
          disabled={running || !qa.selectedScenario}
          className="inline-flex items-center gap-2 rounded-full border border-sky-300 bg-sky-50 px-3 py-1.5 text-xs font-semibold text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-300"
          data-testid="qa-run-scenario"
        >
          <Play className="h-3.5 w-3.5" />
          Run
        </button>
        <button
          type="button"
          onClick={() => { void qa.resetTestContext() }}
          disabled={running}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Reset
        </button>
        <button
          type="button"
          onClick={qa.abort}
          disabled={!running}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
        >
          <Square className="h-3.5 w-3.5" />
          Stop
        </button>
      </div>

      {qa.testContext && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs dark:border-white/10 dark:bg-white/[0.03]">
          <div className="font-semibold text-slate-800 dark:text-slate-100">Seed context</div>
          <dl className="mt-2 space-y-1 text-slate-500 dark:text-slate-400">
            <div><dt className="inline font-medium">Signup email:</dt> <dd className="inline break-all">{qa.testContext.signup_email}</dd></div>
            <div><dt className="inline font-medium">Seeded signin:</dt> <dd className="inline break-all">{qa.testContext.seeded_email}</dd></div>
            <div><dt className="inline font-medium">Password:</dt> <dd className="inline">{qa.testContext.signup_password}</dd></div>
          </dl>
        </div>
      )}

      {qa.summary && (
        <div className={cn(
          'flex gap-2 rounded-lg border p-3 text-xs',
          qa.summary.verdict === 'pass'
            ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200'
            : 'border-red-200 bg-red-50 text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200',
        )}>
          {qa.summary.verdict === 'pass' ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <XCircle className="h-4 w-4 shrink-0" />}
          <span>{qa.summary.reasoning}</span>
        </div>
      )}

      <div className="space-y-2">
        <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Run log</div>
        <div className="max-h-64 space-y-2 overflow-y-auto rounded-lg border border-slate-200 p-2 dark:border-white/10">
          {qa.events.length === 0 ? (
            <p className="p-2 text-xs text-slate-500 dark:text-slate-400">No QA run yet.</p>
          ) : (
            qa.events.map((event) => (
              <div key={event.id} className="rounded-md bg-slate-50 px-2 py-1.5 text-xs dark:bg-white/[0.03]">
                <div className="flex items-center justify-between gap-2">
                  <span className={cn(
                    'font-semibold capitalize',
                    event.status === 'fail' ? 'text-red-600 dark:text-red-300' : event.status === 'running' ? 'text-sky-600 dark:text-sky-300' : 'text-slate-700 dark:text-slate-200',
                  )}>
                    {event.status}
                  </span>
                  <span className="text-[10px] text-slate-400">{new Date(event.at).toLocaleTimeString()}</span>
                </div>
                <p className="mt-1 leading-5 text-slate-500 dark:text-slate-400">{event.detail}</p>
              </div>
            ))
          )}
        </div>
      </div>

      {qa.consoleErrors.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200">
          <div className="flex items-center gap-2 font-semibold"><AlertTriangle className="h-4 w-4" /> Console errors captured</div>
          <ul className="mt-2 list-disc space-y-1 pl-4">
            {qa.consoleErrors.slice(-3).map((error, index) => <li key={`${error}-${index}`}>{error}</li>)}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => downloadText('saastoagent-qa-replay.json', qa.exportJson(), 'application/json')}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
        >
          <Download className="h-3.5 w-3.5" />
          JSON
        </button>
        <button
          type="button"
          onClick={() => downloadText('saastoagent-qa-replay.yaml', qa.exportYaml(), 'text/yaml')}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
        >
          <Download className="h-3.5 w-3.5" />
          YAML
        </button>
      </div>
    </div>
  )
}
