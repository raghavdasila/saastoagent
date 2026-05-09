import { useCallback, useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bot, Plus, RotateCcw, Trash2 } from 'lucide-react'

import { ChatInput } from '@/components/agent/ChatInput'
import { MessageBubble } from '@/components/agent/MessageBubble'
import { useSSEChat } from '@/hooks/useSSEChat'
import { api, ApiError } from '@/lib/api'
import { formatWorkspaceDisplayName, OPERATOR_NAME } from '@/lib/entryGraph'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import type {
  AgentDocument,
  AgentMessageRow,
  AgentSession,
  ChatUIMessage,
} from '@/types/agent'
import type { Workspace } from '@/types/domain'

const STARTER_PROMPTS = [
  'Map the SaaS operating workflow you should own in this workspace.',
  'Summarise the documents I uploaded and turn them into operator guidance.',
  'What can this workspace do right now, and what is still missing?',
]

interface AgentChatProps {
  workspace?: Workspace
}

export function AgentChat({ workspace }: AgentChatProps) {
  const workspaceId = useWorkspaceStore((state) => state.workspaceId)
  const setActiveView = useWorkspaceStore((state) => state.setActiveView)
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [injectText, setInjectText] = useState('')

  const {
    messages,
    isStreaming,
    sessionId,
    sendMessage,
    clearMessages,
    setMessages,
    setSessionId,
  } = useSSEChat({
    workspaceId,
    onError: setError,
  })

  // Sessions list (sidebar)
  const { data: sessionsData } = useQuery({
    queryKey: ['agent-sessions', workspaceId],
    queryFn: () =>
      api.get<{ sessions: AgentSession[]; total: number }>(
        `/workspaces/${workspaceId}/agent/sessions`,
      ),
    enabled: !!workspaceId,
  })

  // Refetch when stream finishes (new session may have been created)
  useEffect(() => {
    if (!isStreaming && sessionId) {
      queryClient.invalidateQueries({ queryKey: ['agent-sessions', workspaceId] })
    }
  }, [isStreaming, sessionId, workspaceId, queryClient])

  // Load history when picking an existing session
  const loadSession = useCallback(
    async (sid: string) => {
      if (!workspaceId) return
      try {
        const rows = await api.get<AgentMessageRow[]>(
          `/workspaces/${workspaceId}/agent/sessions/${sid}/messages`,
        )
        const ui: ChatUIMessage[] = rows.map((r) => ({
          id: r.id,
          role: r.role === 'user' ? 'user' : 'assistant',
          content: r.content,
          timestamp: new Date(r.created_at).getTime(),
          thinking: r.thinking ?? undefined,
          toolCalls: undefined,
          sources: r.sources?.map((s) => ({
            title: (s as Record<string, unknown>).title as string ?? '',
            chunk: (s as Record<string, unknown>).chunk as string ?? '',
            score: ((s as Record<string, unknown>).score as number) ?? 0,
            documentId: ((s as Record<string, unknown>).document_id as string) ?? '',
          })),
          followUps: r.follow_ups ?? undefined,
        }))
        setMessages(ui)
        setSessionId(sid)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load session')
      }
    },
    [workspaceId, setMessages, setSessionId],
  )

  const deleteSession = useMutation({
    mutationFn: (sid: string) =>
      api.delete<{ status: string }>(`/workspaces/${workspaceId}/agent/sessions/${sid}`),
    onSuccess: (_, sid) => {
      queryClient.invalidateQueries({ queryKey: ['agent-sessions', workspaceId] })
      if (sid === sessionId) {
        clearMessages()
      }
    },
  })

  const uploadFile = useMutation({
    mutationFn: (file: File) =>
      api.upload<AgentDocument>(`/workspaces/${workspaceId}/agent/documents`, file),
    onSuccess: (doc) => {
      queryClient.invalidateQueries({ queryKey: ['agent-documents', workspaceId] })
      setInjectText(`Tell me what's in ${doc.original_name}`)
    },
    onError: (e) => {
      setError(e instanceof ApiError ? e.message : 'Upload failed')
    },
  })

  const sessions = sessionsData?.sessions ?? []
  const workspaceName = formatWorkspaceDisplayName(workspace?.name) || 'this workspace'
  const operatorTitle = OPERATOR_NAME

  const handleSend = (text: string) => {
    setError(null)
    sendMessage(text, sessionId)
  }

  const handleNewChat = () => {
    clearMessages()
  }

  const showStarter = useMemo(() => messages.length === 0 && !isStreaming, [messages, isStreaming])

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] bg-slate-50 dark:bg-background">
      {/* Sidebar: sessions */}
      <aside className="hidden w-72 shrink-0 border-r border-slate-200 bg-white p-3 dark:border-white/10 dark:bg-[#0a0a0b] lg:flex lg:flex-col">
        <button
          type="button"
          onClick={handleNewChat}
          className="surface-outline-button flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium"
        >
          <Plus className="h-4 w-4" />
          New chat
        </button>
        <div className="mt-4 flex-1 overflow-y-auto">
          <div className="px-1 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Recent sessions
          </div>
          <ul className="mt-2 space-y-1">
            {sessions.length === 0 && (
              <li className="px-2 py-3 text-xs text-slate-500">No conversations yet.</li>
            )}
            {sessions.map((s) => {
              const active = s.id === sessionId
              return (
                <li key={s.id}>
                  <div
                    className={[
                      'group flex items-center gap-2 rounded-md px-2 py-1.5 text-sm cursor-pointer',
                      active
                        ? 'bg-slate-100 text-slate-900 dark:bg-white/[0.08] dark:text-white'
                        : 'text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-white/[0.04]',
                    ].join(' ')}
                  >
                    <button
                      type="button"
                      onClick={() => loadSession(s.id)}
                      className="flex-1 truncate text-left"
                    >
                      {s.title || 'Untitled'}
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm('Delete this conversation?')) {
                          deleteSession.mutate(s.id)
                        }
                      }}
                      className="opacity-0 transition group-hover:opacity-100"
                      title="Delete"
                    >
                      <Trash2 className="h-3.5 w-3.5 text-slate-400 hover:text-red-500" />
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      </aside>

      {/* Main pane */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <div className="border-b border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#09090b] sm:px-6">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-sky-600" />
              <div>
                <h1 className="text-lg font-semibold text-slate-900 dark:text-white">{operatorTitle}</h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">{workspaceName}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActiveView('attachments')}
                className="surface-outline-button rounded-md px-3 py-1.5 text-xs"
              >
                Attachments
              </button>
              <button
                type="button"
                onClick={handleNewChat}
                title="Reset thread"
                className="surface-outline-button inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {showStarter ? (
            <div className="mx-auto flex max-w-3xl flex-col items-center justify-center px-6 py-16 text-center">
              <Bot className="h-10 w-10 text-sky-500" />
              <h2 className="mt-4 text-2xl font-semibold text-slate-900 dark:text-white">
                Direct the operator in {workspaceName}
              </h2>
              <p className="mt-2 max-w-lg text-sm text-slate-600 dark:text-slate-400">
                The operator can reason over uploaded documents, persistent memory, and bound tools. Try one of these to start:
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {STARTER_PROMPTS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => handleSend(p)}
                    className="surface-outline-button rounded-full px-3 py-1.5 text-xs"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-4xl py-4">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} onFollowUp={(q) => setInjectText(q)} />
              ))}
            </div>
          )}
        </div>

        {/* Composer */}
        <div className="border-t border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#09090b] sm:px-6">
          {error && (
            <div className="mx-auto mb-2 max-w-4xl rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
              {error}
            </div>
          )}
          {uploadFile.isPending && (
            <div className="mx-auto mb-2 max-w-4xl text-xs text-slate-500">Uploading…</div>
          )}
          <div className="mx-auto max-w-4xl">
            <ChatInput
              onSend={handleSend}
              onFileUpload={(file) => uploadFile.mutate(file)}
              disabled={isStreaming || !workspaceId}
              placeholder="Describe what you need done"
              injectText={injectText}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
