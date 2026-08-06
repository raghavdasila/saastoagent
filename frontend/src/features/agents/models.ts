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

export interface CreateAgentInput {
  readonly name: string;
  readonly description: string;
  readonly instructions: string;
}

export interface UpdateAgentInput extends CreateAgentInput {
  readonly agent_id: string;
  readonly expected_version: number;
}
