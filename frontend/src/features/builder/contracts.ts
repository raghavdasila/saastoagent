import type {
  AgentBuildCollectionView,
  ChannelCollectionView,
  DeploymentCollectionView,
  EvaluationCollectionView,
  OperationsCollectionView,
  SandboxRunCollectionView,
  SandboxDeploymentCollectionView,
} from "./models";

export type * from "./models";

export interface AgentRuntimeReader {
  builds(agentId: string): Promise<AgentBuildCollectionView>;
  sandbox(agentId: string): Promise<SandboxRunCollectionView>;
  sandboxDeployment(agentId: string): Promise<SandboxDeploymentCollectionView>;
  evaluations(agentId: string): Promise<EvaluationCollectionView>;
  channels(agentId: string): Promise<ChannelCollectionView>;
  deployments(agentId: string): Promise<DeploymentCollectionView>;
  operations(agentId: string): Promise<OperationsCollectionView>;
}
