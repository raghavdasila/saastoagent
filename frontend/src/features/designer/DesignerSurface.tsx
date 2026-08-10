import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { AgentStore } from "../agents/store";
import { completedOutcome } from "../agents/operationResult";
import type { DesignerClient } from "./client";
import type { AgentDesignView, DesignContent } from "./models";
import type { DesignerRefreshStore } from "./refreshStore";
import { DesignerBlueprint } from "./DesignerBlueprint";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";


export function DesignerSurface({ dispatchAffordance, props, agentStore, client, refreshStore }: RouteDeckSurfaceComponentProps & { agentStore: AgentStore; client: DesignerClient; refreshStore: DesignerRefreshStore }) {
  const sessionVersion = useRouteDeckSessionVersion();
  const agents = useSyncExternalStore(agentStore.subscribe, agentStore.snapshot);
  const selectedRef = typeof props.selected_agent_ref === "string" ? props.selected_agent_ref : null;
  const selected = useMemo(() => agents.agents.find((item) => item.id === agents.selectedId) ?? null, [agents.agents, agents.selectedId]);
  const [view, setView] = useState<AgentDesignView | null>(null);
  const [draft, setDraft] = useState<DesignContent | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refreshSequence = useSyncExternalStore(refreshStore.subscribe, refreshStore.snapshot);
  const savedRevision = view?.revisions.at(-1) ?? null;
  const topologyCurrent = draft !== null && savedRevision !== null
    && JSON.stringify(draft) === JSON.stringify(savedRevision.content);

  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => { agentStore.syncSelectionFromHandle(selectedRef); }, [agentStore, agents.agents, selectedRef]);
  useEffect(() => {
    if (selected === null) return;
    let active = true;
    void client.get(selected.id).then((next) => {
      if (!active) return;
      setView(next);
      setDraft(next?.revisions.at(-1)?.content ?? null);
    }).catch((caught) => active && setError(message(caught)));
    return () => { active = false; };
  }, [client, selected?.id, refreshSequence, sessionVersion]);

  async function refresh() {
    if (selected === null) return;
    const next = await client.get(selected.id);
    setView(next);
    setDraft(next?.revisions.at(-1)?.content ?? null);
  }

  async function action(affordance: "propose" | "customize" | "approve" | "request_build") {
    if (selectedRef === null || selected === null) return;
    setBusy(true);
    setError(null);
    try {
      const current = view?.revisions.at(-1);
      if (affordance !== "propose" && (current === undefined || draft === null)) return;
      const result = affordance === "propose"
        ? await dispatchAffordance(affordance, { agent_ref: selectedRef })
        : affordance === "customize"
          ? await dispatchAffordance(affordance, { agent_ref: selectedRef, expected_revision_id: view!.current_revision_id, content: contentArguments(draft!) })
          : affordance === "approve"
            ? await dispatchAffordance(affordance, { agent_ref: selectedRef, expected_revision_id: view!.current_revision_id })
            : await dispatchAffordance(affordance, { agent_ref: selectedRef, accepted_revision_id: view!.accepted_revision_id! });
      if (affordance === "approve") {
        if (result.disposition !== "requires_review") setError(result.failure?.public_message ?? "Designer review could not be prepared.");
      } else {
        const expected = affordance === "customize" ? "customized" : affordance === "request_build" ? "requested" : "proposed";
        const failure = completedOutcome(result, expected);
        if (failure !== null) setError(failure);
        else await refresh();
      }
    } catch (caught) {
      setError(message(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="designer-home" aria-labelledby="designer-title">
      <header><div><p>Selected Agent</p><h1 id="designer-title">Agent Designer</h1><span>{selected?.name ?? "Loading exact Agent…"}</span></div>
        <Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void dispatchAffordance("return_to_agent", { agent_ref: selectedRef })}>Back to Agent</Button>
      </header>
      {error === null ? null : <p role="alert">{error}</p>}
      {view === null ? (
        <div><p>No design proposal exists. Proposal uses the exact current Agent, pinned Source revisions, and saved operation curations.</p><Button type="button" disabled={busy || selectedRef === null} onClick={() => void action("propose")}>Propose design</Button></div>
      ) : draft === null ? null : (
        <>
          <dl><div><dt>Current revision</dt><dd>{view.current_revision_id}</dd></div><div><dt>Accepted revision</dt><dd>{view.accepted_revision_id ?? "None"}</dd></div><div><dt>History</dt><dd>{view.revisions.length} immutable revisions</dd></div></dl>
          <DesignerBlueprint
            content={draft}
            topology={topologyCurrent ? savedRevision!.topology : null}
            sourceInputs={view.revisions.at(-1)?.source_inputs ?? []}
          />
          <FieldGroup>
            <Field><FieldLabel htmlFor="designer-goal">Goal</FieldLabel><Input id="designer-goal" value={draft.goal} onChange={(event) => setDraft({ ...draft, goal: event.target.value })} /></Field>
            <Field><FieldLabel htmlFor="designer-instructions">Instructions</FieldLabel><Textarea id="designer-instructions" value={draft.instructions} onChange={(event) => setDraft({ ...draft, instructions: event.target.value })} /></Field>
            {(["features", "behaviors", "policies", "capabilities", "tools"] as const).map((field) => (
              <Field key={field}><FieldLabel htmlFor={`designer-${field}`}>{field === "capabilities" ? "Capabilities (Title: operation IDs)" : field[0].toUpperCase() + field.slice(1)}</FieldLabel><Textarea id={`designer-${field}`} value={draft[field].join("\n")} onChange={(event) => setDraft({ ...draft, [field]: lines(event.target.value) })} /></Field>
            ))}
          </FieldGroup>
          <div>
            <Button type="button" disabled={busy} onClick={() => void action("customize")}>Save customization</Button>
            <Button type="button" variant="outline" disabled={busy} onClick={() => void action("approve")}>Review for approval</Button>
            <Button type="button" disabled={busy || view.accepted_revision_id === null || view.build_request !== null} onClick={() => void action("request_build")}>{view.build_request === null ? "Request build" : `Build ${view.build_request.status}`}</Button>
          </div>
        </>
      )}
    </section>
  );
}

function lines(value: string): readonly string[] { return value.split("\n").map((item) => item.trim()).filter(Boolean); }
function contentArguments(value: DesignContent) {
  return {
    goal: value.goal,
    instructions: value.instructions,
    features: [...value.features],
    behaviors: [...value.behaviors],
    policies: [...value.policies],
    capabilities: [...value.capabilities],
    tools: [...value.tools],
  };
}
function message(error: unknown): string { return error instanceof Error ? error.message : "Agent Designer is unavailable."; }
