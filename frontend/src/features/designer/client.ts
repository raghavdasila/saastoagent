import type { AuthorizedTransport } from "@/shared/transport/contracts";
import type { AgentDesignView } from "./models";

export class DesignerClient {
  constructor(private readonly transport: AuthorizedTransport) {}

  async get(agentId: string): Promise<AgentDesignView | null> {
    const response = await this.transport.fetch(`/api/agents/${encodeURIComponent(agentId)}/design`);
    if (!response.ok) {
      const problem = await response.json().catch(() => ({})) as { message?: string };
      throw new Error(problem.message ?? "Agent Designer is unavailable.");
    }
    return response.json() as Promise<AgentDesignView | null>;
  }
}
