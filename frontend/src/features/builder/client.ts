import type { AuthorizedTransport } from "@/shared/transport/contracts";
import type { AgentBuildCollectionView, ChannelCollectionView, DeploymentCollectionView, EvaluationCollectionView, OperationsCollectionView, PlaygroundInteractionView, SandboxDeploymentCollectionView, SandboxDiagnosticsView, SandboxRunCollectionView } from "./models";

export class AgentRuntimeClient {
  constructor(private readonly transport: AuthorizedTransport) {}

  async builds(agentId: string): Promise<AgentBuildCollectionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/runtime-builds`, "Agent Builds are unavailable.");
  }

  async sandbox(agentId: string): Promise<SandboxRunCollectionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/sandbox/legacy`, "Legacy Sandbox evidence is unavailable.");
  }

  async sandboxDeployment(agentId: string): Promise<SandboxDeploymentCollectionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/sandbox`, "Agent Sandbox is unavailable.");
  }

  async deploySandbox(agentId: string, buildId: string, requestKey: string) {
    return this.post(`/api/agents/${encodeURIComponent(agentId)}/sandbox/deployments`, { build_id: buildId, request_key: requestKey }, "Sandbox deployment failed.");
  }

  async createPlaygroundSession(agentId: string): Promise<PlaygroundInteractionView> {
    return this.post(`/api/agents/${encodeURIComponent(agentId)}/sandbox/sessions`, {}, "Sandbox conversation could not start.");
  }

  async playgroundSession(agentId: string, sessionId: string): Promise<PlaygroundInteractionView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/sandbox/sessions/${encodeURIComponent(sessionId)}`, "Sandbox conversation is unavailable.");
  }

  async sendPlaygroundMessage(agentId: string, sessionId: string, text: string): Promise<PlaygroundInteractionView> {
    return this.post(`/api/agents/${encodeURIComponent(agentId)}/sandbox/sessions/${encodeURIComponent(sessionId)}/messages`, { text }, "Sandbox message failed.");
  }

  async resolvePlaygroundReview(agentId: string, sessionId: string, reviewId: string, accepted: boolean): Promise<PlaygroundInteractionView> {
    return this.post(`/api/agents/${encodeURIComponent(agentId)}/sandbox/sessions/${encodeURIComponent(sessionId)}/reviews`, { review_id: reviewId, accepted }, "Sandbox review failed.");
  }

  async sandboxDiagnostics(agentId: string, sessionId: string): Promise<SandboxDiagnosticsView> {
    return this.get(`/api/agents/${encodeURIComponent(agentId)}/sandbox/sessions/${encodeURIComponent(sessionId)}/diagnostics`, "Sandbox diagnostics are unavailable.");
  }

  async runEvaluationSet(agentId: string, evaluationSetId: string, sandboxDeploymentId: string): Promise<EvaluationCollectionView> {
    return this.post(`/api/agents/${encodeURIComponent(agentId)}/evaluations/sandbox-runs`, { evaluation_set_id: evaluationSetId, sandbox_deployment_id: sandboxDeploymentId }, "Sandbox evaluation could not start.");
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

  private async post<T>(path: string, body: Readonly<Record<string, unknown>>, fallback: string): Promise<T> {
    const response = await this.transport.fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const problem = await response.json().catch(() => ({})) as { message?: string };
      throw new Error(problem.message ?? fallback);
    }
    return response.json() as Promise<T>;
  }
}
