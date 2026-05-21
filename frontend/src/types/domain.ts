export interface User {
  id: string
  email: string
  display_name?: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
}

export interface SaaSAgent {
  id: string
  name: string
  slug: string
  created_by: string
  created_at: string
  role?: string
}

export interface SaaSAgentStats {
  connections_count: number
  tools_count: number
  learnings_count: number
  active_learnings_count: number
  systems_count: number
  connections_with_learnings: number
  tools_with_learnings: number
  avg_confidence: number
  maturity: number
}

export interface AuthTokens {
  access_token: string
  token_type: string
}

export interface DeployedAgentProfile {
  saas_agent_id: string
  slug: string
  name: string
  enabled: boolean
  auth_required: boolean
  visitor_auth_mode: 'inherit_from_connection' | 'anonymous' | 'login_required'
  execution_mode: 'sandbox' | 'live'
  default_write_policy: 'confirm' | 'owner_approval' | 'block'
  welcome_message: string
}

export interface SaaSAgentDeployment {
  id: string
  saas_agent_id: string
  enabled: boolean
  visitor_auth_mode: 'inherit_from_connection' | 'anonymous' | 'login_required'
  execution_mode: 'sandbox' | 'live'
  default_write_policy: 'confirm' | 'owner_approval' | 'block'
  welcome_message: string
  created_at: string
  updated_at: string
}

export interface ConnectionRead {
  id: string
  saas_agent_id: string
  name: string
  type: string
  provider: string
  config: Record<string, unknown>
  auth_type?: string | null
  has_credentials: boolean
  action_nodes_count: number
  tools_count: number
  activation_status?: string | null
  activation_steps?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ConnectionPreview {
  title: string
  version?: string | null
  servers: string[]
  endpoint_count: number
  methods: Record<string, number>
  tags: Record<string, number>
  sample_actions: Array<Record<string, unknown>>
  warnings: string[]
}

export interface ActionNodeRead {
  id: string
  connection_id: string
  saas_agent_id: string
  name: string
  path: string
  method: string
  description?: string | null
  risk_level: string
  status: string
  tags: unknown[]
  source_type?: string | null
  created_at: string
  updated_at: string
}

export interface GeneratedToolRead {
  id: string
  action_node_id: string
  connection_id: string
  saas_agent_id: string
  name: string
  description?: string | null
  function_schema: Record<string, unknown>
  risk_level: string
  status: string
  requires_approval: boolean
  created_at: string
  updated_at: string
}

export interface EntityRead {
  id: string
  label: string
  description: string
  action_count: number
  read_count: number
  write_count: number
  risky_count: number
  sample_paths: string[]
}

export interface ActionCatalogRead {
  actions: ActionNodeRead[]
  tools: GeneratedToolRead[]
  entities: EntityRead[]
  totals: Record<string, number>
}
