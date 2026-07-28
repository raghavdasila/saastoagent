import { Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Field, FieldLabel } from "@/components/ui/field"
import { Textarea } from "@/components/ui/textarea"
import type { ChatActor, MockChatMessage } from "@/workbench/types"

interface MockChatEditorProps {
  messages: MockChatMessage[]
  disabled: boolean
  onChange: (messages: MockChatMessage[]) => void
}

export function MockChatEditor({ messages, disabled, onChange }: MockChatEditorProps) {
  function addMessage(actor: ChatActor) {
    onChange([...messages, { id: `${actor.toLowerCase()}-${Date.now()}`, actor, content: "" }])
  }

  return (
    <section aria-labelledby="mock-chat-heading" className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="mock-chat-heading" className="text-sm font-semibold">Mock conversation</h2>
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" disabled={disabled} onClick={() => addMessage("Corpus")}>
            <Plus data-icon="inline-start" /> Corpus
          </Button>
          <Button size="sm" variant="ghost" disabled={disabled} onClick={() => addMessage("Owner")}>
            <Plus data-icon="inline-start" /> Owner
          </Button>
        </div>
      </div>

      <div className="flex flex-col divide-y divide-border border-y border-border">
        {messages.map((message, index) => (
          <div key={message.id} className="py-2">
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className="text-xs font-semibold text-muted-foreground">{message.actor}</span>
              <Button
                size="icon-xs"
                variant="ghost"
                disabled={disabled}
                aria-label={`Remove ${message.actor} message ${index + 1}`}
                onClick={() => onChange(messages.filter((item) => item.id !== message.id))}
              >
                <Trash2 />
              </Button>
            </div>
            <Field>
              <FieldLabel className="sr-only" htmlFor={`message-${message.id}`}>{message.actor} message {index + 1}</FieldLabel>
              <Textarea
                id={`message-${message.id}`}
                className="min-h-14 bg-transparent"
                value={message.content}
                disabled={disabled}
                onChange={(event) => onChange(messages.map((item) => item.id === message.id ? { ...item, content: event.target.value } : item))}
              />
            </Field>
          </div>
        ))}
      </div>
    </section>
  )
}
