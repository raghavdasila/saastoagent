import { useEffect, useRef, useState } from 'react'

import { CommandComposer } from '@/components/agent/CommandComposer'
import { MessageBubble } from '@/components/agent/MessageBubble'
import { normalizeWorkspaceName, toSlug, wantsConfirm, type WorkspaceLaunchStep } from '@/lib/entryGraph'
import type { ChatUIMessage } from '@/types/agent'

interface WorkspaceLaunchPadProps {
  title?: string
  description?: string
  error?: string
  isPending: boolean
  onCreate: (body: { name: string; slug: string }) => void
}

function makeMessage(role: 'user' | 'assistant', content: string): ChatUIMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: Date.now(),
  }
}

export function WorkspaceLaunchPad({
  title = 'Launch a SaaSToAgent Operator',
  description = 'Describe the SaaS operating job this operator should own, then confirm the generated operator workspace name.',
  error,
  isPending,
  onCreate,
}: WorkspaceLaunchPadProps) {
  const [step, setStep] = useState<WorkspaceLaunchStep>('ask_job')
  const [draft, setDraft] = useState('')
  const [workspaceName, setWorkspaceName] = useState('')
  const [messages, setMessages] = useState<ChatUIMessage[]>([
    makeMessage(
      'assistant',
      'Tell me what SaaS operating job this operator should own. For example: `support escalations`, `renewal recovery`, or `billing exceptions`.',
    ),
  ])
  const lastError = useRef('')

  const appendAssistant = (content: string) => {
    setMessages((current) => [...current, makeMessage('assistant', content)])
  }

  const appendUser = (content: string) => {
    setMessages((current) => [...current, makeMessage('user', content)])
  }

  useEffect(() => {
    if (error && error !== lastError.current) {
      lastError.current = error
      appendAssistant(`${error} Reply with a better name, or type \`launch\` again if you want to retry.`)
    }
  }, [error])

  const handleSend = () => {
    const value = draft.trim()
    if (!value || isPending || step === 'done') {
      return
    }

    setDraft('')
    appendUser(value)

    if (step === 'ask_job') {
      const nextName = normalizeWorkspaceName(value)
      if (!nextName) {
        appendAssistant('I need at least a short operating job before I can derive the SaaSToAgent Operator name.')
        return
      }
      const slug = toSlug(nextName)
      setWorkspaceName(nextName)
      setStep('confirm')
      appendAssistant(`I can launch **${nextName}** at \`/${slug}\`. Type \`launch\` to create it, or reply with a better name.`)
      return
    }

    if (step === 'confirm') {
      if (wantsConfirm(value)) {
        const slug = toSlug(workspaceName)
        appendAssistant(`Launching **${workspaceName}** now.`)
        onCreate({ name: workspaceName, slug })
        return
      }

      const nextName = normalizeWorkspaceName(value)
      if (!nextName) {
        appendAssistant('That rename did not leave me with a valid operator workspace name. Try again.')
        return
      }
      const slug = toSlug(nextName)
      setWorkspaceName(nextName)
      appendAssistant(`Updated. I can launch **${nextName}** at \`/${slug}\`. Type \`launch\` to continue, or rename it again.`)
    }
  }

  return (
    <section className="surface-card rounded-3xl overflow-hidden">
      <div className="px-6 py-6 sm:px-8">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">Operator launch pad</div>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">{title}</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-400">{description}</p>
      </div>

      <div className="max-h-[24rem] overflow-y-auto border-t border-slate-200 py-2 dark:border-white/10">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>

      <div className="border-t border-slate-200 bg-white px-4 py-4 dark:border-white/10 dark:bg-[#09090b] sm:px-6">
        <CommandComposer
          value={draft}
          onChange={setDraft}
          onSend={handleSend}
          placeholder={step === 'ask_job' ? 'What job should this operator own?' : 'launch or rename'}
          disabled={isPending}
        />
      </div>
    </section>
  )
}