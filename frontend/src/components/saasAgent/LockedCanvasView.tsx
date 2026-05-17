import { capabilityItems, type SaaSAgentView } from '@/stores/saasAgentStore'

interface LockedCanvasViewProps {
  view: SaaSAgentView
}

export function LockedCanvasView({ view }: LockedCanvasViewProps) {
  const capability = capabilityItems.find((item) => item.id === view)

  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center px-4 py-10">
      <section className="surface-card w-full max-w-xl rounded-lg p-8 text-center">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-500">
          {capability?.slice || 'Future slice'}
        </div>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
          {capability?.label || 'Capability'} is not active yet
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-400">
          {capability?.disabledReason || 'This saasAgent capability will be enabled in a later slice.'}
        </p>
      </section>
    </div>
  )
}
