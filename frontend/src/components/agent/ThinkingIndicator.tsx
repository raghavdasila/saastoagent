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
      <div className="flex items-center gap-1.5 py-1" aria-label="Corpus is responding">
        <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/70 [animation-delay:-0.2s]" />
        <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/70 [animation-delay:-0.1s]" />
        <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/70" />
        <div className="ml-1 h-px w-8 overflow-hidden rounded-full bg-muted-foreground/20">
          <div className="h-full w-1/2 animate-pulse rounded-full bg-muted-foreground/60" />
        </div>
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
