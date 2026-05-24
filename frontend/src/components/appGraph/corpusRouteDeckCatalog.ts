export const corpusNodeIds = {
  home: 'home',
  agentHome: 'agent_home',
  saasAgentSelect: 'saas_agent_select',
  saasAgentCreate: 'saas_agent_create',
} as const

export const corpusOperationIds = {
  navigateHome: 'navigate.home',
  createSaaSAgent: 'saas_agent.create',
  listSaaSAgents: 'saas_agent.list',
  openSaaSAgent: 'saas_agent.open',
} as const

export const corpusSurfaceComponents = {
  auth: 'CorpusAuthSurface',
  lounge: 'CorpusLoungeSurface',
  dashboard: 'CorpusDashboardSurface',
  instructions: 'InstructionsSurface',
  entities: 'EntitiesSurface',
  actions: 'ActionsSurface',
  knowledge: 'KnowledgeSurface',
  learning: 'LearningSurface',
  qa: 'QASurface',
  memory: 'MemorySurface',
  schemaPreview: 'SchemaPreviewSurface',
  catalog: 'CatalogSurface',
  connectionSetup: 'ConnectionSetupSurface',
  saaSAgentList: 'SaaSAgentListSurface',
  execution: 'ExecutionSurface',
  recovery: 'RecoverySurface',
} as const
