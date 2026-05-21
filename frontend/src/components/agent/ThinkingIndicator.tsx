import { useState } from 'react'
import { Brain, ChevronDown, ChevronRight } from 'lucide-react'

import { cn } from '@/lib/cn'

interface Props {
  thinking?: string
  collapsed?: boolean
}

export function ThinkingIndicator({ thinking, collapsed = false }: Props) {
  const [isOpen, setIsOpen] = useState(!collapsed)

  if (!thinking) {
    return (
      <div
        className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/60 px-2.5 py-1.5 text-xs text-muted-foreground shadow-sm"
        aria-label="Corpus is thinking"
      >
        <span className="corpus-thinking-orb" aria-hidden="true">
          <span />
        </span>
        <span>Thinking</span>
      </div>
    )
  }

  return (
    <div className="mb-2">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        <Brain className="h-3 w-3" />
        <span>Reasoning</span>
      </button>
      {isOpen && (
        <div
          className={cn(
            'mt-1.5 rounded-lg bg-background/50 border border-border p-3',
            'text-xs text-muted-foreground whitespace-pre-wrap max-h-48 overflow-y-auto',
          )}
        >
          {thinking}
        </div>
      )}
    </div>
  )
}
