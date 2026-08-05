export type ReviewStatus = "draft" | "approved" | "rejected"
export type ChatActor = "Corpus" | "Owner"
export type EvalCoverageTag = "normal" | "boundary" | "failure" | "privacy" | "adversarial"

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

export interface DeterministicExpectations {
  startingBehavior: string
  finalBehavior: string
  allowedFinalBehaviors?: string[]
  authentication: "public" | "authenticated" | "unchanged"
  requiredOperations: string[]
  allowedOperations: string[]
  forbiddenOperations: string[]
  requiredSurfaces: string[]
  requiredSuggestedActions: string[]
  forbiddenOutcomes: string[]
}

export interface BehaviorEvalCase {
  id: string
  title: string
  enabled: boolean
  blocking: boolean
  coverage: EvalCoverageTag[]
  input: string
  referenceResponse: string
  requiredCriteria: string[]
  forbiddenCriteria: string[]
  expectations: DeterministicExpectations
}

export interface EvaluationExemption {
  coverage: EvalCoverageTag
  reason: string
}

export interface FeatureConversationEvalScenario {
  id: string
  title: string
  enabled: boolean
  blocking: boolean
  openingMessage: string
  hiddenGoal: string
  persona: string
  facts: string[]
  mayDisclose: string[]
  withholdUntilAsked: string[]
  bypassAttempts: string[]
  perTurnCriteria: string[]
  finalRequiredCriteria: string[]
  finalForbiddenCriteria: string[]
  expectations: DeterministicExpectations
  successCondition: string
  failureConditions: string[]
  stoppingConditions: string[]
  maxTurns: number
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
  behaviorEvals: BehaviorEvalCase[]
  evalExemptions: EvaluationExemption[]
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
  conversationEvals: FeatureConversationEvalScenario[]
}

export interface WorkbenchState {
  features: DesignFeature[]
}
