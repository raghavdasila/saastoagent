export type ReviewStatus = "draft" | "approved" | "rejected"
export type ChatActor = "Corpus" | "Owner"

export interface MockChatMessage {
  id: string
  actor: ChatActor
  content: string
}

export interface MockAction {
  id: string
  label: string
}

export interface DesignStory {
  id: string
  title: string
  userIntent: string
  agentIntent: string
  expectedBehavior: string
  messages: MockChatMessage[]
  actions: MockAction[]
  mockSurfacePath: string | null
  policies: AgentPolicyDesign[]
  status: ReviewStatus
  rejectionReason: string
}

export type AgentPolicyScope =
  | "feature"
  | "behavior"
  | "node"
  | "capability"
  | "surface"
  | "action"
  | "operation"
  | "other"

export interface AgentPolicyDesign {
  scope: AgentPolicyScope
  scopeName: string
  guidance: string
}

export interface DesignFeature {
  id: string
  name: string
  stories: DesignStory[]
  policies: AgentPolicyDesign[]
}

export interface WorkbenchState {
  version: 13
  features: DesignFeature[]
}
