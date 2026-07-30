import { Input } from "@/components/ui/input"
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { STUDIO_CONFIG } from "@/workbench/studioConfig"
import type { DesignStory } from "@/workbench/types"

interface StoryEditorProps {
  story: DesignStory
  disabled: boolean
  onChange: (patch: Partial<DesignStory>) => void
}

export function StoryEditor({ story, disabled, onChange }: StoryEditorProps) {
  return (
    <section aria-labelledby="story-heading" className="pb-5">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <span>{STUDIO_CONFIG.views.behavior.label}</span>
            <span aria-hidden="true">·</span>
            <span className={cn(
              story.status === "approved" && "text-[var(--studio-success)]",
              story.status === "rejected" && "text-destructive",
            )}>
              {story.status[0].toUpperCase() + story.status.slice(1)}
            </span>
          </div>
          <h2 id="story-heading" className="mt-1 truncate text-xl font-semibold tracking-[-0.025em]">{story.title}</h2>
        </div>
        <span className="shrink-0 rounded-full border border-primary/35 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          {STUDIO_CONFIG.views.behavior.objectType}
        </span>
      </div>

      <FieldGroup className="gap-4">
        <Field>
          <FieldLabel htmlFor="story-title">Title</FieldLabel>
          <Input id="story-title" value={story.title} disabled={disabled} onChange={(event) => onChange({ title: event.target.value })} />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
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
          <FieldLabel htmlFor="expected-behavior">Expected behavior</FieldLabel>
          <Textarea
            id="expected-behavior"
            className="min-h-20"
            placeholder="Observable Corpus response and completion state"
            value={story.expectedBehavior}
            disabled={disabled}
            onChange={(event) => onChange({ expectedBehavior: event.target.value })}
          />
          <FieldDescription className="text-xs">What Corpus visibly does, including material constraints and the completion state.</FieldDescription>
        </Field>
      </FieldGroup>
    </section>
  )
}
