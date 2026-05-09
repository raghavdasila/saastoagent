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
      <div className="flex items-center gap-2 py-1">
        <Brain className="h-4 w-4 text-muted-foreground animate-pulse" />
        <span className="text-sm text-muted-foreground">Thinking</span>
        <div className="flex gap-1">
          <span className="thinking-dot" />
          <span className="thinking-dot" />
          <span className="thinking-dot" />
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
