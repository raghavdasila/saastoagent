// Agent runtime types, mirrored from backend SSE protocol.

export interface ToolCallState {
  callId: string
  toolName: string
  inputs: Record<string, unknown>
  output?: string
  isRunning: boolean
}

export interface SourceCitation {
  title: string
  chunk: string
  score: number
  documentId: string
}

export interface ChatUIMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  source?: 'entry' | 'agent' | 'system'
  thinking?: string
  toolCalls?: ToolCallState[]
  sources?: SourceCitation[]
  followUps?: string[]
  metadata?: Record<string, unknown> | null
  isStreaming?: boolean
}

export type SSEEventType =
  | 'stream_start'
  | 'agent_start'
  | 'message_delta'
  | 'thinking_delta'
  | 'tool_start'
  | 'tool_end'
  | 'follow_ups'
  | 'source_citations'
  | 'debug_timing'
  | 'agent_end'
  | 'stream_end'
  | 'error'

export interface AgentSession {
  id: string
  saas_agent_id: string
  user_id?: string | null
  title: string | null
  created_at: string
  updated_at: string
  message_count: number
}

export interface AgentMessageRow {
  id: string
  session_id: string
  role: string
  content: string
  tool_calls?: unknown
  thinking?: string | null
  sources?: Array<Record<string, unknown>> | null
  follow_ups?: string[] | null
  metadata?: Record<string, unknown> | null
  created_at: string
}

export interface AgentDocument {
  id: string
  saas_agent_id: string
  filename: string
  original_name: string
  content_type: string
  size_bytes: number
  chunk_count: number
  created_at: string
}

export interface AgentDocumentChunk {
  id: string
  document_id: string
  chunk_index: number
  content: string
  has_embedding: boolean
}

export interface AgentMemoryRow {
  id: string
  saas_agent_id: string
  session_id: string | null
  content: string
  category: string
  created_at: string
}

export interface AgentLearningCandidate {
  id: string
  saas_agent_id: string
  source_trace_id?: string | null
  trigger_type: string
  status: string
  title: string
  summary: string
  hint_text: string
  target_tool_name?: string | null
  target_action_path?: string | null
  target_risk_level?: string | null
  evidence?: Record<string, unknown> | null
  created_at: string
  reviewed_at?: string | null
}

export interface AgentHandoffContext {
  entry_session_id?: string | null
  saas_agent_id?: string | null
  saas_agent_name?: string | null
  entry_draft?: Record<string, unknown>
  connection_draft?: Record<string, unknown>
  active_connection_id?: string | null
  recent_entry_messages?: string[]
}

export interface AgentAdminStats {
  total_sessions: number
  total_messages: number
  total_documents: number
  total_memories: number
}
