import type { AgentClient } from "./client";
import type { AgentView } from "./models";

export interface AgentStoreSnapshot {
  readonly agents: readonly AgentView[];
  readonly selectedId: string | null;
  readonly loading: boolean;
  readonly error: string | null;
}

const INITIAL: AgentStoreSnapshot = Object.freeze({
  agents: Object.freeze([]),
  selectedId: null,
  loading: false,
  error: null,
});

export class AgentStore {
  private state = INITIAL;
  private readonly listeners = new Set<() => void>();
  private requestGeneration = 0;

  constructor(private readonly client: AgentClient) {}

  readonly snapshot = (): AgentStoreSnapshot => this.state;

  readonly subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  async refresh(): Promise<void> {
    const generation = ++this.requestGeneration;
    this.replace({ ...this.state, loading: true, error: null });
    try {
      const result = await this.client.list();
      if (generation !== this.requestGeneration) return;
      const selectedId = result.agents.some(
        (agent) => agent.id === this.state.selectedId,
      )
        ? this.state.selectedId
        : result.agents.at(0)?.id ?? null;
      this.replace({
        agents: Object.freeze([...result.agents]),
        selectedId,
        loading: false,
        error: null,
      });
    } catch (error) {
      if (generation !== this.requestGeneration) return;
      this.replace({
        ...this.state,
        loading: false,
        error: errorMessage(error),
      });
    }
  }

  select(agentId: string): void {
    if (!this.state.agents.some((agent) => agent.id === agentId)) return;
    this.replace({ ...this.state, selectedId: agentId });
  }

  clearError(): void {
    if (this.state.error === null) return;
    this.replace({ ...this.state, error: null });
  }

  private replace(next: AgentStoreSnapshot): void {
    this.state = Object.freeze(next);
    this.listeners.forEach((listener) => listener());
  }
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Agents could not be loaded.";
}
