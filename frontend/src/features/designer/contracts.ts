import type { AgentDesignView } from "./models";

export type * from "./models";

export interface DesignerReader {
  get(agentId: string): Promise<AgentDesignView | null>;
}
