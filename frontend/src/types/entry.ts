import type { ChatUIMessage } from '@/types/agent'
import type { User } from '@/types/domain'

export type AuthIntent = 'login' | 'register'
export type OperatorExperienceMode = 'entry' | 'operator'
export type OperatorSidebarItem =
  | 'chat'
  | 'learn'
  | 'setup'
  | 'signin'
  | 'register'
  | 'connect'
  | 'attachments'
  | 'sessions'
  | 'admin'
  | 'entities'
  | 'actions'
  | 'qa'

export type UnifiedOperatorMessage = ChatUIMessage & {
  source: 'entry' | 'agent' | 'system'
}

export type GatewayNode =
  | 'bootstrap'
  | 'intent'
  | 'display_name'
  | 'email'
  | 'password'
  | 'saas_agent_select'
  | 'saas_agent_job'
  | 'saas_agent_confirm'
  | 'setup_intro'
  | 'connection_confirm'
  | 'operator_ready'

export interface GatewayState {
  node: GatewayNode
  intent: AuthIntent | null
  display_name: string
  email: string
  saas_agent_name: string
  saas_agent_slug: string
  active_saas_agent_id: string | null
  active_connection_id?: string | null
  connection_draft?: Record<string, unknown>
  entry_draft?: Record<string, unknown>
  canvas_artifacts?: EntryUIArtifact[]
  platform_question_context?: Record<string, unknown>[]
  follow_up_context?: Record<string, unknown>
}

export interface EntryTurnMessage {
  role: 'assistant'
  content: string
}

export interface EntrySession {
  access_token: string
  token_type: 'bearer'
  user: User
}

export interface EntryTurnResponse {
  state: GatewayState
  session_id?: string | null
  run_id?: string | null
  graph_version?: string | null
  graph_manifest?: EntryGraphManifest | null
  messages: EntryTurnMessage[]
  session?: EntrySession | null
  available_actions?: EntryActionCard[]
  persistent_actions?: EntryActionCard[]
  ui_artifacts?: EntryUIArtifact[]
  route_deck_snapshot?: RouteDeckRuntimeSnapshot | null
  replace_path?: string | null
}

export interface EntryPersistentActionsResponse {
  persistent_actions: EntryActionCard[]
}

export interface EntryGraphManifestNode {
  id: string
  label: string
  lane: string
  parent?: string | null
  description?: string | null
  prompt_placeholder?: string | null
  allowed_actions?: string[]
  expected_input?: string | null
  recovery_prompt?: string | null
}

export interface EntryGraphManifestEdge {
  from: string
  to: string
  type: string
  condition?: string | null
  explanation?: string | null
  action_id?: string | null
}

export interface EntryGraphManifestAction {
  id: string
  label: string
  capability_id?: string | null
  description?: string | null
  emphasis?: 'primary' | 'secondary'
  kind?: EntryActionKind
  category?: 'auth' | 'setup' | 'navigation' | 'execution' | 'feedback' | 'learning' | 'deployment'
  placement?: 'next_best' | 'rail' | 'inline' | 'evidence'
  fields?: EntryActionField[]
  payload?: Record<string, unknown>
  allowed_nodes?: string[]
  visibility?: 'contextual' | 'persistent' | 'dynamic' | string
  recovery_prompt?: string | null
  sensitive?: boolean
}

export interface RouteDeckRuntimeSnapshot {
  current_node?: string | null
  reachable_nodes?: string[]
  valid_actions?: EntryActionCard[]
  blocked_actions?: { id: string; reason: string }[]
  executed_nodes?: string[]
  progress?: Record<string, unknown>
  recovery_prompts?: string[]
  diagnostics?: Record<string, unknown>
}

export interface SaaSAgentRouteDeckContext {
  saas_agent_id: string
  saas_agent_name?: string | null
  saas_agent_slug?: string | null
  current_node?: string | null
  current_label?: string | null
  working_on?: string | null
  connection_count?: number
  ready_connection_count?: number
  action_count?: number
  tool_count?: number
  latest_connection_id?: string | null
  latest_connection_name?: string | null
  latest_activation_status?: string | null
  latest_activation_step?: string | null
  blocked_reason?: string | null
  latest_execution_id?: string | null
  latest_execution_status?: string | null
  latest_execution_approval_state?: string | null
  latest_execution_tool_name?: string | null
  latest_execution_risk?: string | null
  reachable_nodes?: string[]
}

export interface SaaSAgentRouteDeckResponse {
  manifest: EntryGraphManifest
  snapshot: RouteDeckRuntimeSnapshot
  context: SaaSAgentRouteDeckContext
}

export interface EntryGraphManifest {
  version: string
  nodes: EntryGraphManifestNode[]
  edges: EntryGraphManifestEdge[]
  actions?: EntryGraphManifestAction[]
  policies?: Record<string, unknown>
  test_paths?: Record<string, unknown>[]
}

export interface StageCompletedEvent {
  output?: {
    next_node?: GatewayNode
    active_saas_agent_id?: string | null
    active_connection_id?: string | null
    replace_path?: string | null
    available_actions?: EntryActionCard[]
    persistent_actions?: EntryActionCard[]
    ui_artifacts?: EntryUIArtifact[]
    route_deck_snapshot?: RouteDeckRuntimeSnapshot
    connection_draft?: Record<string, unknown>
    entry_draft?: Record<string, unknown>
  }
}

export type EntryActionKind = 'button' | 'chip' | 'form' | 'nav' | 'summary'

export interface EntryActionField {
  key: string
  label: string
  field_type?: 'text' | 'password' | 'select' | 'url' | 'textarea'
  required?: boolean
  placeholder?: string | null
  default?: unknown
  options?: { value: string; label: string }[] | null
  help_text?: string | null
  validation_hint?: string | null
  sensitive?: boolean
}

export interface EntryActionCard {
  id: string
  label: string
  capability_id?: string | null
  description?: string | null
  emphasis?: 'primary' | 'secondary'
  kind?: EntryActionKind
  category?: 'auth' | 'setup' | 'navigation' | 'execution' | 'feedback' | 'learning' | 'deployment'
  placement?: 'next_best' | 'rail' | 'inline' | 'evidence'
  explanation?: string | null
  recovery_prompt?: string | null
  feedback_target?: string | null
  fields?: EntryActionField[]
  payload?: Record<string, unknown>
  disabled_reason?: string | null
}

export type EntryUIArtifactKind = 'widget' | 'markup'
export type EntryUIArtifactSurface = 'inline' | 'canvas' | 'both'

export interface EntryUIArtifact {
  id: string
  kind: EntryUIArtifactKind
  surface?: EntryUIArtifactSurface
  title?: string | null
  widget_type?: string | null
  payload?: Record<string, unknown>
  markup?: string | null
}

export type EntryMessageRole = ChatUIMessage['role']
