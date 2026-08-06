import type { WorkspaceClient } from "./client";
import type { WorkspaceOverviewView } from "./models";

export interface WorkspaceStoreSnapshot {
  readonly overview: WorkspaceOverviewView | null;
  readonly loading: boolean;
  readonly error: string | null;
}

export class WorkspaceStore {
  private state: WorkspaceStoreSnapshot = Object.freeze({
    overview: null,
    loading: false,
    error: null,
  });
  private readonly listeners = new Set<() => void>();
  private generation = 0;

  constructor(private readonly client: WorkspaceClient) {}

  readonly snapshot = (): WorkspaceStoreSnapshot => this.state;

  readonly subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  async refresh(): Promise<void> {
    const generation = ++this.generation;
    this.replace({ ...this.state, loading: true, error: null });
    try {
      const overview = await this.client.overview();
      if (generation !== this.generation) return;
      this.replace({ overview, loading: false, error: null });
    } catch (error) {
      if (generation !== this.generation) return;
      this.replace({
        ...this.state,
        loading: false,
        error: error instanceof Error
          ? error.message
          : "The Workspace overview is unavailable.",
      });
    }
  }

  private replace(next: WorkspaceStoreSnapshot): void {
    this.state = Object.freeze(next);
    this.listeners.forEach((listener) => listener());
  }
}
