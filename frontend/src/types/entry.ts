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
  | 'intent'
  | 'display_name'
  | 'email'
  | 'password'
  | 'workspace_select'
  | 'workspace_job'
  | 'workspace_confirm'
  | 'setup_intro'
  | 'connection_confirm'
  | 'operator_ready'

export interface GatewayState {
  node: GatewayNode
  intent: AuthIntent | null
  display_name: string
  email: string
  workspace_name: string
  workspace_slug: string
  active_workspace_id: string | null
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
  messages: EntryTurnMessage[]
  session?: EntrySession | null
  available_actions?: EntryActionCard[]
  persistent_actions?: EntryActionCard[]
  ui_artifacts?: EntryUIArtifact[]
  replace_path?: string | null
}

export interface EntryPersistentActionsResponse {
  persistent_actions: EntryActionCard[]
}

export interface StageCompletedEvent {
  output?: {
    next_node?: GatewayNode
    active_workspace_id?: string | null
    active_connection_id?: string | null
    replace_path?: string | null
    available_actions?: EntryActionCard[]
    persistent_actions?: EntryActionCard[]
    ui_artifacts?: EntryUIArtifact[]
    connection_draft?: Record<string, unknown>
    entry_draft?: Record<string, unknown>
  }
}

export type EntryActionKind = 'button' | 'chip' | 'form' | 'nav' | 'summary'

export interface EntryActionField {
  key: string
  label: string
  field_type?: 'text' | 'password' | 'select' | 'url'
  required?: boolean
  placeholder?: string | null
  default?: unknown
  options?: { value: string; label: string }[] | null
  help_text?: string | null
}

export interface EntryActionCard {
  id: string
  label: string
  description?: string | null
  emphasis?: 'primary' | 'secondary'
  kind?: EntryActionKind
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
