import type { AgentClient } from "./client";
import type {
  AgentDependencyView,
  AgentBuildLineageView,
  AgentProductOverviewView,
  AgentSourceAttachmentView,
  AgentView,
} from "./models";

export interface AgentStoreSnapshot {
  readonly agents: readonly AgentView[];
  readonly selectedId: string | null;
  readonly loading: boolean;
  readonly error: string | null;
  readonly attachments: readonly AgentSourceAttachmentView[];
  readonly dependencies: AgentDependencyView | null;
  readonly builds: readonly AgentBuildLineageView[];
  readonly productOverview: AgentProductOverviewView | null;
}

export interface CreateAgentDraft {
  readonly name: string;
  readonly description: string;
  readonly instructions: string;
}

const EMPTY_CREATE_DRAFT: CreateAgentDraft = Object.freeze({
  name: "",
  description: "",
  instructions: "",
});

const INITIAL: AgentStoreSnapshot = Object.freeze({
  agents: Object.freeze([]),
  selectedId: null,
  loading: false,
  error: null,
  attachments: Object.freeze([]),
  dependencies: null,
  builds: Object.freeze([]),
  productOverview: null,
});

export class AgentStore {
  private state = INITIAL;
  private createAgentDraft: CreateAgentDraft = EMPTY_CREATE_DRAFT;
  private readonly listeners = new Set<() => void>();
  private requestGeneration = 0;

  constructor(private readonly client: AgentClient) {}

  readonly createDraft = (): CreateAgentDraft => this.createAgentDraft;

  updateCreateDraft(next: Partial<CreateAgentDraft>): void {
    this.createAgentDraft = Object.freeze({ ...this.createAgentDraft, ...next });
    this.notify();
  }

  clearCreateDraft(): void {
    if (this.createAgentDraft === EMPTY_CREATE_DRAFT) return;
    this.createAgentDraft = EMPTY_CREATE_DRAFT;
    this.notify();
  }

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
        : null;
      this.replace({
        agents: Object.freeze([...result.agents]),
        selectedId,
        loading: false,
        error: null,
        attachments: selectedId === null ? Object.freeze([]) : this.state.attachments,
        dependencies: selectedId === null ? null : this.state.dependencies,
        builds: selectedId === null ? Object.freeze([]) : this.state.builds,
        productOverview: selectedId === null ? null : this.state.productOverview,
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
    if (this.state.selectedId === agentId) return;
    this.replace({
      ...this.state,
      selectedId: agentId,
      attachments: Object.freeze([]),
      dependencies: null,
      builds: Object.freeze([]),
      productOverview: null,
    });
  }

  clearSelection(): void {
    if (this.state.selectedId === null) return;
    this.replace({
      ...this.state,
      selectedId: null,
      attachments: Object.freeze([]),
      dependencies: null,
      builds: Object.freeze([]),
      productOverview: null,
    });
  }

  syncSelectionFromHandle(agentRef: string | null): void {
    if (agentRef === null) return;
    const selected = this.state.agents.find(
      (agent) => `agent-${agent.id.replaceAll("-", "").slice(0, 20)}` === agentRef,
    );
    if (selected !== undefined) this.select(selected.id);
  }

  async refreshAttachments(agentId: string): Promise<void> {
    try {
      const result = await this.client.listSources(agentId);
      if (this.state.selectedId !== agentId) return;
      this.replace({
        ...this.state,
        attachments: Object.freeze([...result.attachments]),
        error: null,
      });
    } catch (error) {
      if (this.state.selectedId !== agentId) return;
      this.replace({ ...this.state, error: errorMessage(error) });
    }
  }

  async refreshDependencies(agentId: string): Promise<void> {
    try {
      const result = await this.client.inspectDependencies(agentId);
      if (this.state.selectedId !== agentId) return;
      this.replace({ ...this.state, dependencies: result, error: null });
    } catch (error) {
      if (this.state.selectedId !== agentId) return;
      this.replace({ ...this.state, dependencies: null, error: errorMessage(error) });
    }
  }

  async refreshBuilds(agentId: string): Promise<void> {
    try {
      const result = await this.client.listBuilds(agentId);
      if (this.state.selectedId !== agentId) return;
      this.replace({ ...this.state, builds: Object.freeze([...result.builds]), error: null });
    } catch (error) {
      if (this.state.selectedId !== agentId) return;
      this.replace({ ...this.state, builds: Object.freeze([]), error: errorMessage(error) });
    }
  }

  async refreshProductOverview(agentId: string): Promise<void> {
    try {
      const result = await this.client.productOverview(agentId);
      if (this.state.selectedId !== agentId) return;
      this.replace({ ...this.state, productOverview: result, error: null });
    } catch (error) {
      if (this.state.selectedId !== agentId) return;
      this.replace({ ...this.state, productOverview: null, error: errorMessage(error) });
    }
  }

  clearError(): void {
    if (this.state.error === null) return;
    this.replace({ ...this.state, error: null });
  }

  reportError(message: string): void {
    this.replace({ ...this.state, error: message });
  }

  private replace(next: AgentStoreSnapshot): void {
    this.state = Object.freeze(next);
    this.notify();
  }

  private notify(): void {
    this.listeners.forEach((listener) => listener());
  }
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Agents could not be loaded.";
}
