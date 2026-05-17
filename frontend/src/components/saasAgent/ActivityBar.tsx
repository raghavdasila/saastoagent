import { Bot, Brain, FlaskConical, GitBranch, MessageSquareText, Paperclip, PlugZap, Shield } from 'lucide-react'

import { PRODUCT_NAME } from '@/lib/entryGraph'
import { capabilityItems, useSaaSAgentStore, type CapabilityStatus, type SaaSAgentView } from '@/stores/saasAgentStore'

const icons: Record<SaaSAgentView, typeof PlugZap> = {
  connect: PlugZap,
  entities: GitBranch,
  actions: Bot,
  chat: MessageSquareText,
  attachments: Paperclip,
  admin: Shield,
  learn: Brain,
  qa: FlaskConical,
}

const statusClass: Record<CapabilityStatus, string> = {
  active: 'bg-emerald-500',
  ready: 'bg-sky-500',
  pending: 'bg-amber-400',
  locked: 'bg-slate-300',
}

export function ActivityBar() {
  const activeView = useSaaSAgentStore((state) => state.activeView)
  const setActiveView = useSaaSAgentStore((state) => state.setActiveView)

  return (
    <aside className="border-b border-slate-200 bg-white md:min-h-[calc(100vh-3.5rem)] md:w-72 md:shrink-0 md:border-b-0 md:border-r dark:border-white/10 dark:bg-[#09090b]">
      <div className="hidden border-b border-slate-200 px-4 py-4 md:block dark:border-white/10">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">SaaSAgent navigation</div>
        <div className="mt-2 text-sm font-semibold text-slate-950 dark:text-white">{PRODUCT_NAME}</div>
        <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
          Use the live operator surfaces first. Locked capabilities stay visible until the runtime is wired.
        </p>
      </div>

      <nav className="flex gap-2 overflow-x-auto px-2 py-2 md:flex-col md:gap-1.5 md:px-3 md:py-4" aria-label="SaaSAgent navigation">
        {capabilityItems.map((item) => {
          const Icon = icons[item.id]
          const isActive = item.id === activeView
          const isEnabled = item.id === 'chat' || item.id === 'connect' || item.id === 'attachments' || item.id === 'admin' || item.status === 'ready'
          const renderedStatus = isActive ? 'active' : item.status
          const title = isEnabled ? item.label : `${item.label} - ${item.disabledReason}`

          return (
            <button
              key={item.id}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
              className={[
                'flex min-w-[11rem] shrink-0 items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition md:min-w-0',
                isActive
                  ? 'border-slate-900 bg-slate-950 text-white shadow-sm dark:border-white dark:bg-white dark:text-slate-950'
                  : 'border-transparent text-slate-600 hover:border-slate-200 hover:bg-slate-50 dark:text-slate-400 dark:hover:border-white/10 dark:hover:bg-white/[0.06]',
                isEnabled ? 'cursor-pointer' : 'cursor-not-allowed opacity-60',
              ].join(' ')}
              disabled={!isEnabled}
              onClick={() => setActiveView(item.id)}
              title={title}
              type="button"
            >
              <span
                className={[
                  'flex h-10 w-10 items-center justify-center rounded-lg',
                  isActive
                    ? 'bg-white/10 text-white dark:bg-slate-950/10 dark:text-slate-950'
                    : 'bg-slate-100 text-slate-700 dark:bg-white/[0.06] dark:text-slate-300',
                ].join(' ')}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>

              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium">{item.label}</span>
                <span
                  className={[
                    'mt-0.5 block truncate text-xs',
                    isActive ? 'text-white/70 dark:text-slate-700' : 'text-slate-500 dark:text-slate-400',
                  ].join(' ')}
                >
                  {isEnabled ? item.slice : item.disabledReason}
                </span>
              </span>

              <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${statusClass[renderedStatus]}`} />
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
