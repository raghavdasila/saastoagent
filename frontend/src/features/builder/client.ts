import type { AuthorizedTransport } from "@/shared/transport/contracts";
import type { AgentBuildCollectionView, ChannelCollectionView, DeploymentCollectionView, EvaluationCollectionView, OperationsCollectionView, SandboxRunCollectionView } from "./models";

export class AgentRuntimeClient {
  constructor(private readonly transport: AuthorizedTransport) {}

  async builds(agentId: string): Promise<AgentBuildCollectionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/runtime-builds`, "Agent Builds are unavailable.");
  }

  async sandbox(agentId: string): Promise<SandboxRunCollectionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/sandbox`, "Agent Sandbox is unavailable.");
  }

  async evaluations(agentId: string): Promise<EvaluationCollectionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/evaluations`, "Agent Evaluations are unavailable.");
  }

  async channels(agentId: string): Promise<ChannelCollectionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/channels`, "Agent Channels are unavailable.");
  }

  async deployments(agentId: string): Promise<DeploymentCollectionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/deployments`, "Agent Deployments are unavailable.");
  }

  async operations(agentId: string): Promise<OperationsCollectionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/operations`, "Agent Operations are unavailable.");
  }

  private async get<T>(path: string, fallback: string): Promise<T> {
    const response = await this.transport.fetch(path);
    if (!response.ok) {
      const problem = await response.json().catch(() => ({})) as { message?: string };
      throw new Error(problem.message ?? fallback);
    }
    return response.json() as Promise<T>;
  }
}
