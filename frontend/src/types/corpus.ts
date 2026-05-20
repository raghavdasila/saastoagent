import type { RouteDeckProjection, RouteDeckSurface } from '@routedeck/react'

import type { AppGraphState } from '@/types/appGraph'
import type { EntryTurnMessage } from '@/types/entry'

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

export interface CorpusExpectedActiveSurface {
  name: string
  component: string
  variant?: string | null
  role?: string | null
}

export interface CorpusSurfaceOpening {
  operation_id: string
  label: string
  target_node?: string | null
  expected_active_surface?: CorpusExpectedActiveSurface | null
}

export interface CorpusSurfacePrompt {
  operation_id: string
  target_node?: string | null
  expected_active_surface?: CorpusExpectedActiveSurface | null
  content: string
}

export interface CorpusActionResponse {
  state: AppGraphState
  projection: RouteDeckProjection
  active_surface?: RouteDeckSurface | null
  messages: EntryTurnMessage[]
  replace_path?: string | null
  surface_prompt?: CorpusSurfacePrompt | null
}

export interface CorpusStateResponse {
  state: AppGraphState
  projection: RouteDeckProjection
  replace_path?: string | null
}

export interface CorpusDiagnosticsSnapshot {
  graph_manifest: Record<string, unknown>
  runtime_snapshot: Record<string, unknown>
  introspection: Record<string, unknown>
  projection: RouteDeckProjection
}
