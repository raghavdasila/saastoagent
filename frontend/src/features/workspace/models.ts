export type WorkspaceSectionStatus = "available" | "empty" | "unavailable";

export interface WorkspaceSectionView {
  readonly status: WorkspaceSectionStatus;
  readonly message: string;
}

export interface WorkspaceOverviewView {
  readonly agent_count: number;
  readonly source_count: number;
  readonly agents: WorkspaceSectionView;
  readonly sources: WorkspaceSectionView;
  readonly recent_activity: WorkspaceSectionView;
  readonly activity: readonly WorkspaceActivityView[];
}

export interface WorkspaceActivityView {
  readonly kind: "agent" | "source";
  readonly title: string;
  readonly status: string;
  readonly occurred_at: string;
}
