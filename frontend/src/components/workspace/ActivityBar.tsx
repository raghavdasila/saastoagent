import { Bot, FlaskConical, GitBranch, MessageSquareText, PlugZap } from 'lucide-react'

import { capabilityItems, useWorkspaceStore, type CapabilityStatus, type WorkspaceView } from '@/stores/workspaceStore'

const icons: Record<WorkspaceView, typeof PlugZap> = {
  connect: PlugZap,
  entities: GitBranch,
  actions: Bot,
  chat: MessageSquareText,
  qa: FlaskConical,
}

const statusClass: Record<CapabilityStatus, string> = {
  active: 'bg-emerald-500',
  ready: 'bg-sky-500',
  pending: 'bg-amber-400',
  locked: 'bg-slate-300',
}

export function ActivityBar() {
  const activeView = useWorkspaceStore((state) => state.activeView)
  const setActiveView = useWorkspaceStore((state) => state.setActiveView)

  return (
    <aside className="border-b border-slate-200 bg-white md:min-h-[calc(100vh-3.5rem)] md:w-14 md:border-b-0 md:border-r dark:border-white/10 dark:bg-[#09090b]">
      <nav className="flex items-center gap-1 overflow-x-auto px-2 py-2 md:flex-col md:px-1.5 md:py-3" aria-label="Workspace capabilities">
        {capabilityItems.map((item) => {
          const Icon = icons[item.id]
          const isActive = item.id === activeView
          const isEnabled = item.id === 'chat' || item.id === 'connect' || item.status === 'ready'
          const renderedStatus = isActive ? 'active' : item.status
          const title = isEnabled ? item.label : `${item.label} - ${item.disabledReason}`

          return (
            <button
              key={item.id}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
              className={[
                'relative flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border text-slate-500 transition dark:text-slate-400',
                isActive
                  ? 'border-slate-900 bg-slate-950 text-white dark:border-white dark:bg-white dark:text-slate-950'
                  : 'border-transparent hover:border-slate-200 hover:bg-slate-50 dark:hover:border-white/10 dark:hover:bg-white/[0.06]',
                isEnabled ? 'cursor-pointer' : 'cursor-not-allowed opacity-60',
              ].join(' ')}
              disabled={!isEnabled}
              onClick={() => setActiveView(item.id)}
              title={title}
              type="button"
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
              <span className={`absolute bottom-1 right-1 h-2 w-2 rounded-full ring-2 ring-white ${statusClass[renderedStatus]}`} />
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
