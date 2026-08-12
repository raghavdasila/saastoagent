export type AgentLifecycle = "active" | "archived";

export interface AgentView {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly instructions: string;
  readonly lifecycle: AgentLifecycle;
  readonly current_version: number;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface AgentListView {
  readonly agents: readonly AgentView[];
}

export interface AgentSourceAttachmentView {
  readonly source_id: string;
  readonly source_revision_id: string;
  readonly display_name: string;
  readonly attached_at: string;
}

export interface AgentSourceAttachmentListView {
  readonly attachments: readonly AgentSourceAttachmentView[];
}

export interface AgentDependencySourceView {
  readonly source_id: string;
  readonly source_revision_id: string;
}

export interface AgentDependencyView {
  readonly agent_id: string;
  readonly source_attachments: readonly AgentDependencySourceView[];
  readonly build_ids: readonly string[];
  readonly blocks_delete: boolean;
}

export interface AgentBuildSourceReferenceView {
  readonly source_id: string;
  readonly source_revision_id: string;
  readonly display_name: string | null;
  readonly available: boolean;
}

export interface AgentBuildLineageView {
  readonly build_id: string;
  readonly agent_id: string;
  readonly agent_version: number;
  readonly created_at: string;
  readonly source_references: readonly AgentBuildSourceReferenceView[];
}

export interface AgentBuildLineageListView {
  readonly builds: readonly AgentBuildLineageView[];
}

export interface AgentProductOverviewView {
  readonly agent_id: string;
  readonly agent_version: number;
  readonly source_count: number;
  readonly design_status: "missing" | "draft" | "accepted";
  readonly design_revision: number | null;
  readonly build_status: string | null;
  readonly build_runtime_lifecycle: string | null;
  readonly evaluation_status: string | null;
  readonly evaluation_case_count: number;
  readonly evaluation_eligible: boolean | null;
  readonly delivery_status: "none" | "channel_only" | "deploying" | "live" | "disabled" | "failed";
  readonly hosted_path: string | null;
  readonly operations_count: number;
  readonly next_step: string;
}

export interface CreateAgentInput {
  readonly name: string;
  readonly description: string;
  readonly instructions: string;
}

export interface UpdateAgentInput extends CreateAgentInput {
  readonly agent_id: string;
  readonly expected_version: number;
}
