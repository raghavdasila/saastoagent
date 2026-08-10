export class DesignerRefreshStore {
  private value = 0;
  private readonly listeners = new Set<() => void>();

  readonly snapshot = () => this.value;
  readonly subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };
  notify(): void {
    this.value += 1;
    this.listeners.forEach((listener) => listener());
  }
}
