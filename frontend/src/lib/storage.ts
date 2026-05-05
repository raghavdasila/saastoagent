const TOKEN_KEY = 'sta_v01_token'
const WORKSPACE_KEY = 'sta_v01_workspace_id'

export const storage = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  removeToken: () => localStorage.removeItem(TOKEN_KEY),

  getWorkspaceId: () => localStorage.getItem(WORKSPACE_KEY),
  setWorkspaceId: (id: string) => localStorage.setItem(WORKSPACE_KEY, id),
  removeWorkspaceId: () => localStorage.removeItem(WORKSPACE_KEY),
}
