import { useEffect, useMemo } from 'react'
import { ArrowRight, Bot, RotateCcw, Send } from 'lucide-react'

import { buildInitialAgentMessage, buildShellAgentReply } from '@/components/saasAgent/shellAgent'
import { formatSaaSAgentDisplayName } from '@/lib/entryGraph'
import { useSaaSAgentStore, type ShellMessage } from '@/stores/saasAgentStore'
import type { SaaSAgent, SaaSAgentStats } from '@/types/domain'

interface AgentChatStubProps {
  saasAgent?: SaaSAgent
  stats?: SaaSAgentStats
}

export function AgentChatStub({ saasAgent, stats }: AgentChatStubProps) {
  const saasAgentName = formatSaaSAgentDisplayName(saasAgent?.name) || 'this saasAgent'
  const saasAgentId = useSaaSAgentStore((state) => state.saasAgentId)
  const setActiveView = useSaaSAgentStore((state) => state.setActiveView)
  const setShellDraft = useSaaSAgentStore((state) => state.setShellDraft)
  const appendShellMessage = useSaaSAgentStore((state) => state.appendShellMessage)
  const clearShellMessages = useSaaSAgentStore((state) => state.clearShellMessages)
  const draft = useSaaSAgentStore((state) => (saasAgentId ? state.shellDraftBySaaSAgent[saasAgentId] || '' : ''))
  const storedMessages = useSaaSAgentStore((state) =>
    saasAgentId ? state.shellMessagesBySaaSAgent[saasAgentId] || [] : [],
  )

  const starterPrompts = useMemo(
    () => [
      'Connect HubSpot so you can manage support work for me.',
      'What will you be able to do once this saasAgent is connected?',
      'How will you catch failures and learn over time?',
    ],
    [],
  )

  useEffect(() => {
    if (!saasAgentId || storedMessages.length > 0) {
      return
    }

    appendShellMessage(saasAgentId, {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: buildInitialAgentMessage(saasAgent, stats),
      createdAt: Date.now(),
    })
  }, [appendShellMessage, stats, storedMessages.length, saasAgent, saasAgentId])

  const sendMessage = (content: string) => {
    if (!saasAgentId) {
      return
    }

    const trimmed = content.trim()
    if (!trimmed) {
      return
    }

    const now = Date.now()
    const userMessage: ShellMessage = {
      id: `user-${now}`,
      role: 'user',
      content: trimmed,
      createdAt: now,
    }
    const assistantMessage: ShellMessage = {
      id: `assistant-${now + 1}`,
      role: 'assistant',
      content: buildShellAgentReply(trimmed, saasAgent, stats),
      createdAt: now + 1,
    }

    appendShellMessage(saasAgentId, userMessage)
    appendShellMessage(saasAgentId, assistantMessage)
    setShellDraft(saasAgentId, '')
  }

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] flex-col bg-slate-50 dark:bg-background">
      <div className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-6">
          <section className="surface-card rounded-lg p-6 sm:p-8">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">Agent saasAgent</div>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
                  {saasAgentName}
                </h1>
                <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600 dark:text-slate-400">
                  Start from the outcome you want. The agent uses this conversation as the control surface for planning, action selection, execution, and later QA.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  className="surface-outline-button inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium"
                  onClick={() => setActiveView('connect')}
                  type="button"
                >
                  Open setup
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </button>
                {saasAgentId && (
                  <button
                    className="surface-outline-button inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium"
                    onClick={() => clearShellMessages(saasAgentId)}
                    type="button"
                  >
                    Reset thread
                    <RotateCcw className="h-4 w-4" aria-hidden="true" />
                  </button>
                )}
              </div>
            </div>
          </section>

          <section className="surface-card rounded-lg p-4 sm:p-5">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-400">
              <Bot className="h-4 w-4 text-sky-600" aria-hidden="true" />
              Agent thread
            </div>

            <div className="mt-4 space-y-4">
              {storedMessages.map((message) => (
                <div
                  key={message.id}
                  className={[
                    'flex',
                    message.role === 'user' ? 'justify-end' : 'justify-start',
                  ].join(' ')}
                >
                  <div
                    className={[
                      'max-w-3xl whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-7 shadow-sm',
                      message.role === 'user'
                        ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
                        : 'border border-slate-200 bg-slate-50 text-slate-700 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200',
                    ].join(' ')}
                  >
                    {message.content}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {starterPrompts.map((prompt) => (
                <button
                  key={prompt}
                  className="surface-outline-button rounded-full px-3 py-1.5 text-sm hover:border-sky-300 dark:hover:border-white/20 dark:hover:text-white"
                  onClick={() => sendMessage(prompt)}
                  type="button"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </section>
        </div>
      </div>

      <div className="border-t border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#09090b] sm:px-6 lg:px-8">
        <div className="surface-muted mx-auto flex max-w-6xl items-center gap-3 rounded-lg px-3 py-2">
          <input
            className="min-w-0 flex-1 bg-transparent px-1 py-2 text-sm text-slate-700 outline-none placeholder:text-slate-500 dark:text-slate-100 dark:placeholder:text-slate-500"
            value={draft}
            onChange={(event) => saasAgentId && setShellDraft(saasAgentId, event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                sendMessage(draft)
              }
            }}
            placeholder="Tell your agent what you want done"
            type="text"
          />
          <button
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-950 text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200 dark:disabled:bg-white/10 dark:disabled:text-slate-500"
            disabled={!draft.trim()}
            onClick={() => sendMessage(draft)}
            title="Send"
            type="button"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}
