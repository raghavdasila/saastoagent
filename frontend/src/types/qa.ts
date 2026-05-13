import type { GatewayNode, RouteDeckRuntimeSnapshot, UnifiedOperatorMessage } from '@/types/entry'

export type QAVerdict = 'pass' | 'fail' | 'continue' | 'error' | 'aborted'
export type QAPhase = 'idle' | 'running' | 'evaluating' | 'done'

export type QAMilestoneActionName =
  | 'type_composer'
  | 'click_send'
  | 'click_action'
  | 'fill_action_field'
  | 'submit_action_form'
  | 'open_panel'
  | 'open_route_deck'
  | 'pan_graph'
  | 'zoom_graph'
  | 'assert_visible'
  | 'assert_node'
  | 'assert_action_enabled'
  | 'collect_evidence'
  | 'reset_test_context'

export interface QAMilestoneAction {
  action: QAMilestoneActionName
  params: Record<string, unknown>
}

export interface QAEvidenceGate {
  gate: string
  required: boolean
  params: Record<string, unknown>
}

export interface QAMilestone {
  id: string
  capability: string
  goal: string
  actions: QAMilestoneAction[]
  evidence_gates: QAEvidenceGate[]
}

export interface QAScenario {
  id: string
  name: string
  persona: string
  opening_message: string
  context: string
  pass_criteria: string
  max_turns: number
  milestones: QAMilestone[]
}

export interface QAScenarioListResponse {
  scenarios: QAScenario[]
}

export interface QAResetResponse {
  qa_run_id: string
  signup_email: string
  signup_password: string
  seeded_email: string
  seeded_password: string
  seeded_workspace_id?: string | null
  seeded_workspace_name?: string | null
}

export interface QAEvalRequest {
  scenario_id?: string | null
  milestone_id?: string | null
  evidence: Record<string, unknown>
  evidence_gates: QAEvidenceGate[]
}

export interface QAEvalResponse {
  qa_run_id: string
  verdict: 'pass' | 'fail' | 'continue' | 'error'
  confidence: number
  reasoning: string
  gates: Record<string, boolean>
  failures: string[]
}

export interface QAEvent {
  id: string
  at: string
  milestone_id?: string | null
  action?: string | null
  status: 'ok' | 'fail' | 'running' | 'skipped'
  detail: string
}

export interface QAEvaluation {
  milestone_id: string
  verdict: QAVerdict
  confidence: number
  reasoning: string
  gates: Record<string, boolean>
  failures: string[]
}

export interface QAEvidenceSnapshot {
  current_node?: GatewayNode | string | null
  route_deck_snapshot_present: boolean
  valid_action_ids: string[]
  enabled_action_ids: string[]
  messages: string[]
  assistant_messages: string[]
  visible_text: string
  console_errors: string[]
  route_deck_snapshot?: RouteDeckRuntimeSnapshot | null
}

export interface QAExportData {
  started_at: string | null
  ended_at: string | null
  scenario: QAScenario | null
  test_context: QAResetResponse | null
  events: QAEvent[]
  evaluations: QAEvaluation[]
  messages: Pick<UnifiedOperatorMessage, 'role' | 'content' | 'timestamp' | 'source'>[]
  summary: {
    verdict: QAVerdict
    reasoning: string
  } | null
}
