import type { WorkspaceOverviewView } from "./models";

export interface WorkspaceAuthorizedTransport {
  fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response>;
}

export class WorkspaceClient {
  constructor(private readonly transport: WorkspaceAuthorizedTransport) {}

  async overview(): Promise<WorkspaceOverviewView> {
    let response: Response;
    try {
      response = await this.transport.fetch("/api/workspace/overview");
    } catch (error) {
      throw new Error(
        error instanceof Error
          ? error.message
          : "The Workspace overview is unavailable.",
      );
    }
    if (!response.ok) {
      const problem = await readProblem(response);
      throw new Error(
        problem.message ?? `The Workspace overview failed (${response.status}).`,
      );
    }
    return response.json() as Promise<WorkspaceOverviewView>;
  }
}

async function readProblem(response: Response): Promise<{ message?: string }> {
  try {
    return (await response.json()) as { message?: string };
  } catch {
    return {};
  }
}
