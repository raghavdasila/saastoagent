import { useState } from 'react'
import { BookOpen, ChevronDown, ChevronRight } from 'lucide-react'

import type { SourceCitation } from '@/types/agent'

interface Props {
  sources: SourceCitation[]
}

export function SourceCitations({ sources }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="w-full">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        <BookOpen className="h-3 w-3" />
        <span>{sources.length} source(s)</span>
      </button>

      {isOpen && (
        <div className="mt-1.5 space-y-1.5">
          {sources.map((source, i) => (
            <div
              key={i}
              className="rounded-lg border border-border bg-background/50 px-3 py-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">{source.title}</span>
                <span className="text-muted-foreground">
                  {(source.score * 100).toFixed(0)}% relevant
                </span>
              </div>
              <p className="mt-1 text-muted-foreground line-clamp-2">{source.chunk}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
