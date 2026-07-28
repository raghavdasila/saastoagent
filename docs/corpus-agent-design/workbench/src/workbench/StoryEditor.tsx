import { Input } from "@/components/ui/input"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Textarea } from "@/components/ui/textarea"
import type { DesignStory } from "@/workbench/types"

interface StoryEditorProps {
  story: DesignStory
  disabled: boolean
  onChange: (patch: Partial<DesignStory>) => void
}

export function StoryEditor({ story, disabled, onChange }: StoryEditorProps) {
  return (
    <section aria-labelledby="story-heading" className="flex flex-col gap-4">
      <div>
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">User story</p>
          {story.status === "draft" && <span className="rounded-full bg-muted px-2 py-1 text-xs font-medium text-muted-foreground">Draft</span>}
        </div>
        <h2 id="story-heading" className="mt-1 text-xl font-semibold tracking-tight">{story.title}</h2>
      </div>

      <FieldGroup className="gap-4">
        <Field>
          <FieldLabel htmlFor="story-title">Title</FieldLabel>
          <Input id="story-title" value={story.title} disabled={disabled} onChange={(event) => onChange({ title: event.target.value })} />
        </Field>
        <Field>
          <FieldLabel htmlFor="story-body">User story</FieldLabel>
          <Textarea
            id="story-body"
            className="min-h-28"
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
