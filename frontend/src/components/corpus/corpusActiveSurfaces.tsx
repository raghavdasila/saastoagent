import type { ReactNode } from 'react'
import {
  RouteDeckSurfaceHost,
  type RouteDeckProjection,
  type RouteDeckSurface,
} from '@routedeck/react'
import {
  AlertTriangle,
  Boxes,
  FileText,
  KeyRound,
  Play,
  ShieldCheck,
} from 'lucide-react'

import { AdminPanel } from '@/components/agent/AdminPanel'
import { AttachmentsPanel } from '@/components/agent/AttachmentsPanel'
import { LearningPanel } from '@/components/agent/LearningPanel'
import { QAAgentPanel } from '@/components/qa/QAAgentPanel'
import { ActionsCanvas } from '@/components/saasAgent/ActionsCanvas'
import { EntitiesCanvas } from '@/components/saasAgent/EntitiesCanvas'
import type { CorpusContextLens, CorpusGraphState } from '@/types/corpus'
import type { SaaSAgent } from '@/types/domain'

import { corpusSurfaceComponents } from './corpusRouteDeckCatalog'
import {
  AuthSurfaceCard,
  ConnectionSetupSurface,
  Fact,
  InfoSurface,
  InstructionsSurface,
  Metric,
  SaaSAgentListSurface,
  OperationReviewSurface,
  surfaceTitle,
  contextLensFromProjection,
  type ActiveSurfaceDirtyState,
} from './corpusSurfaces'

interface SurfaceRendererProps {
  surface: RouteDeckSurface
  contextLens: CorpusContextLens | null
  graphState: CorpusGraphState | null
  projection: RouteDeckProjection
  busy: boolean
  onOperationSubmit: (operationId: string, args: Record<string, unknown>) => void
  onDirtyStateChange?: (state: ActiveSurfaceDirtyState | null) => void
}

type SurfaceComponentRenderer = (props: SurfaceRendererProps) => ReactNode

export function ActiveSurfacePanel({
  projection,
  graphState,
  busy,
  onOperationSubmit,
  onDirtyStateChange,
}: {
  projection: RouteDeckProjection
  graphState: CorpusGraphState | null
  busy: boolean
  onOperationSubmit: (operationId: string, args: Record<string, unknown>) => void
  onDirtyStateChange?: (state: ActiveSurfaceDirtyState | null) => void
}) {
  const contextLens = contextLensFromProjection(projection)

  return (
    <section className="py-4" data-testid="active-surface-panel">
      <RouteDeckSurfaceHost>
        {(activeSurface) => {
          if (!activeSurface) return null
          return (
            <div className="rounded-[0.9rem] border border-border/30 bg-card p-5 shadow-[0_26px_64px_-42px_hsl(var(--foreground)/0.65)] dark:border-white/15 dark:bg-muted dark:shadow-black/40">
              <div className="mb-4 flex items-center justify-between gap-3 pb-3">
                <div>
                  <h2 className="text-base font-semibold">{surfaceTitle(activeSurface, contextLens)}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">Opened from committed graph state.</p>
                </div>
                <span className="shrink-0 whitespace-nowrap rounded-full bg-secondary px-3 py-1 text-[11px] font-semibold text-secondary-foreground shadow-sm">
                  Active surface
                </span>
              </div>
              <SurfaceRenderer
                surface={activeSurface}
                contextLens={contextLens}
                graphState={graphState}
                projection={projection}
                busy={busy}
                onOperationSubmit={onOperationSubmit}
                onDirtyStateChange={onDirtyStateChange}
              />
            </div>
          )
        }}
      </RouteDeckSurfaceHost>
    </section>
  )
}

export function SurfaceRenderer(props: SurfaceRendererProps) {
  const renderer = activeSurfaceRenderers[props.surface.component] || DefaultSurfaceRenderer
  return <>{renderer(props)}</>
}

const activeSurfaceRenderers: Record<string, SurfaceComponentRenderer> = {
  [corpusSurfaceComponents.auth]: ({ surface }) => <AuthSurfaceCard surface={surface} />,
  [corpusSurfaceComponents.operationReview]: ({ projection, surface, busy, onOperationSubmit }) => (
    <OperationReviewSurface
      projection={projection}
      surface={surface}
      busy={busy}
      onOperationSubmit={onOperationSubmit}
    />
  ),
  [corpusSurfaceComponents.entities]: ({ graphState }) => (
    <EntitiesCanvas saasAgentId={activeSaaSAgentIdFromGraphState(graphState)} />
  ),
  [corpusSurfaceComponents.actions]: ({ graphState }) => (
    <ActionsCanvas saasAgentId={activeSaaSAgentIdFromGraphState(graphState)} />
  ),
  [corpusSurfaceComponents.knowledge]: ({ graphState }) => (
    <AttachmentsPanel saasAgentId={activeSaaSAgentIdFromGraphState(graphState)} />
  ),
  [corpusSurfaceComponents.learning]: ({ surface, graphState }) => (
    <LearningPanel
      saasAgentId={activeSaaSAgentIdFromGraphState(graphState)}
      filter={String(surface.props?.filter || 'policy_gaps')}
    />
  ),
  [corpusSurfaceComponents.learningPolicyCandidate]: ({ surface, graphState }) => (
    <LearningPanel
      saasAgentId={activeSaaSAgentIdFromGraphState(graphState)}
      candidateId={String(surface.props?.candidate_id || '')}
      readonly={Boolean(surface.props?.readonly)}
    />
  ),
  [corpusSurfaceComponents.learningExecutionTrace]: ({ surface }) => (
    <InfoSurface
      title="Execution trace"
      description="Owner-only trace review for the selected public or owner execution."
      icon={<Play className="h-5 w-5" />}
    >
      <dl className="grid gap-2 text-sm sm:grid-cols-2">
        <Fact label="Trace ID" value={String(surface.props?.trace_id || 'No trace selected')} />
        <Fact label="Visibility" value="Owner only" />
      </dl>
    </InfoSurface>
  ),
  [corpusSurfaceComponents.qa]: () => <QAAgentPanel onResetRuntime={async () => undefined} />,
  [corpusSurfaceComponents.instructions]: ({ surface, graphState, onDirtyStateChange }) => (
    <InstructionsSurface
      saasAgentId={activeSaaSAgentIdFromGraphState(graphState)}
      surfaceId={surface.surface_id || 'instructions.active'}
      onDirtyStateChange={onDirtyStateChange}
    />
  ),
  [corpusSurfaceComponents.memory]: ({ surface, graphState }) => {
    const activeSaaSAgentId = activeSaaSAgentIdFromGraphState(graphState)
    const agents = Array.isArray(surface.props?.saas_agents) ? (surface.props?.saas_agents as SaaSAgent[]) : []
    const activeAgent = agents.find((agent) => agent.id === activeSaaSAgentId)
    return <AdminPanel saasAgent={activeAgent} saasAgentId={activeSaaSAgentId} />
  },
  [corpusSurfaceComponents.schemaPreview]: ({ surface }) => {
    const preview = surface.props?.schema_preview as Record<string, unknown> | undefined
    return (
      <InfoSurface
        title="Schema preview"
        description="Review the detected API shape before activation."
        icon={<FileText className="h-5 w-5" />}
      >
        <dl className="grid gap-2 text-sm sm:grid-cols-3">
          <Fact label="Title" value={String(preview?.title || 'Pending preview')} />
          <Fact label="Version" value={String(preview?.version || 'Unknown')} />
          <Fact label="Endpoints" value={String(preview?.endpoint_count || 0)} />
        </dl>
      </InfoSurface>
    )
  },
  [corpusSurfaceComponents.catalog]: ({ surface, contextLens }) => (
    <CatalogSurface surface={surface} contextLens={contextLens} />
  ),
  [corpusSurfaceComponents.connectionSetup]: ({ projection, busy, onOperationSubmit }) => (
    <ConnectionSetupSurface projection={projection} busy={busy} onOperationSubmit={onOperationSubmit} />
  ),
  [corpusSurfaceComponents.saaSAgentList]: ({ surface }) => {
    const agents = Array.isArray(surface.props?.saas_agents) ? (surface.props?.saas_agents as SaaSAgent[]) : []
    return <SaaSAgentListSurface agents={agents} />
  },
  [corpusSurfaceComponents.execution]: () => (
    <InfoSurface
      title="Execution"
      description="Corpus will propose execution inputs or approvals when the graph requires them."
      icon={<Play className="h-5 w-5" />}
    />
  ),
  [corpusSurfaceComponents.recovery]: () => (
    <InfoSurface
      title="Recovery"
      description="This path needs a different prerequisite. Diagnostics can explain why it is blocked."
      icon={<AlertTriangle className="h-5 w-5" />}
    />
  ),
}

function DefaultSurfaceRenderer({ surface, contextLens }: SurfaceRendererProps) {
  return (
    <InfoSurface
      title={surfaceTitle(surface, contextLens)}
      description="This surface is available from the current node."
      icon={<Boxes className="h-5 w-5" />}
    />
  )
}

function CatalogSurface({
  surface,
  contextLens,
}: {
  surface: RouteDeckSurface
  contextLens: CorpusContextLens | null
}) {
  const activationEvents = Array.isArray(surface.props?.activation_events)
    ? (surface.props?.activation_events as unknown[])
    : []
  const catalog = surface.props?.catalog as Record<string, unknown> | undefined
  const routerIndex =
    (surface.props?.router_index as Record<string, unknown> | undefined) ||
    (catalog?.router_index as Record<string, unknown> | undefined) ||
    (contextLens?.router_index_status
      ? {
          status: contextLens.router_index_status,
          document_count: contextLens.router_documents_count,
          endpoint_count: contextLens.router_endpoint_count,
          router_version: contextLens.router_version,
        }
      : undefined)
  const requestReferenceCount = Number(routerIndex?.document_count || contextLens?.router_documents_count || 0)
  const requestMatchingStatus = routerIndex ? requestMatchingStatusLabel(String(routerIndex.status || 'unknown')) : null

  return (
    <InfoSurface
      title="Catalog"
      description="Activated API capabilities and generated tools appear here as they become available."
      icon={<Boxes className="h-5 w-5" />}
    >
      <div className="grid gap-3 sm:grid-cols-4">
        <Metric label="Ready APIs" value={contextLens?.ready_connection_count || 0} icon={<KeyRound className="h-4 w-4" />} />
        <Metric label="Actions" value={contextLens?.action_count || 0} icon={<Play className="h-4 w-4" />} />
        <Metric label="Tools" value={contextLens?.tool_count || 0} icon={<ShieldCheck className="h-4 w-4" />} />
        <Metric label="API references" value={requestReferenceCount} icon={<FileText className="h-4 w-4" />} />
      </div>
      {requestMatchingStatus && (
        <p className="mt-3 text-sm text-slate-500">
          Request matching: {requestMatchingStatus}
        </p>
      )}
      {activationEvents.length > 0 && (
        <p className="mt-3 text-sm text-slate-500">{activationEvents.length} activation events captured for diagnostics.</p>
      )}
    </InfoSurface>
  )
}

function activeSaaSAgentIdFromGraphState(graphState: CorpusGraphState | null) {
  return graphState?.active_saas_agent_id || null
}

function requestMatchingStatusLabel(status: string) {
  if (status === 'ready') return 'Ready'
  if (status === 'building') return 'Preparing'
  if (status === 'stale') return 'Refreshing'
  if (status === 'failed') return 'Needs attention'
  return 'Pending'
}
