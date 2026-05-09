import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { CommandComposer } from '@/components/agent/CommandComposer'
import { MessageBubble } from '@/components/agent/MessageBubble'
import { ThemeToggleButton } from '@/components/theme/ThemeToggleButton'
import { useAuth } from '@/context/AuthContext'
import { detectAuthIntent, isValidEmail, OPERATOR_NAME, PRODUCT_NAME, wantsSkip, type AuthIntent, type AuthStep } from '@/lib/entryGraph'
import type { ChatUIMessage } from '@/types/agent'

interface AuthAgentDeskProps {
  initialIntent?: AuthIntent
}

function makeMessage(role: 'user' | 'assistant', content: string): ChatUIMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    timestamp: Date.now(),
  }
}

function startingMessages(intent: AuthIntent | undefined): ChatUIMessage[] {
  if (intent === 'login') {
    return [
      makeMessage(
        'assistant',
        "You're at the Corpus sign-in step now, not a settings form. We'll sign you in through conversation. Start with the email tied to your account.",
      ),
    ]
  }

  if (intent === 'register') {
    return [
      makeMessage(
        'assistant',
        "We'll create your account conversationally, then drop you into workspace setup. Tell me the name you want on the account, or type `skip` if you don't care.",
      ),
    ]
  }

  return [
    makeMessage(
      'assistant',
      'Say `sign in` or `create account` and I will collect the rest of the auth details step by step.',
    ),
  ]
}

export function AuthAgentDesk({ initialIntent }: AuthAgentDeskProps) {
  const navigate = useNavigate()
  const { login, register } = useAuth()
  const [intent, setIntent] = useState<AuthIntent | null>(initialIntent ?? null)
  const [step, setStep] = useState<AuthStep>(
    initialIntent === 'register' ? 'display_name' : initialIntent === 'login' ? 'email' : 'intent',
  )
  const [messages, setMessages] = useState<ChatUIMessage[]>(() => startingMessages(initialIntent))
  const [draft, setDraft] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const appendAssistant = (content: string) => {
    setMessages((current) => [...current, makeMessage('assistant', content)])
  }

  const appendUser = (content: string, masked = false) => {
    setMessages((current) => [...current, makeMessage('user', masked ? '••••••••' : content)])
  }

  const resetForIntent = (nextIntent: AuthIntent) => {
    setIntent(nextIntent)
    setDisplayName('')
    setEmail('')
    if (nextIntent === 'login') {
      setStep('email')
      appendAssistant('Switching to sign in. Give me the email for the account.')
      return
    }
    setStep('display_name')
    appendAssistant('Switching to registration. Tell me the display name to use, or type `skip`.')
  }

  const submit = async (password: string) => {
    if (!intent) return

    setSubmitting(true)
    appendAssistant(intent === 'login' ? 'Signing you in now.' : 'Creating the account and signing you in.')

    try {
      if (intent === 'login') {
        await login(email, password)
      } else {
        await register(email, password, displayName || undefined)
      }
      setStep('done')
      navigate('/')
    } catch (error: any) {
      setStep(intent === 'register' ? 'email' : 'email')
      appendAssistant(
        `${error?.message || 'Auth failed.'} Start again from the email address or tell me to switch flows.`,
      )
    } finally {
      setSubmitting(false)
    }
  }

  const handleSend = async () => {
    const value = draft.trim()
    if (!value || submitting || step === 'done') {
      return
    }

    setDraft('')

    const nextIntent = detectAuthIntent(value)
    if (nextIntent && nextIntent !== intent) {
      appendUser(value)
      resetForIntent(nextIntent)
      return
    }

    appendUser(value, step === 'password')

    if (step === 'intent') {
      if (!nextIntent) {
        appendAssistant('I still need either `sign in` or `create account` before I know which path to run.')
        return
      }
      resetForIntent(nextIntent)
      return
    }

    if (step === 'display_name') {
      if (wantsSkip(value)) {
        setDisplayName('')
        setStep('email')
        appendAssistant('No display name. Give me the email address for the new account.')
        return
      }
      setDisplayName(value)
      setStep('email')
      appendAssistant(`Using **${value}**. Now give me the email for the new account.`)
      return
    }

    if (step === 'email') {
      if (!isValidEmail(value)) {
        appendAssistant('That does not look like a valid email address. Try again with a full address like `you@example.com`.')
        return
      }
      setEmail(value)
      setStep('password')
      appendAssistant('Got it. Now send the password. I will mask it in the transcript.')
      return
    }

    if (step === 'password') {
      if (intent === 'register' && value.length < 8) {
        appendAssistant('Use at least 8 characters for the password, then send it again.')
        return
      }
      await submit(value)
    }
  }

  const placeholder = useMemo(() => {
    if (step === 'intent') return 'sign in or create account'
    if (step === 'display_name') return 'Display name or skip'
    if (step === 'email') return 'you@example.com'
    if (step === 'password') return 'Password'
    return 'Authenticated'
  }, [step])

  const inputType = step === 'password' ? 'password' : step === 'email' ? 'email' : 'text'

  return (
    <div className="min-h-screen bg-background px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-5xl items-center justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">{PRODUCT_NAME}</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
            Sign in through conversation
          </h1>
        </div>
        <ThemeToggleButton />
      </div>

      <div className="mx-auto mt-6 grid max-w-5xl gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="surface-card rounded-3xl overflow-hidden">
          <div className="max-h-[65vh] overflow-y-auto py-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>
          <div className="border-t border-slate-200 bg-white px-4 py-4 dark:border-white/10 dark:bg-[#09090b] sm:px-6">
            <CommandComposer
              value={draft}
              onChange={setDraft}
              onSend={() => {
                void handleSend()
              }}
              placeholder={placeholder}
              disabled={submitting || step === 'done'}
              inputType={inputType}
            />
          </div>
        </section>

        <aside className="space-y-6">
          <section className="surface-card rounded-3xl p-6 sm:p-8">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">Why this changed</div>
            <p className="mt-4 text-sm leading-7 text-slate-600 dark:text-slate-400">
              Auth is handled inside {OPERATOR_NAME} instead of a detached form. The flow collects only the next field it needs, stays in one thread, and hands you straight into workspace setup.
            </p>
          </section>

          <section className="surface-card rounded-3xl p-6 sm:p-8">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">Flow nodes</div>
            <div className="mt-4 space-y-3 text-sm leading-6 text-slate-600 dark:text-slate-400">
              <p><span className="font-semibold text-slate-950 dark:text-white">1.</span> Choose auth intent.</p>
              <p><span className="font-semibold text-slate-950 dark:text-white">2.</span> Collect only the missing identity fields.</p>
              <p><span className="font-semibold text-slate-950 dark:text-white">3.</span> Authenticate and route into workspace onboarding.</p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}
