export interface ChannelDraft {
  readonly name: string;
  readonly slug: string;
}

const EMPTY_DRAFT: ChannelDraft = Object.freeze({ name: "", slug: "" });

export class ChannelDraftStore {
  private readonly drafts = new Map<string, ChannelDraft>();
  private readonly listeners = new Set<() => void>();

  readonly subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  get(agentId: string): ChannelDraft {
    return this.drafts.get(agentId) ?? EMPTY_DRAFT;
  }

  update(agentId: string, next: Partial<ChannelDraft>): ChannelDraft {
    const value = Object.freeze({ ...this.get(agentId), ...next });
    this.drafts.set(agentId, value);
    this.notify();
    return value;
  }

  clear(agentId: string): void {
    if (this.drafts.delete(agentId)) this.notify();
  }

  private notify(): void {
    this.listeners.forEach((listener) => listener());
  }
}
