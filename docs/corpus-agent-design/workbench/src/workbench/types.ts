export type ReviewStatus = "draft" | "approved" | "rejected"
export type ChatActor = "Corpus" | "Owner"

export interface MockChatMessage {
  id: string
  actor: ChatActor
  content: string
}

export interface DesignStory {
  id: string
  title: string
  story: string
  messages: MockChatMessage[]
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
  version: 3
  features: DesignFeature[]
}
