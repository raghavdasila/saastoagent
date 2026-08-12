export interface AgentBuildView {
  readonly id: string;
  readonly agent_id: string;
  readonly build_request_id: string;
  readonly design_revision_id: string;
  readonly agent_version: number;
  readonly attempt_number: number;
  readonly status: string;
  readonly runtime_lifecycle: "stopped" | "running" | "paused" | "removed";
  readonly runtime_build_hash: string | null;
  readonly model: string | null;
  readonly model_digest: string | null;
  readonly allowed_operation_ids: readonly string[];
  readonly navgraph_hash: string | null;
  readonly compiled_navgraph: Readonly<Record<string, unknown>>;
  readonly frontend_contract: Readonly<Record<string, unknown>>;
  readonly job_id?: string | null;
  readonly failure_code: string | null;
  readonly failure_message: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface AgentBuildCollectionView {
  readonly agent_id: string;
  readonly builds: readonly AgentBuildView[];
}

export interface SandboxRunView {
  readonly id: string;
  readonly agent_id: string;
  readonly build_id: string;
  readonly runtime_session_id: string;
  readonly runtime_run_id: string;
  readonly status: string;
  readonly message: string;
  readonly awaiting: string | null;
  readonly clarification: {
    readonly question: string;
    readonly candidate_operation_ids: readonly string[];
    readonly candidate_choices: readonly {
      readonly operation_id: string;
      readonly label: string | null;
    }[];
    readonly missing_input_names: readonly string[];
  } | null;
  readonly final_response: string | null;
  readonly api_call_count: number;
  readonly events: readonly { readonly sequence: number; readonly kind: string; readonly occurred_at: string; readonly safe_data: Readonly<Record<string, unknown>> }[];
  readonly routedeck_projection: Readonly<Record<string, unknown>>;
  readonly failure_code: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface SandboxRunCollectionView {
  readonly agent_id: string;
  readonly runs: readonly SandboxRunView[];
}

export interface EvaluationCaseView {
  readonly id: string;
  readonly title: string;
  readonly message: string;
  readonly source_kind: string;
  readonly category: string;
  readonly difficulty: string;
  readonly mandatory: boolean;
  readonly expected_operation_ids: readonly string[];
  readonly current_revision: number;
  readonly removed: boolean;
  readonly runnable: boolean;
  readonly latest_status: string | null;
  readonly latest_run_attempt: EvaluationRunAttemptView | null;
}

export interface EvaluationRunAttemptView {
  readonly id: string;
  readonly status: "queued" | "running" | "succeeded" | "failed";
  readonly failure_code: string | null;
  readonly failure_message: string | null;
  readonly retry_of_attempt_id: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface EvaluationSetView {
  readonly id: string;
  readonly agent_id: string;
  readonly build_id: string;
  readonly name: string;
  readonly generation_job_id: string | null;
  readonly generation_status: "manual" | "queued" | "running" | "ready" | "failed";
  readonly generation_failure_code: string | null;
  readonly generation_failure_message: string | null;
  readonly generation_summary: Readonly<Record<string, unknown>> | null;
  readonly cases: readonly EvaluationCaseView[];
  readonly eligible: boolean | null;
  readonly eligibility_reasons: readonly string[];
  readonly created_at: string;
}

export interface EvaluationCollectionView {
  readonly agent_id: string;
  readonly evaluation_sets: readonly EvaluationSetView[];
}

export interface OperationsInteractionView {
  readonly interaction_id: string;
  readonly agent_id: string;
  readonly build_id: string;
  readonly deployment_id: string;
  readonly session_id: string;
  readonly input_summary: string;
  readonly output_summary: string;
  readonly status: string;
  readonly evaluation_case_id: string | null;
  readonly events: readonly { readonly sequence: number; readonly kind: string; readonly safe_data: Readonly<Record<string, unknown>> }[];
}

export interface OperationsCollectionView {
  readonly interactions: readonly OperationsInteractionView[];
}

export interface ChannelView {
  readonly id: string;
  readonly agent_id: string;
  readonly name: string;
  readonly slug: string;
  readonly status: string;
  readonly enabled: boolean;
  readonly active_deployment_id: string | null;
  readonly failure_code: string | null;
  readonly failure_message: string | null;
  readonly created_at: string;
}

export interface ChannelCollectionView {
  readonly agent_id: string;
  readonly channels: readonly ChannelView[];
}

export interface DeploymentView {
  readonly id: string;
  readonly agent_id: string;
  readonly channel_id: string;
  readonly build_id: string;
  readonly status: string;
  readonly bundle_hash: string;
  readonly failure_code: string | null;
  readonly failure_message: string | null;
  readonly job_id: string | null;
  readonly retry_of_deployment_id: string | null;
  readonly created_at: string;
}

export interface DeploymentCollectionView {
  readonly agent_id: string;
  readonly deployments: readonly DeploymentView[];
}
