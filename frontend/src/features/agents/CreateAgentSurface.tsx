import { useState } from "react";
import type { FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { ArrowLeft, Bot, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { AgentStore } from "./store";
import { completedOutcome } from "./operationResult";

export function CreateAgentSurface({
  dispatchAffordance,
  store,
}: RouteDeckSurfaceComponentProps & { store: AgentStore }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await dispatchAffordance("create_agent", {
        name: name.trim(),
        description: description.trim(),
        instructions: instructions.trim(),
      });
      const failure = completedOutcome(result, "created");
      if (failure !== null) {
        setError(failure);
        setBusy(false);
      } else {
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
      <form onSubmit={(event) => void create(event)}>
        <Bot aria-hidden="true" className="agent-create-icon" />
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="agent-create-name">Name</FieldLabel>
            <Input id="agent-create-name" required maxLength={120} value={name} placeholder="Research Agent" onChange={(event) => setName(event.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="agent-create-description">Description</FieldLabel>
            <Input id="agent-create-description" maxLength={500} value={description} placeholder="What this agent is responsible for" onChange={(event) => setDescription(event.target.value)} />
          </Field>
          <Field>
            <FieldLabel htmlFor="agent-create-instructions">Instructions</FieldLabel>
            <Textarea id="agent-create-instructions" required maxLength={12000} value={instructions} placeholder="Define the agent's operating instructions and boundaries." onChange={(event) => setInstructions(event.target.value)} />
            <FieldDescription>Source attachments and deployments are outside this core slice.</FieldDescription>
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
