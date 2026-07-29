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
  story: string
  messages: MockChatMessage[]
  actions: MockAction[]
  mockSurfacePath: string | null
  status: ReviewStatus
  rejectionReason: string
}

export interface PolicyCapabilityDesign {
  id: string
  title: string
  policies: string[]
}

export interface PolicyOperationDesign {
  id: string
  policies: string[]
}

export interface PolicySurfaceDesign {
  id: string
  policies: string[]
}

export interface PolicyNodeDesign {
  id: string
  title: string
  policies: string[]
  capabilities: PolicyCapabilityDesign[]
  activeSurface: PolicySurfaceDesign | null
  operations: PolicyOperationDesign[]
}

export interface FeaturePolicyDesign {
  policies: string[]
  nodes: PolicyNodeDesign[]
}

export interface DesignFeature {
  id: string
  name: string
  stories: DesignStory[]
  policies: FeaturePolicyDesign
}

export interface WorkbenchState {
  version: 10
  features: DesignFeature[]
}
