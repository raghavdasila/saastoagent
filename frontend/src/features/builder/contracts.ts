import type {
  AgentBuildCollectionView,
  ChannelCollectionView,
  DeploymentCollectionView,
  EvaluationCollectionView,
  OperationsCollectionView,
  SandboxRunCollectionView,
} from "./models";

export type * from "./models";

export interface AgentRuntimeReader {
  builds(agentId: string): Promise<AgentBuildCollectionView>;
  sandbox(agentId: string): Promise<SandboxRunCollectionView>;
  evaluations(agentId: string): Promise<EvaluationCollectionView>;
  channels(agentId: string): Promise<ChannelCollectionView>;
  deployments(agentId: string): Promise<DeploymentCollectionView>;
  operations(agentId: string): Promise<OperationsCollectionView>;
}
