export type WorkspaceSectionStatus = "available" | "empty" | "unavailable";

export interface WorkspaceSectionView {
  readonly status: WorkspaceSectionStatus;
  readonly message: string;
}

export interface WorkspaceOverviewView {
  readonly agent_count: number;
  readonly agents: WorkspaceSectionView;
  readonly sources: WorkspaceSectionView;
  readonly recent_activity: WorkspaceSectionView;
}
