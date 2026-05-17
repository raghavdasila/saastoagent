import { useEffect, useRef, useState } from 'react'

import { CommandComposer } from '@/components/agent/CommandComposer'
import { MessageBubble } from '@/components/agent/MessageBubble'
import { normalizeSaaSAgentName, toSlug, wantsConfirm, type SaaSAgentLaunchStep } from '@/lib/entryGraph'
import type { ChatUIMessage } from '@/types/agent'

interface SaaSAgentLaunchPadProps {
  title?: string
  description?: string
  error?: string
  isPending: boolean
  presets?: Array<{ name: string; slug: string; description: string }>
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

export function SaaSAgentLaunchPad({
  title = 'Launch a SaaS Agent',
  description = 'Configure the SaaS Agent name and slug, then add API schema connections.',
  error,
  isPending,
  presets = [],
  onCreate,
}: SaaSAgentLaunchPadProps) {
  const [step, setStep] = useState<SaaSAgentLaunchStep>('ask_job')
  const [draft, setDraft] = useState('')
  const [saasAgentName, setSaaSAgentName] = useState('')
  const [saasAgentSlug, setSaaSAgentSlug] = useState('')
  const [messages, setMessages] = useState<ChatUIMessage[]>([
    makeMessage(
      'assistant',
      'What should this SaaS Agent be called? You can edit the slug before launch.',
    ),
  ])
  const lastError = useRef('')

  const appendAssistant = (content: string) => {
    setMessages((current) => [...current, makeMessage('assistant', content)])
  }

  const appendUser = (content: string) => {
    setMessages((current) => [...current, makeMessage('user', content)])
  }

  const applyPreset = (preset: { name: string; slug: string; description: string }) => {
    setSaaSAgentName(preset.name)
    setSaaSAgentSlug(preset.slug)
    setStep('confirm')
    appendAssistant(`Configured **${preset.name}** at \`/${preset.slug}\`. Type \`launch\` to create it, or edit the name and slug first.`)
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
      const nextName = normalizeSaaSAgentName(value)
      if (!nextName) {
        appendAssistant('I need a saasAgent name before I can create it.')
        return
      }
      const slug = toSlug(nextName)
      setSaaSAgentName(nextName)
      setSaaSAgentSlug(slug)
      setStep('confirm')
      appendAssistant(`I can launch **${nextName}** at \`/${slug}\`. Type \`launch\` to create it, or reply with a better name.`)
      return
    }

    if (step === 'confirm') {
      if (wantsConfirm(value)) {
        const slug = toSlug(saasAgentSlug || saasAgentName)
        appendAssistant(`Launching **${saasAgentName}** now.`)
        onCreate({ name: saasAgentName, slug })
        return
      }

      const nextName = normalizeSaaSAgentName(value)
      if (!nextName) {
        appendAssistant('That rename did not leave me with a valid saasAgent name. Try again.')
        return
      }
      const slug = toSlug(nextName)
      setSaaSAgentName(nextName)
      setSaaSAgentSlug(slug)
      appendAssistant(`Updated. I can launch **${nextName}** at \`/${slug}\`. Type \`launch\` to continue, or rename it again.`)
    }
  }

  return (
    <section className="surface-card rounded-3xl overflow-hidden">
      <div className="px-6 py-6 sm:px-8">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">SaaS Agent launch pad</div>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">{title}</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-400">{description}</p>
      </div>

      <div className="max-h-[24rem] overflow-y-auto border-t border-slate-200 py-2 dark:border-white/10">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>

      <div className="border-t border-slate-200 bg-white px-4 py-4 dark:border-white/10 dark:bg-[#09090b] sm:px-6">
        {presets.length > 0 && step === 'ask_job' && (
          <div className="mb-3 flex flex-wrap gap-2">
            {presets.map((preset) => (
              <button
                key={preset.slug}
                type="button"
                onClick={() => applyPreset(preset)}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-300"
                title={preset.description}
              >
                {preset.name}
              </button>
            ))}
          </div>
        )}
        {step === 'confirm' && (
          <div className="mb-3 grid gap-3 sm:grid-cols-2">
            <label className="space-y-1 text-xs font-medium text-slate-600 dark:text-slate-300">
              <span>Name</span>
              <input
                value={saasAgentName}
                onChange={(event) => {
                  setSaaSAgentName(event.target.value)
                  setSaaSAgentSlug(toSlug(event.target.value))
                }}
                className="h-9 w-full rounded-md border border-slate-200 bg-white px-2 text-sm text-slate-950 outline-none focus:border-sky-400 dark:border-white/10 dark:bg-[#050506] dark:text-white"
              />
            </label>
            <label className="space-y-1 text-xs font-medium text-slate-600 dark:text-slate-300">
              <span>Slug</span>
              <input
                value={saasAgentSlug}
                onChange={(event) => setSaaSAgentSlug(toSlug(event.target.value))}
                className="h-9 w-full rounded-md border border-slate-200 bg-white px-2 text-sm text-slate-950 outline-none focus:border-sky-400 dark:border-white/10 dark:bg-[#050506] dark:text-white"
              />
            </label>
          </div>
        )}
        <CommandComposer
          value={draft}
          onChange={setDraft}
          onSend={handleSend}
          placeholder={step === 'ask_job' ? 'SaaS Agent name' : 'launch or rename'}
          disabled={isPending}
        />
      </div>
    </section>
  )
}
