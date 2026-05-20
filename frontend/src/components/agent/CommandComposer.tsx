import { type KeyboardEvent, useEffect, useRef } from 'react'
import { ArrowUp } from 'lucide-react'

import { cn } from '@/lib/cn'

interface CommandComposerProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  placeholder?: string
  disabled?: boolean
  inputType?: 'text' | 'email' | 'password'
}

export function CommandComposer({
  value,
  onChange,
  onSend,
  placeholder,
  disabled = false,
  inputType = 'text',
}: CommandComposerProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus()
    }
  }, [disabled])

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      onSend()
      window.setTimeout(() => inputRef.current?.focus(), 0)
    }
  }

  return (
    <div className="flex items-center gap-2 rounded-full border border-border/30 bg-muted p-2 shadow-inner transition-shadow duration-200 focus-within:shadow-[0_0_0_3px_hsl(var(--ring)/0.18),inset_0_1px_2px_hsl(var(--foreground)/0.08)] dark:border-white/10">
      <input
        ref={inputRef}
        type={inputType}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          'corpus-command-input min-w-0 flex-1 bg-transparent px-4 py-2 text-sm text-foreground outline-none focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0',
          'placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50',
        )}
        data-testid="corpus-command-input"
      />
      <button
        type="button"
        onClick={() => {
          onSend()
          window.setTimeout(() => inputRef.current?.focus(), 0)
        }}
        disabled={disabled || !value.trim()}
        className="flex h-11 w-11 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-sm transition-all duration-300 hover:bg-primary/90 hover:shadow-md active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
        title="Send"
        data-testid="corpus-command-send"
      >
        <ArrowUp className="h-4 w-4" />
      </button>
    </div>
  )
}
