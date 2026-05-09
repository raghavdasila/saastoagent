import { MessageSquare } from 'lucide-react'

interface Props {
  questions: string[]
  onSelect?: (question: string) => void
}

export function FollowUpChips({ questions, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2 mt-1">
      {questions.map((q, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onSelect?.(q)}
          className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
        >
          <MessageSquare className="h-3 w-3" />
          {q}
        </button>
      ))}
    </div>
  )
}
