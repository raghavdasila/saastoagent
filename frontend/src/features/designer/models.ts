export interface DesignContent {
  readonly goal: string;
  readonly instructions: string;
  readonly features: readonly string[];
  readonly behaviors: readonly string[];
  readonly policies: readonly string[];
  readonly capabilities: readonly string[];
  readonly tools: readonly string[];
}

export interface DesignTopology {
  readonly topology_hash: string;
  readonly entry_node_id: string;
  readonly nodes: readonly {
    readonly id: string;
    readonly title: string;
    readonly capability_ids: readonly string[];
    readonly operation_ids: readonly string[];
    readonly surface_ids: readonly string[];
    readonly policy_count: number;
  }[];
  readonly capabilities: readonly {
    readonly id: string;
    readonly title: string;
    readonly operation_ids: readonly string[];
  }[];
  readonly operation_ids: readonly string[];
}

export interface DesignRevisionView {
  readonly id: string;
  readonly revision: number;
  readonly agent_version: number;
  readonly input_fingerprint: string;
  readonly content: DesignContent;
  readonly topology: DesignTopology;
  readonly source_inputs: readonly Readonly<Record<string, unknown>>[];
  readonly created_at: string;
}

export interface AgentDesignView {
  readonly agent_id: string;
  readonly current_revision_id: string;
  readonly accepted_revision_id: string | null;
  readonly revisions: readonly DesignRevisionView[];
  readonly build_request: null | {
    readonly id: string;
    readonly design_revision_id: string;
    readonly status: string;
    readonly created_at: string;
  };
}
