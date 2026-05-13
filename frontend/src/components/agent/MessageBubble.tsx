import { Bot, User } from 'lucide-react'

import { cn } from '@/lib/cn'
import type { ChatUIMessage } from '@/types/agent'

import { CollapsibleMarkdown } from './CollapsibleMarkdown'
import { FollowUpChips } from './FollowUpChips'
import { SourceCitations } from './SourceCitations'
import { ThinkingIndicator } from './ThinkingIndicator'
import { ToolCard } from './ToolCard'

interface Props {
  message: ChatUIMessage
  onFollowUp?: (question: string) => void
}

export function MessageBubble({ message, onFollowUp }: Props) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn('flex gap-3 px-4 py-3', isUser && 'flex-row-reverse')}
      data-testid="message-bubble"
      data-message-role={message.role}
    >
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground',
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={cn('flex max-w-[75%] flex-col gap-2', isUser && 'items-end')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-2.5',
            isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground',
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap text-sm">{message.content}</p>
          ) : (
            <>
              {message.isStreaming && !message.content && (
                <ThinkingIndicator thinking={message.thinking} />
              )}

              {!message.isStreaming && message.thinking && (
                <ThinkingIndicator thinking={message.thinking} collapsed />
              )}

              {message.toolCalls && message.toolCalls.length > 0 && (
                <div className="mb-2 space-y-1.5">
                  {message.toolCalls.map((tc) => (
                    <ToolCard key={tc.callId} toolCall={tc} />
                  ))}
                </div>
              )}

              {message.content && (
                <CollapsibleMarkdown content={message.content} forcePlain={message.isStreaming} />
              )}
            </>
          )}
        </div>

        {message.sources && message.sources.length > 0 && (
          <SourceCitations sources={message.sources} />
        )}

        {!message.isStreaming && message.followUps && message.followUps.length > 0 && (
          <FollowUpChips questions={message.followUps} onSelect={onFollowUp} />
        )}

        <span className="text-xs text-muted-foreground">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
    </div>
  )
}
