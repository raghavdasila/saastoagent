import { type ReactNode, createContext, useCallback, useContext, useEffect, useState } from 'react'

import { api } from '@/lib/api'
import { storage } from '@/lib/storage'
import type { AuthTokens, User } from '@/types/domain'

interface AuthContextValue {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName?: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(storage.getToken())
  const [isLoading, setIsLoading] = useState(true)

  const fetchUser = useCallback(async () => {
    if (!storage.getToken()) {
      setIsLoading(false)
      return
    }

    try {
      const currentUser = await api.get<User>('/me')
      setUser(currentUser)
    } catch {
      storage.removeToken()
      setToken(null)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const login = async (email: string, password: string) => {
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
    setToken(data.access_token)

    const currentUser = await api.get<User>('/me')
    setUser(currentUser)
  }

  const register = async (email: string, password: string, displayName?: string) => {
    await api.post('/auth/register', {
      email,
      password,
      display_name: displayName || undefined,
    })
    await login(email, password)
  }

  const logout = () => {
    storage.removeToken()
    storage.removeWorkspaceId()
    setUser(null)
    setToken(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
