import { useState, type ReactNode } from 'react'
import {
  useRouteDeckProjection,
  useRouteDeckStore,
  useRouteDeckSurface,
  type RouteDeckProjection,
  type RouteDeckSurface,
} from '@routedeck/react'
import { Sparkles } from 'lucide-react'

import { useSaaSAgentUiStore } from '@/stores/saasAgentUiStore'
import type { AppGraphContextLens } from '@/types/appGraph'
import type { SaaSAgent } from '@/types/domain'

import { graphStateFromRouteDeckState } from './corpusRouteDeckClient'
import { corpusOperationIds, corpusSurfaceComponents } from './corpusRouteDeckCatalog'
import { contextLensFromProjection } from './corpusSurfaces'
import { displayWork } from './workbenchDisplay'

interface FrameSurfaceRendererProps {
  surface: RouteDeckSurface
  projection: RouteDeckProjection
  contextLens: AppGraphContextLens | null
  openingAgentId: string | null
  onOpenSaaSAgent: (agent: SaaSAgent) => void
  onListSaaSAgents: () => void
}

type FrameSurfaceRenderer = (props: FrameSurfaceRendererProps) => ReactNode

const frameSurfaceRenderers: Record<string, FrameSurfaceRenderer> = {
  [corpusSurfaceComponents.lounge]: ({ surface }) => (
    <div className="md3-surface-low p-5">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <Sparkles className="h-4 w-4 text-primary" />
        {String(surface.props?.title || 'Explore SaaStoAgent')}
      </div>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">
        {String(
          surface.props?.subtitle ||
            'Ask about the platform, then let Corpus guide you into the next graph node when needed.',
        )}
      </p>
    </div>
  ),
  [corpusSurfaceComponents.dashboard]: ({
    surface,
    openingAgentId,
    onOpenSaaSAgent,
    onListSaaSAgents,
  }) => {
    const saasAgents = Array.isArray(surface.props?.saas_agents)
      ? (surface.props?.saas_agents as SaaSAgent[])
      : []
    const agentCount = Number(surface.props?.agent_count ?? saasAgents.length)

    return (
      <div className="relative overflow-hidden rounded-[0.9rem] border border-border/20 bg-gradient-to-br from-card via-muted/75 to-card p-5 shadow-[0_22px_52px_-42px_hsl(var(--foreground)/0.68)] dark:border-white/10 dark:from-muted/80 dark:via-card dark:to-muted/50">
        <div className="pointer-events-none absolute -right-16 -top-24 h-56 w-56 rounded-full bg-secondary/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-28 left-1/4 h-52 w-52 rounded-full bg-primary/10 blur-3xl" />
        <div className="flex items-start justify-between gap-4">
          <div className="relative min-w-0">
            <div className="text-sm font-semibold">Dashboard</div>
            <p className="mt-2 text-sm text-muted-foreground">
              Corpus stays in the center. The dashboard remains contextual until you ask to open or create an agent.
            </p>
          </div>
          <div className="relative shrink-0 whitespace-nowrap rounded-full bg-secondary px-3 py-1 text-[11px] font-semibold text-secondary-foreground shadow-[0_12px_26px_-18px_hsl(var(--secondary)/0.9)]">
            {agentCount} agents
          </div>
        </div>
        {saasAgents.length > 0 && (
          <div className="relative mt-4 grid gap-2 sm:grid-cols-2">
            {saasAgents.slice(0, 2).map((agent) => (
              <button
                key={agent.id}
                type="button"
                onClick={() => onOpenSaaSAgent(agent)}
                disabled={openingAgentId === agent.id}
                className="rounded-[0.75rem] border border-border/20 bg-card/90 p-3 text-left text-sm shadow-[0_16px_32px_-28px_hsl(var(--foreground)/0.55)] transition hover:border-primary/35 hover:bg-primary/5 disabled:opacity-60 dark:border-white/10 dark:bg-background/30"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0 font-semibold">{agent.name}</div>
                  <span className="rounded-full bg-secondary/10 px-2 py-0.5 text-[11px] font-semibold text-secondary">
                    {openingAgentId === agent.id ? 'Opening' : 'Open'}
                  </span>
                </div>
                <div className="mt-1 text-xs text-muted-foreground">Configure API or continue setup</div>
              </button>
            ))}
          </div>
        )}
        <div className="relative mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onListSaaSAgents}
            className="rounded-full border border-border/30 bg-card px-3 py-1.5 text-xs font-semibold text-foreground shadow-sm transition hover:border-primary/35 hover:bg-primary/5"
          >
            List agents
          </button>
        </div>
      </div>
    )
  },
}

export function FrameSurfacePanel() {
  const projection = useRouteDeckProjection()
  const routeDeckStore = useRouteDeckStore()
  const surface = useRouteDeckSurface('main')
  const contextLens = contextLensFromProjection(projection)
  const setMirroredSaaSAgentId = useSaaSAgentUiStore((state) => state.setMirroredSaaSAgentId)
  const [openingAgentId, setOpeningAgentId] = useState<string | null>(null)
  if (!surface) return null

  const onOpenSaaSAgent = async (agent: SaaSAgent) => {
    setOpeningAgentId(agent.id)
    try {
      const response = await routeDeckStore.dispatch({
        operation_id: corpusOperationIds.openSaaSAgent,
        args: { saas_agent_id: agent.id },
      })
      const nextGraphState = graphStateFromRouteDeckState(response.state)
      setMirroredSaaSAgentId(nextGraphState?.active_saas_agent_id || agent.id)
    } finally {
      setOpeningAgentId(null)
    }
  }

  const onListSaaSAgents = async () => {
    await routeDeckStore.dispatch({
      operation_id: corpusOperationIds.listSaaSAgents,
      args: {},
    })
  }

  const renderer = frameSurfaceRenderers[surface.component] || DefaultFrameSurface
  return (
    <>
      {renderer({
        surface,
        projection,
        contextLens,
        openingAgentId,
        onOpenSaaSAgent: (agent) => void onOpenSaaSAgent(agent),
        onListSaaSAgents: () => void onListSaaSAgents(),
      })}
    </>
  )
}

function DefaultFrameSurface({ surface, projection, contextLens }: FrameSurfaceRendererProps) {
  return (
    <div className="md3-surface-low p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-semibold">
          {String(surface.props?.title || contextLens?.working_on || displayWork(projection.graph_node))}
        </div>
        <span className="shrink-0 whitespace-nowrap rounded-full bg-secondary px-3 py-1 text-[11px] font-semibold text-secondary-foreground shadow-sm">
          Current node
        </span>
      </div>
      <div className="mt-2 text-sm text-muted-foreground">
        {contextLens?.selected_saas_agent_name
          ? `Focused on ${contextLens.selected_saas_agent_name}.`
          : 'Context is graph-owned and can change when Corpus commits the next legal operation.'}
      </div>
    </div>
  )
}
