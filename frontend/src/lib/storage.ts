const TOKEN_KEY = 'sta_v01_token'
const SAAS_AGENT_KEY = 'sta_v01_saas_agent_id'

export const storage = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  removeToken: () => localStorage.removeItem(TOKEN_KEY),

  getSaaSAgentId: () => localStorage.getItem(SAAS_AGENT_KEY),
  setSaaSAgentId: (id: string) => localStorage.setItem(SAAS_AGENT_KEY, id),
  removeSaaSAgentId: () => localStorage.removeItem(SAAS_AGENT_KEY),
}
