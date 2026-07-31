export type ReviewStatus = "draft" | "approved" | "rejected"
export type ChatActor = "Corpus" | "Owner"

export interface MockChatMessage {
  id: string
  actor: ChatActor
  content: string
}

export interface SuggestedActionDesign {
  id: string
  label: string
  operationName: string
  visibility: string
}

export interface DesignStory {
  id: string
  title: string
  userIntent: string
  agentIntent: string
  expectedBehavior: string
  messages: MockChatMessage[]
  mockSurfacePath: string | null
  nodePolicies: string[]
  capabilities: CapabilityDesign[]
  surfaces: SurfaceDesign[]
  operations: OperationDesign[]
  suggestedActions: SuggestedActionDesign[]
  status: ReviewStatus
  rejectionReason: string
}

export interface CapabilityDesign {
  name: string
  purpose: string
  operationNames: string[]
  surfaceNames: string[]
  policies: string[]
}

export interface SurfaceDesign {
  name: string
  purpose: string
  policies: string[]
}

export interface OperationDesign {
  name: string
  purpose: string
  inputs: string
  outcomes: string
  safetyAndReview: string
  recovery: string
  policies: string[]
}

export interface DesignFeature {
  id: string
  name: string
  prompt: string
  stories: DesignStory[]
  policies: string[]
}

export interface WorkbenchState {
  version: 20
  features: DesignFeature[]
}
