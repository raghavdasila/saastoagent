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
    <div className="flex items-center gap-2 rounded-2xl border border-border bg-background p-2 shadow-sm">
      <input
        ref={inputRef}
        type={inputType}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          'min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-foreground outline-none',
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
        className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        title="Send"
        data-testid="corpus-command-send"
      >
        <ArrowUp className="h-4 w-4" />
      </button>
    </div>
  )
}
