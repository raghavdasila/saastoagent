import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bot, Lock, LogOut, RotateCcw } from 'lucide-react'
import { useParams } from 'react-router-dom'

import { ChatInput } from '@/components/agent/ChatInput'
import { MessageBubble } from '@/components/agent/MessageBubble'
import { useAuth } from '@/context/AuthContext'
import { useSSEChat } from '@/hooks/useSSEChat'
import { api } from '@/lib/api'
import { storage } from '@/lib/storage'
import type { DeployedAgentProfile } from '@/types/domain'
import type { ChatUIMessage } from '@/types/agent'

interface PublicAssistantMessageEvent {
  message_id: string
  session_id: string
  role: 'assistant'
  content: string
}

export function DeployedAgentChatPage() {
  const { slug } = useParams<{ slug: string }>()
  const { user, login, register, logout } = useAuth()
  const [error, setError] = useState<string | null>(null)

  const profileQuery = useQuery({
    queryKey: ['deployed-agent-profile', slug],
    queryFn: () => api.get<DeployedAgentProfile>(`/deployed-agents/${slug}`),
    enabled: Boolean(slug),
  })

  const profile = profileQuery.data
  const chatPath = slug ? `/api/deployed-agents/${slug}/chat` : null
  const {
    messages,
    isStreaming,
    sessionId,
    sendMessage,
    clearMessages,
    setMessages,
  } = useSSEChat({
    saasAgentId: profile?.saas_agent_id ?? null,
    chatPath,
    onError: setError,
  })

  const appendPublicAssistantMessage = useCallback((event: PublicAssistantMessageEvent) => {
    setMessages((current) => {
      if (current.some((message) => message.id === event.message_id)) return current
      const message: ChatUIMessage = {
        id: event.message_id,
        role: 'assistant',
        content: event.content,
        timestamp: Date.now(),
        source: 'agent',
      }
      return [...current, message]
    })
  }, [setMessages])

  useDeployedSessionEvents({
    slug: slug || null,
    sessionId,
    enabled: Boolean((slug && sessionId && !profile?.auth_required) || user),
    onMessage: appendPublicAssistantMessage,
    onError: setError,
  })

  const authBlocked = Boolean(profile?.auth_required && !user)

  if (profileQuery.isLoading) {
    return <PublicShell title="Loading agent..." />
  }

  if (profileQuery.error || !profile) {
    return (
      <PublicShell title="Agent unavailable">
        <p className="text-sm text-muted-foreground">
          This deployed agent does not exist or is not enabled yet.
        </p>
      </PublicShell>
    )
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.16),transparent_34%),linear-gradient(135deg,#f8fafc,#eef2f7)] text-foreground dark:bg-[radial-gradient(circle_at_top_left,rgba(56,189,248,0.16),transparent_34%),linear-gradient(135deg,#09090b,#111827)]">
      <header className="border-b border-border/60 bg-background/82 px-4 py-4 shadow-sm backdrop-blur md:px-8">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-sm">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">{profile.name}</h1>
              <p className="text-xs text-muted-foreground">Deployed SaaS agent · /a/{profile.slug}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="rounded-full border border-border bg-background px-3 py-1">
              {profile.auth_required ? 'Login required' : 'Anonymous allowed'}
            </span>
            {user && (
              <button
                type="button"
                onClick={logout}
                className="inline-flex items-center gap-1 rounded-full border border-border bg-background px-3 py-1 text-foreground"
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign out
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-5xl flex-col px-4 py-5 md:px-8">
        {authBlocked ? (
          <DeployedAuthGate
            onLogin={login}
            onRegister={register}
            onError={setError}
            error={error}
          />
        ) : (
          <>
            <section className="flex-1 overflow-y-auto rounded-3xl border border-border/70 bg-background/80 shadow-xl shadow-slate-950/5 backdrop-blur dark:bg-background/55">
              {messages.length === 0 && !isStreaming ? (
                <div className="mx-auto flex max-w-2xl flex-col items-center px-6 py-16 text-center">
                  <Bot className="h-10 w-10 text-primary" />
                  <h2 className="mt-4 text-2xl font-semibold">Talk to {profile.name}</h2>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">{profile.welcome_message}</p>
                  <button
                    type="button"
                    className="mt-6 rounded-full border border-border bg-background px-4 py-2 text-sm"
                    onClick={() => sendMessage('What can you help me do?', sessionId)}
                  >
                    What can you help me do?
                  </button>
                </div>
              ) : (
                <div className="mx-auto max-w-4xl py-4">
                  {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} showToolCalls={false} collapseJsonPayloads />
                  ))}
                </div>
              )}
            </section>

            <section className="mt-4 rounded-2xl border border-border/70 bg-background/90 p-3 shadow-lg shadow-slate-950/5 backdrop-blur">
              {error && (
                <div className="mb-2 rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
                  {error}
                </div>
              )}
              <div className="flex items-end gap-2">
                <div className="min-w-0 flex-1">
                  <ChatInput
                    onSend={(text) => {
                      setError(null)
                      sendMessage(text, sessionId)
                    }}
                    disabled={isStreaming}
                    placeholder="Describe what you need done"
                  />
                </div>
                <button
                  type="button"
                  onClick={clearMessages}
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-border text-muted-foreground"
                  title="Reset chat"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}

function useDeployedSessionEvents({
  slug,
  sessionId,
  enabled,
  onMessage,
  onError,
}: {
  slug: string | null
  sessionId: string | null
  enabled: boolean
  onMessage: (event: PublicAssistantMessageEvent) => void
  onError: (message: string | null) => void
}) {
  const lastMessageIdRef = useRef<string | null>(null)

  useEffect(() => {
    if (!slug || !sessionId || !enabled) return undefined
    const params = new URLSearchParams()
    if (lastMessageIdRef.current) {
      params.set('after_message_id', lastMessageIdRef.current)
    }
    const path = `/api/deployed-agents/${slug}/sessions/${sessionId}/events${params.toString() ? `?${params.toString()}` : ''}`
    const xhr = new XMLHttpRequest()
    let canceled = false
    let cursor = 0
    let buffer = ''
    xhr.open('GET', path)
    const token = storage.getToken()
    if (token && token !== 'undefined' && token !== 'null') {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    }
    xhr.onprogress = () => {
      const chunk = xhr.responseText.slice(cursor)
      cursor = xhr.responseText.length
      buffer += chunk
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''
      for (const eventText of events) {
        const lines = eventText.split('\n')
        const eventLine = lines.find((line) => line.startsWith('event: '))
        const dataLine = lines.find((line) => line.startsWith('data: '))
        if (eventLine?.slice(7).trim() !== 'assistant_message' || !dataLine) continue
        try {
          const event = JSON.parse(dataLine.slice(6)) as PublicAssistantMessageEvent
          if (!event.message_id || !event.content) continue
          lastMessageIdRef.current = event.message_id
          onMessage(event)
        } catch {
          // Keep waiting for a complete SSE frame.
        }
      }
    }
    xhr.onerror = () => {
      if (!canceled) onError('Live chat updates disconnected.')
    }
    xhr.send()
    return () => {
      canceled = true
      xhr.abort()
    }
  }, [slug, sessionId, enabled, onMessage, onError])
}

function PublicShell({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md rounded-3xl border border-border bg-card p-8 text-center shadow-lg">
        <Bot className="mx-auto h-10 w-10 text-primary" />
        <h1 className="mt-4 text-xl font-semibold">{title}</h1>
        {children}
      </div>
    </div>
  )
}

function DeployedAuthGate({
  onLogin,
  onRegister,
  onError,
  error,
}: {
  onLogin: (email: string, password: string) => Promise<void>
  onRegister: (email: string, password: string, displayName?: string) => Promise<void>
  onError: (message: string | null) => void
  error: string | null
}) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    setBusy(true)
    onError(null)
    try {
      if (mode === 'register') {
        await onRegister(email, password, displayName)
      } else {
        await onLogin(email, password)
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto mt-10 max-w-md rounded-3xl border border-border bg-background/90 p-6 shadow-xl">
      <div className="flex items-center gap-3">
        <Lock className="h-5 w-5 text-primary" />
        <div>
          <h2 className="font-semibold">Sign in to continue</h2>
          <p className="text-xs text-muted-foreground">This agent follows the connected SaaS auth policy.</p>
        </div>
      </div>
      <div className="mt-5 space-y-3">
        {mode === 'register' && (
          <input
            className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
            placeholder="Display name"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
          />
        )}
        <input
          className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <input
          className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {error && <p className="text-xs text-red-500">{error}</p>}
        <button
          type="button"
          onClick={submit}
          disabled={busy || !email || !password}
          className="w-full rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {busy ? 'Please wait...' : mode === 'register' ? 'Create account' : 'Sign in'}
        </button>
        <button
          type="button"
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
          className="w-full text-xs text-muted-foreground"
        >
          {mode === 'login' ? 'Need an account? Register' : 'Already have an account? Sign in'}
        </button>
      </div>
    </div>
  )
}
