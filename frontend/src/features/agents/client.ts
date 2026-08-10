import type {
  AgentDependencyView,
  AgentBuildLineageListView,
  AgentListView,
  AgentSourceAttachmentListView,
  AgentView,
} from "./models";

export interface AgentAuthorizedTransport {
  fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response>;
}

export class AgentClientError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "AgentClientError";
  }
}

export class AgentClient {
  constructor(private readonly transport: AgentAuthorizedTransport) {}

  async list(): Promise<AgentListView> {
    return this.request<AgentListView>("/api/agents");
  }

  async get(agentId: string): Promise<AgentView> {
    return this.request<AgentView>(
      `/api/agents/${encodeURIComponent(agentId)}`,
    );
  }

  async listSources(agentId: string): Promise<AgentSourceAttachmentListView> {
    return this.request<AgentSourceAttachmentListView>(
      `/api/agents/${encodeURIComponent(agentId)}/sources`,
    );
  }

  async inspectDependencies(agentId: string): Promise<AgentDependencyView> {
    return this.request<AgentDependencyView>(
      `/api/agents/${encodeURIComponent(agentId)}/dependencies`,
    );
  }

  async listBuilds(agentId: string): Promise<AgentBuildLineageListView> {
    return this.request<AgentBuildLineageListView>(
      `/api/agents/${encodeURIComponent(agentId)}/builds`,
    );
  }

  private async request<T>(url: string): Promise<T> {
    let response: Response;
    try {
      response = await this.transport.fetch(url);
    } catch (error) {
      throw new AgentClientError(
        error instanceof Error
          ? error.message
          : "The Agents service is unavailable.",
        "agent_network_failure",
        0,
      );
    }
    if (!response.ok) {
      const problem = await readProblem(response);
      throw new AgentClientError(
        problem.message ?? `The Agents request failed (${response.status}).`,
        problem.code ?? "agent_request_failed",
        response.status,
      );
    }
    return response.json() as Promise<T>;
  }
}

async function readProblem(
  response: Response,
): Promise<{ code?: string; message?: string }> {
  try {
    return (await response.json()) as { code?: string; message?: string };
  } catch {
    return {};
  }
}
