import { create } from 'zustand'

import { api } from '@/lib/api'
import { storage } from '@/lib/storage'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import type { AuthTokens, User } from '@/types/domain'

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  hydrateAuth: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName?: string) => Promise<void>
  applySession: (user: User, token: string) => void
  logout: () => void
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: storage.getToken(),
  isLoading: true,

  hydrateAuth: async () => {
    const token = storage.getToken()

    if (!token) {
      set({ token: null, user: null, isLoading: false })
      return
    }

    set({ token, isLoading: true })

    try {
      const currentUser = await api.get<User>('/me')
      set({ user: currentUser, token, isLoading: false })
    } catch {
      storage.removeToken()
      set({ user: null, token: null, isLoading: false })
    }
  },

  login: async (email: string, password: string) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(body.detail || 'Login failed')
    }

    const data: AuthTokens = await response.json()
    storage.setToken(data.access_token)
    set({ token: data.access_token })

    const currentUser = await api.get<User>('/me')
    set({ user: currentUser })
  },

  register: async (email: string, password: string, displayName?: string) => {
    await api.post('/auth/register', {
      email,
      password,
      display_name: displayName || undefined,
    })
    await get().login(email, password)
  },

  applySession: (user, token) => {
    storage.setToken(token)
    set({ user, token, isLoading: false })
  },

  logout: () => {
    storage.removeToken()
    useWorkspaceStore.getState().clearWorkspace()
    set({ user: null, token: null })
  },

  setUser: (user) => set({ user }),
}))
