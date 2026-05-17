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

export interface AppGraphSurface {
  id: string
  renderer: string
  title: string
  payload: Record<string, unknown>
}

export interface AppGraphResponse {
  state: AppGraphState
  graph_version: string
  graph_manifest: EntryGraphManifest
  route_deck_snapshot: RouteDeckRuntimeSnapshot
  context_lens: AppGraphContextLens
  active_surface: AppGraphSurface
  available_actions: EntryActionCard[]
  persistent_actions: EntryActionCard[]
  ui_artifacts: EntryUIArtifact[]
  evidence: Record<string, unknown>[]
  diagnostics: Record<string, unknown>
  messages: EntryTurnMessage[]
  saas_agents: SaaSAgent[]
  replace_path?: string | null
}
