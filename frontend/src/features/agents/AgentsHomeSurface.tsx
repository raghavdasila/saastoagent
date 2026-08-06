import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { ArrowLeft, Bot, Plus, Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { AgentStore } from "./store";
import { completedOutcome } from "./operationResult";

type BusyAction = "create" | "save" | "return";

export function AgentsHomeSurface({
  dispatchAffordance,
  store,
}: RouteDeckSurfaceComponentProps & { store: AgentStore }) {
  const snapshot = useSyncExternalStore(store.subscribe, store.snapshot);
  const selected = useMemo(
    () =>
      snapshot.agents.find((agent) => agent.id === snapshot.selectedId) ?? null,
    [snapshot.agents, snapshot.selectedId],
  );
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [busy, setBusy] = useState<BusyAction | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    void store.refresh();
  }, [store]);

  useEffect(() => {
    setName(selected?.name ?? "");
    setDescription(selected?.description ?? "");
    setInstructions(selected?.instructions ?? "");
    setActionError(null);
  }, [selected?.id, selected?.current_version]);

  async function openCreate() {
    setBusy("create");
    setActionError(null);
    try {
      const result = await dispatchAffordance("open_create", {});
      const failure = completedOutcome(result, "opened");
      if (failure !== null) {
        setActionError(failure);
        setBusy(null);
      }
    } catch (error) {
      setActionError(errorMessage(error));
      setBusy(null);
    }
  }

  async function returnToWorkspace() {
    setBusy("return");
    setActionError(null);
    try {
      const result = await dispatchAffordance("return_to_workspace", {});
      const failure = completedOutcome(result, "opened");
      if (failure !== null) {
        setActionError(failure);
        setBusy(null);
      }
    } catch (error) {
      setActionError(errorMessage(error));
      setBusy(null);
    }
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selected === null) return;
    setBusy("save");
    setActionError(null);
    try {
      const result = await dispatchAffordance("save_changes", {
        agent_id: selected.id,
        expected_version: selected.current_version,
        name: name.trim(),
        description: description.trim(),
        instructions: instructions.trim(),
      });
      const failure = completedOutcome(result, "saved");
      if (failure !== null) {
        setActionError(failure);
      } else {
        await store.refresh();
      }
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="agents-home" aria-labelledby="agents-home-title">
      <header className="agents-heading">
        <div>
          <p>Workspace</p>
          <h1 id="agents-home-title">Agents</h1>
          <span>Persistent agent identities with immutable configuration history.</span>
        </div>
        <div>
          <Button
            type="button"
            variant="outline"
            disabled={busy !== null}
            onClick={() => void returnToWorkspace()}
          >
            <ArrowLeft data-icon="inline-start" />Back to Workspace
          </Button>
          <Button
            type="button"
            disabled={busy !== null}
            onClick={() => void openCreate()}
          >
            <Plus data-icon="inline-start" />Create agent
          </Button>
        </div>
      </header>

      {snapshot.error === null ? null : (
        <p className="agents-error" role="alert">{snapshot.error}</p>
      )}
      {actionError === null ? null : (
        <p className="agents-error" role="alert">{actionError}</p>
      )}

      <div className="agents-layout">
        <aside aria-label="Agent inventory">
          <h2>Agent inventory <span>{snapshot.agents.length}</span></h2>
          {snapshot.loading && snapshot.agents.length === 0 ? (
            <p role="status">Loading agents…</p>
          ) : null}
          {!snapshot.loading && snapshot.agents.length === 0 ? (
            <div className="agents-empty">
              <Bot aria-hidden="true" />
              <strong>No agents yet</strong>
              <span>Create the first agent configuration for this Workspace.</span>
            </div>
          ) : null}
          <ul>
            {snapshot.agents.map((agent) => (
              <li key={agent.id}>
                <button
                  type="button"
                  data-selected={agent.id === snapshot.selectedId}
                  onClick={() => store.select(agent.id)}
                >
                  <Bot aria-hidden="true" />
                  <span><strong>{agent.name}</strong><small>Version {agent.current_version}</small></span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main>
          {selected === null ? (
            <div className="agents-editor-empty">
              <Bot aria-hidden="true" />
              <h2>Select an agent</h2>
              <p>Its current configuration will appear here.</p>
            </div>
          ) : (
            <form onSubmit={(event) => void save(event)}>
              <header>
                <div><p>Current configuration</p><h2>{selected.name}</h2></div>
                <span>Version {selected.current_version}</span>
              </header>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="agent-edit-name">Name</FieldLabel>
                  <Input id="agent-edit-name" required maxLength={120} value={name} onChange={(event) => setName(event.target.value)} />
                </Field>
                <Field>
                  <FieldLabel htmlFor="agent-edit-description">Description</FieldLabel>
                  <Input id="agent-edit-description" maxLength={500} value={description} onChange={(event) => setDescription(event.target.value)} />
                </Field>
                <Field>
                  <FieldLabel htmlFor="agent-edit-instructions">Instructions</FieldLabel>
                  <Textarea id="agent-edit-instructions" required maxLength={12000} value={instructions} onChange={(event) => setInstructions(event.target.value)} />
                </Field>
                <Button type="submit" disabled={busy !== null}>
                  <Save data-icon="inline-start" />
                  {busy === "save" ? "Saving…" : "Save new version"}
                </Button>
              </FieldGroup>
            </form>
          )}
        </main>
      </div>
    </section>
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The agent action failed.";
}
