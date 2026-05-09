import { useState } from 'react'
import { ChevronDown, ChevronRight, Loader2, Wrench } from 'lucide-react'

import type { ToolCallState } from '@/types/agent'

interface Props {
  toolCall: ToolCallState
}

export function ToolCard({ toolCall }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  const inputSummary = Object.entries(toolCall.inputs)
    .map(([k, v]) => `${k}: ${typeof v === 'string' ? v : JSON.stringify(v)}`)
    .join(', ')

  return (
    <div className="rounded-lg border border-border bg-background/50 text-xs">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center gap-2 px-3 py-2 hover:bg-accent/50 transition-colors"
      >
        {toolCall.isRunning ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
        ) : (
          <Wrench className="h-3.5 w-3.5 text-muted-foreground" />
        )}
        <span className="font-medium">{toolCall.toolName}</span>
        {inputSummary && (
          <span className="truncate text-muted-foreground ml-1">({inputSummary})</span>
        )}
        <span className="ml-auto">
          {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        </span>
      </button>

      {isOpen && (
        <div className="border-t border-border px-3 py-2 space-y-2">
          <div>
            <span className="font-medium text-muted-foreground">Inputs:</span>
            <pre className="mt-1 rounded bg-muted p-2 overflow-x-auto">
              {JSON.stringify(toolCall.inputs, null, 2)}
            </pre>
          </div>
          {toolCall.output && (
            <div>
              <span className="font-medium text-muted-foreground">Output:</span>
              <pre className="mt-1 rounded bg-muted p-2 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                {toolCall.output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
