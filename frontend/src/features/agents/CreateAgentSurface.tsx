import { useState, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { ArrowLeft, Bot, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { AgentStore } from "./store";
import { completedOutcome } from "@/shared/routedeck/operationResult";

export function CreateAgentSurface({
  dispatchAffordance,
  props: surfaceProps,
  store,
}: RouteDeckSurfaceComponentProps & { store: AgentStore }) {
  const draft = useSyncExternalStore(store.subscribe, store.createDraft);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pendingSourceName = typeof surfaceProps.pending_source_display_name === "string"
    ? surfaceProps.pending_source_display_name
    : null;
  const pendingSourceRevisionId = typeof surfaceProps.pending_source_revision_id === "string"
    ? surfaceProps.pending_source_revision_id
    : null;

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      const result = await dispatchAffordance("create_agent", {
        name: String(values.get("name") ?? "").trim(),
        description: String(values.get("description") ?? "").trim(),
        instructions: String(values.get("instructions") ?? "").trim(),
      });
      const failure = completedOutcome(result, "created");
      if (failure !== null) {
        setError(failure);
        setBusy(false);
      } else {
        store.clearCreateDraft();
        await store.refresh();
      }
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(false);
    }
  }

  async function cancel() {
    setBusy(true);
    setError(null);
    try {
      const result = await dispatchAffordance("cancel_create", {});
      const failure = completedOutcome(result, "opened");
      if (failure !== null) {
        setError(failure);
        setBusy(false);
      } else {
        store.clearCreateDraft();
      }
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(false);
    }
  }

  return (
    <section className="agent-create" aria-labelledby="agent-create-title">
      <header className="agents-heading">
        <div>
          <p>Agents</p>
          <h1 id="agent-create-title">Create an agent</h1>
          <span>The initial configuration is retained as immutable version 1.</span>
        </div>
        <Button type="button" variant="outline" disabled={busy} onClick={() => void cancel()}>
          <ArrowLeft data-icon="inline-start" />Cancel
        </Button>
      </header>
      {error === null ? null : <p className="agents-error" role="alert">{error}</p>}
      {pendingSourceName === null || pendingSourceRevisionId === null ? null : (
        <div className="agent-pending-source" role="status">
          <div><p>After creation</p><strong>{pendingSourceName}</strong></div>
          <span>API version <code>{pendingSourceRevisionId}</code> will remain ready to attach.</span>
        </div>
      )}
      <form onSubmit={(event) => void create(event)}>
        <Bot aria-hidden="true" className="agent-create-icon" />
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="agent-create-name">Name</FieldLabel>
            <Input id="agent-create-name" name="name" required maxLength={120} value={draft.name} placeholder="Research Agent" onInput={(event) => {
              const next = event.currentTarget.value;
              store.updateCreateDraft({ name: next });
            }} />
          </Field>
          <Field>
            <FieldLabel htmlFor="agent-create-description">Description</FieldLabel>
            <Input id="agent-create-description" name="description" maxLength={500} value={draft.description} placeholder="What this agent is responsible for" onInput={(event) => {
              const next = event.currentTarget.value;
              store.updateCreateDraft({ description: next });
            }} />
          </Field>
          <Field>
            <FieldLabel htmlFor="agent-create-instructions">Instructions</FieldLabel>
            <Textarea id="agent-create-instructions" name="instructions" required maxLength={12000} value={draft.instructions} placeholder="Define the agent's operating instructions and boundaries." onInput={(event) => {
              const next = event.currentTarget.value;
              store.updateCreateDraft({ instructions: next });
            }} />
            <FieldDescription>
              {pendingSourceName === null
                ? "Source attachments can be added after the Agent is created."
                : "This creates the Agent first; the retained API Source is attached only by the separate attachment action."}
            </FieldDescription>
          </Field>
          <Button type="submit" disabled={busy}>
            <Plus data-icon="inline-start" />{busy ? "Creating…" : "Create agent"}
          </Button>
        </FieldGroup>
      </form>
    </section>
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The agent action failed.";
}
