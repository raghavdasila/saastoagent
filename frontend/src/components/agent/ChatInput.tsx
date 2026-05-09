import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { Paperclip, Send } from 'lucide-react'

import { cn } from '@/lib/cn'

interface Props {
  onSend: (message: string) => void
  onFileUpload?: (file: File) => void
  disabled?: boolean
  placeholder?: string
  injectText?: string
}

export function ChatInput({
  onSend,
  onFileUpload,
  disabled = false,
  placeholder = 'Type a message...',
  injectText,
}: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (injectText !== undefined && injectText !== '') {
      setValue(injectText)
      setTimeout(() => {
        const el = textareaRef.current
        if (el) {
          el.focus()
          el.setSelectionRange(injectText.length, injectText.length)
        }
      }, 0)
    }
  }, [injectText])

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, disabled, onSend])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`
    }
  }

  return (
    <div className="flex items-end gap-2">
      {onFileUpload && (
        <>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            title="Upload document"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border text-muted-foreground transition hover:bg-accent disabled:opacity-50"
          >
            <Paperclip className="h-4 w-4" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md,.csv,.markdown"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file && onFileUpload) onFileUpload(file)
              e.target.value = ''
            }}
            className="hidden"
          />
        </>
      )}

      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className={cn(
          'flex-1 resize-none rounded-xl border border-input bg-background px-4 py-3',
          'text-sm placeholder:text-muted-foreground',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'max-h-[200px] min-h-[44px]',
        )}
      />

      <button
        type="button"
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        title="Send message"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Send className="h-4 w-4" />
      </button>
    </div>
  )
}
