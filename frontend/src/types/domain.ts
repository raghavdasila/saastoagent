export interface User {
  id: string
  email: string
  display_name?: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
}

export interface Workspace {
  id: string
  name: string
  slug: string
  created_by: string
  created_at: string
  role?: string
}

export interface WorkspaceStats {
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
