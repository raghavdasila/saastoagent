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

export interface CreateAgentInput {
  readonly name: string;
  readonly description: string;
  readonly instructions: string;
}

export interface UpdateAgentInput extends CreateAgentInput {
  readonly agent_id: string;
  readonly expected_version: number;
}
