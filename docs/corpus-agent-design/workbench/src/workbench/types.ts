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

export interface DesignFeature {
  id: string
  name: string
  stories: DesignStory[]
}

export interface WorkbenchState {
  version: 6
  features: DesignFeature[]
}
