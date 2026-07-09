import type { RouteDeckProjection, RouteDeckRuntimeSnapshot, RouteDeckSurface } from '@routedeck/react'

import type {
  EntryActionCard,
  EntryGraphManifest,
  EntryTurnMessage,
  EntryUIArtifact,
} from '@/types/entry'
import type { SaaSAgent } from '@/types/domain'

export interface CorpusGraphState {
  node: string
  active_saas_agent_id?: string | null
  active_connection_id?: string | null
  pending_trace_id?: string | null
  active_surface_id?: string | null
  route_params?: Record<string, unknown>
  navigation_back_stack?: Array<{
    node_id: string
    surface_id?: string | null
    params?: Record<string, unknown>
  }>
  navigation_forward_stack?: Array<{
    node_id: string
    surface_id?: string | null
    params?: Record<string, unknown>
  }>
  pending_operation_id?: string | null
  pending_operation_args?: Record<string, unknown>
  graph_context?: Record<string, unknown>
  executed_nodes?: string[]
}

export interface CorpusContextLens {
  selected_saas_agent_id?: string | null
  selected_saas_agent_name?: string | null
  selected_saas_agent_slug?: string | null
  current_node: string
  working_on: string
  active_surface_id?: string | null
  route_params?: Record<string, unknown>
  legal_operation_ids?: string[]
  connection_count: number
  ready_connection_count: number
  action_count: number
  tool_count: number
  router_index_status?: string | null
  router_documents_count: number
  router_endpoint_count: number
  router_version?: string | null
  pending_trace_id?: string | null
  pending_trace_status?: string | null
}

export interface CorpusGraphResponse {
  state: CorpusGraphState
  graph_version: string
  graph_manifest: EntryGraphManifest
  route_deck_snapshot: RouteDeckRuntimeSnapshot
  context_lens: CorpusContextLens
  available_actions: EntryActionCard[]
  persistent_actions: EntryActionCard[]
  ui_artifacts: EntryUIArtifact[]
  evidence: Record<string, unknown>[]
  diagnostics: Record<string, unknown>
  messages: EntryTurnMessage[]
  saas_agents: SaaSAgent[]
  replace_path?: string | null
}

export interface CorpusProposal {
  operation_id: string
  label: string
  description?: string | null
  args: Record<string, unknown>
  execution_mode: 'auto' | 'review' | 'blocked'
  safety_class?: string | null
  input_schema?: Record<string, unknown>
  target_node?: string | null
}

export interface CorpusActionResponse {
  state: CorpusGraphState
  projection: RouteDeckProjection
  active_surface?: RouteDeckSurface | null
  messages: EntryTurnMessage[]
  replace_path?: string | null
}

export interface CorpusStateResponse {
  state: CorpusGraphState
  projection: RouteDeckProjection
  replace_path?: string | null
}

export interface CorpusDiagnosticsSnapshot {
  graph_manifest: Record<string, unknown>
  runtime_snapshot: Record<string, unknown>
  introspection: Record<string, unknown>
  projection: RouteDeckProjection
}
