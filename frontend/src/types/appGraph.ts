import type {
  EntryActionCard,
  EntryGraphManifest,
  EntryTurnMessage,
  EntryUIArtifact,
  RouteDeckRuntimeSnapshot,
} from '@/types/entry'
import type { SaaSAgent } from '@/types/domain'

export interface AppGraphState {
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

export interface AppGraphContextLens {
  selected_saas_agent_id?: string | null
  selected_saas_agent_name?: string | null
  selected_saas_agent_slug?: string | null
  current_node: string
  working_on: string
  connection_count: number
  ready_connection_count: number
  action_count: number
  tool_count: number
  pending_trace_id?: string | null
  pending_trace_status?: string | null
}

export interface AppGraphResponse {
  state: AppGraphState
  graph_version: string
  graph_manifest: EntryGraphManifest
  route_deck_snapshot: RouteDeckRuntimeSnapshot
  context_lens: AppGraphContextLens
  available_actions: EntryActionCard[]
  persistent_actions: EntryActionCard[]
  ui_artifacts: EntryUIArtifact[]
  evidence: Record<string, unknown>[]
  diagnostics: Record<string, unknown>
  messages: EntryTurnMessage[]
  saas_agents: SaaSAgent[]
  replace_path?: string | null
}
