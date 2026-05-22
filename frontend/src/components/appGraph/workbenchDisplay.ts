export function displayWork(value: string) {
  const labels: Record<string, string> = {
    home: 'Home',
    auth_sign_in: 'Sign in',
    auth_register: 'Create account',
    saas_agent_select: 'Select SaaS Agent',
    saas_agent_create: 'Create SaaS Agent',
    agent_home: 'SaaS Agent Home',
    connection_configure: 'Connect API',
    schema_preview: 'Schema Preview',
    catalog_activation: 'Catalog Activation',
    catalog: 'Catalog',
    entities: 'Entities',
    actions: 'Actions',
    execution_planning: 'Execution Planning',
    needs_input: 'Needs Input',
    approval_required: 'Approval Required',
    executing: 'Executing',
    result_review: 'Result Review',
    knowledge: 'Knowledge',
    memory: 'Memory',
    learning: 'Learning',
    qa: 'QA',
    recovery: 'Recovery',
    lounge: 'Lounge',
  }
  if (labels[value]) return labels[value]
  return value
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}
