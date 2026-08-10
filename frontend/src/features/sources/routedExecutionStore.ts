import type {
  ApiRoutePlanView,
  ApiRoutedExecutionView,
  SourceClient,
} from "./sourceClient";

interface RoutedExecutionContext {
  readonly sourceId: string;
  readonly plan: ApiRoutePlanView;
}

interface RoutedExecutionSnapshot {
  readonly context: RoutedExecutionContext | null;
  readonly result: ApiRoutedExecutionView | null;
  readonly loading: boolean;
  readonly error: string | null;
}

export class RoutedExecutionStore {
  private value: RoutedExecutionSnapshot = {
    context: null,
    result: null,
    loading: false,
    error: null,
  };
  private generation = 0;
  private readonly listeners = new Set<() => void>();

  constructor(private readonly client: SourceClient) {}

  readonly snapshot = (): RoutedExecutionSnapshot => this.value;
  readonly subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  async select(sourceId: string, plan: ApiRoutePlanView): Promise<void> {
    const ticket = ++this.generation;
    this.update({
      context: { sourceId, plan },
      result: null,
      loading: true,
      error: null,
    });
    try {
      const result = await this.client.currentRoutedApiExecution(sourceId, plan.plan_id);
      if (ticket !== this.generation) return;
      this.update({ context: { sourceId, plan }, result, loading: false, error: null });
    } catch (error) {
      if (ticket !== this.generation) return;
      this.update({
        context: { sourceId, plan },
        result: null,
        loading: false,
        error: error instanceof Error ? error.message : "The routed API result is unavailable.",
      });
    }
  }

  async refresh(): Promise<void> {
    const context = this.value.context;
    if (context === null) return;
    await this.select(context.sourceId, context.plan);
  }

  clear(): void {
    this.generation += 1;
    this.update({ context: null, result: null, loading: false, error: null });
  }

  reportError(message: string): void {
    this.update({ ...this.value, error: message, loading: false });
  }

  clearError(): void {
    this.update({ ...this.value, error: null });
  }

  private update(value: RoutedExecutionSnapshot): void {
    this.value = value;
    this.listeners.forEach((listener) => listener());
  }
}
