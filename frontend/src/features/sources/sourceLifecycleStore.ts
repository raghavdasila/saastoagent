import type { SourceDependencyView, SourceView } from "./contracts";
import type { SourceClient } from "./sourceClient";

export interface SourceLifecycleSnapshot {
  readonly selected: SourceView | null;
  readonly dependencies: SourceDependencyView | null;
}

const EMPTY: SourceLifecycleSnapshot = Object.freeze({ selected: null, dependencies: null });

export class SourceLifecycleStore {
  private state: SourceLifecycleSnapshot = EMPTY;
  private readonly listeners = new Set<() => void>();

  constructor(private readonly client: SourceClient) {}

  readonly subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  readonly snapshot = (): SourceLifecycleSnapshot => this.state;

  select(source: SourceView): void {
    this.replace({ selected: source, dependencies: null });
  }

  async refreshDependencies(sourceId: string): Promise<SourceDependencyView> {
    const dependencies = await this.client.inspectDependencies(sourceId);
    if (this.state.selected?.source_id === sourceId) {
      this.replace({ ...this.state, dependencies });
    }
    return dependencies;
  }

  clear(): void {
    this.replace(EMPTY);
  }

  private replace(next: SourceLifecycleSnapshot): void {
    this.state = Object.freeze(next);
    for (const listener of this.listeners) listener();
  }
}
