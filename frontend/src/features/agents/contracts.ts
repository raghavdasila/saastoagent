import type {
  AgentDependencyView,
  AgentBuildLineageView,
  AgentProductOverviewView,
  AgentSourceAttachmentView,
  AgentView,
} from "./models";

export type * from "./models";

export interface AgentStoreSnapshot {
  readonly agents: readonly AgentView[];
  readonly selectedId: string | null;
  readonly loading: boolean;
  readonly error: string | null;
  readonly attachments: readonly AgentSourceAttachmentView[];
  readonly dependencies: AgentDependencyView | null;
  readonly builds: readonly AgentBuildLineageView[];
  readonly productOverview: AgentProductOverviewView | null;
}

export interface CreateAgentDraft {
  readonly name: string;
  readonly description: string;
  readonly instructions: string;
}

export interface AgentSelectionStore {
  snapshot(): AgentStoreSnapshot;
  subscribe(listener: () => void): () => void;
  refresh(): Promise<void>;
  refreshAttachments(agentId: string): Promise<void>;
  syncSelectionFromHandle(agentRef: string | null): void;
}
