import { Input } from "@/components/ui/input"
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Textarea } from "@/components/ui/textarea"
import type { DesignStory } from "@/workbench/types"

interface StoryEditorProps {
  story: DesignStory
  disabled: boolean
  onChange: (patch: Partial<DesignStory>) => void
}

export function StoryEditor({ story, disabled, onChange }: StoryEditorProps) {
  return (
    <section aria-labelledby="story-heading" className="flex flex-col gap-3">
      <div>
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold text-muted-foreground">Behavior</p>
          {story.status === "draft" && <span className="text-xs font-medium text-muted-foreground">Draft</span>}
        </div>
        <h2 id="story-heading" className="mt-0.5 text-lg font-semibold tracking-tight">{story.title}</h2>
      </div>

      <FieldGroup className="gap-3">
        <Field>
          <FieldLabel htmlFor="story-title">Title</FieldLabel>
          <Input id="story-title" value={story.title} disabled={disabled} onChange={(event) => onChange({ title: event.target.value })} />
        </Field>
        <div className="grid gap-3 border-y border-border py-3 sm:grid-cols-2">
          <Field>
            <FieldLabel htmlFor="user-intent">User intent</FieldLabel>
            <Textarea
              id="user-intent"
              className="min-h-14"
              placeholder="Meaning Corpus should recognize"
              value={story.userIntent}
              disabled={disabled}
              onChange={(event) => onChange({ userIntent: event.target.value })}
            />
            <FieldDescription className="text-xs">The user meaning Corpus should recognize.</FieldDescription>
          </Field>
          <Field>
            <FieldLabel htmlFor="agent-intent">Agent intent</FieldLabel>
            <Textarea
              id="agent-intent"
              className="min-h-14"
              placeholder="Outcome Corpus is responsible for producing"
              value={story.agentIntent}
              disabled={disabled}
              onChange={(event) => onChange({ agentIntent: event.target.value })}
            />
            <FieldDescription className="text-xs">The outcome Corpus is responsible for producing.</FieldDescription>
          </Field>
        </div>
        <Field>
          <FieldLabel htmlFor="story-body">User story</FieldLabel>
          <Textarea
            id="story-body"
            className="min-h-20"
            placeholder="As an owner, I want… so that…"
            value={story.story}
            disabled={disabled}
            onChange={(event) => onChange({ story: event.target.value })}
          />
        </Field>
      </FieldGroup>
    </section>
  )
}
