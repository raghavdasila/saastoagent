import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { AgentSelectionStore } from "../agents/contracts";
import { completedOutcome } from "@/shared/routedeck/operationResult";
import type { DesignerClient } from "./client";
import type { AgentDesignView, DesignContent } from "./models";
import type { DesignerRefreshStore } from "./refreshStore";
import { DesignerBlueprint } from "./DesignerBlueprint";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";


export function DesignerSurface({ dispatchAffordance, props, agentStore, client, refreshStore }: RouteDeckSurfaceComponentProps & { agentStore: AgentSelectionStore; client: DesignerClient; refreshStore: DesignerRefreshStore }) {
  const sessionVersion = useRouteDeckSessionVersion();
  const agents = useSyncExternalStore(agentStore.subscribe, agentStore.snapshot);
  const selectedRef = typeof props.selected_agent_ref === "string" ? props.selected_agent_ref : null;
  const selected = useMemo(() => agents.agents.find((item) => item.id === agents.selectedId) ?? null, [agents.agents, agents.selectedId]);
  const [view, setView] = useState<AgentDesignView | null>(null);
  const [draft, setDraft] = useState<DesignContent | null>(null);
  const [featureDescription, setFeatureDescription] = useState("");
  const [designLoaded, setDesignLoaded] = useState(false);
  const [attachmentsLoaded, setAttachmentsLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refreshSequence = useSyncExternalStore(refreshStore.subscribe, refreshStore.snapshot);
  const savedRevision = view?.revisions.at(-1) ?? null;
  const currentAccepted = view !== null && view.accepted_revision_id === view.current_revision_id;
  const currentBuildRequest = view !== null && view.build_request?.design_revision_id === view.current_revision_id
    ? view.build_request
    : null;
  const topologyCurrent = draft !== null && savedRevision !== null
    && JSON.stringify(draft) === JSON.stringify(savedRevision.content);

  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => { agentStore.syncSelectionFromHandle(selectedRef); }, [agentStore, agents.agents, selectedRef]);
  useEffect(() => {
    if (selected === null) {
      setAttachmentsLoaded(false);
      return;
    }
    let active = true;
    setAttachmentsLoaded(false);
    void agentStore.refreshAttachments(selected.id).finally(() => {
      if (active) setAttachmentsLoaded(true);
    });
    return () => { active = false; };
  }, [agentStore, selected?.id]);
  useEffect(() => {
    if (selected === null) {
      setDesignLoaded(false);
      return;
    }
    let active = true;
    setDesignLoaded(false);
    void client.get(selected.id).then((next) => {
      if (!active) return;
      setView(next);
      setDraft(next?.revisions.at(-1)?.content ?? null);
    }).catch((caught) => {
      if (active) setError(message(caught));
    }).finally(() => {
      if (active) setDesignLoaded(true);
    });
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

  async function generateFeature() {
    if (
      selectedRef === null
      || selected === null
      || view === null
      || featureDescription.trim().length < 8
    ) return;
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance("generate_feature", {
        agent_ref: selectedRef,
        expected_revision_id: view.current_revision_id,
        description: featureDescription.trim(),
      });
      const failure = completedOutcome(result, "generated");
      if (failure !== null) setError(failure);
      else {
        await refresh();
        setFeatureDescription("");
      }
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function continueToBuilds() {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const failure = completedOutcome(
        await dispatchAffordance("continue_to_builds", { agent_ref: selectedRef }),
        "opened",
      );
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function openSourcePrerequisite(sourceId: string) {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const failure = completedOutcome(
        await dispatchAffordance("open_source_prerequisite", {
          agent_ref: selectedRef,
          source_id: sourceId,
        }),
        "opened",
      );
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  return (
    <section className="designer-home" aria-labelledby="designer-title">
      <header><div><p>Selected Agent</p><h1 id="designer-title">Agent Designer</h1><span>{selected?.name ?? "Loading exact Agent…"}</span></div>
        <Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void dispatchAffordance("return_to_agent", { agent_ref: selectedRef })}>Back to Agent</Button>
      </header>
      {error === null ? null : <p role="alert">{error}</p>}
      {!designLoaded ? <p role="status">Loading the current Agent design…</p> : view === null ? (
        <section className="designer-home__prerequisites" aria-labelledby="designer-prerequisites-title">
          <div>
            <p>Design inputs</p>
            <h2 id="designer-prerequisites-title">Prepare the attached Sources</h2>
            <span>Each attached API version needs an explicit operation selection before Designer can propose from it.</span>
          </div>
          {!attachmentsLoaded ? <p role="status">Checking the attached Sources…</p> : agents.attachments.length === 0 ? <p>Attach at least one analyzed Source to this Agent first.</p> : (
            <ul>{agents.attachments.map((attachment) => <li key={`${attachment.source_id}:${attachment.source_revision_id}`}>
              <div><strong>{attachment.display_name}</strong><span>API version {attachment.source_revision_id}</span></div>
              <Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void openSourcePrerequisite(attachment.source_id)}>Open Source setup</Button>
            </li>)}</ul>
          )}
          <div className="designer-home__prerequisite-actions">
            <span>After every attached Source has an operation selection, return here and propose the design.</span>
            <Button type="button" disabled={busy || selectedRef === null || !attachmentsLoaded || agents.attachments.length === 0} onClick={() => void action("propose")}>Propose design</Button>
          </div>
        </section>
      ) : draft === null ? null : (
        <>
          <dl className="designer-home__status" aria-label="Designer status">
            <div><dt>Current proposal</dt><dd>Revision {savedRevision?.revision ?? view.revisions.length}</dd></div>
            <div><dt>Approval</dt><dd>{currentAccepted ? "Accepted" : "Needs review"}</dd></div>
            <div><dt>Build</dt><dd>{currentBuildRequest?.status ?? (currentAccepted ? "Not requested" : "Awaiting approval")}</dd></div>
          </dl>
          {!view.current_inputs_ready ? (
            <section className="designer-home__input-change" role="status">
              <div><strong>Current design inputs need attention</strong><span>One or more attached API versions or operation selections are not ready for a new proposal.</span></div>
            </section>
          ) : view.current_inputs_match ? null : (
            <section className="designer-home__input-change" role="status">
              <div><strong>Agent inputs changed</strong><span>Create a new immutable proposal from the current Agent, API versions, and operation selections. The accepted design and its build history stay unchanged.</span></div>
              <Button type="button" disabled={busy || selectedRef === null} onClick={() => void action("propose")}>Update proposal from current inputs</Button>
            </section>
          )}
          {savedRevision?.topology.mode === "legacy_single_area" && view.current_inputs_ready ? (
            <section className="designer-home__input-change" role="status">
              <div><strong>A richer runtime map is available</strong><span>Create a new immutable proposal from the same Agent and operation selections. Existing accepted designs and builds remain unchanged.</span></div>
              <Button type="button" disabled={busy || selectedRef === null} onClick={() => void action("propose")}>Create capability-area proposal</Button>
            </section>
          ) : null}
          <details className="designer-home__identities"><summary>Inspect immutable design identities</summary><dl><div><dt>Current revision ID</dt><dd><code>{view.current_revision_id}</code></dd></div><div><dt>Accepted revision ID</dt><dd><code>{view.accepted_revision_id ?? "None"}</code></dd></div><div><dt>History</dt><dd>{view.revisions.length} immutable revisions</dd></div></dl></details>
          <DesignerBlueprint
            content={draft}
            topology={topologyCurrent ? savedRevision!.topology : null}
            sourceInputs={view.revisions.at(-1)?.source_inputs ?? []}
          />
          <section className="designer-home__generator" aria-labelledby="designer-generator-title">
            <div><p>Describe the next behavior</p><h2 id="designer-generator-title">Generate a feature proposal</h2><span>Corpus will use this Agent's exact Source intelligence and already-selected API operations. The result remains a draft until you approve it.</span></div>
            <Field>
              <FieldLabel htmlFor="designer-feature-description">Feature or behavior</FieldLabel>
              <Textarea id="designer-feature-description" value={featureDescription} onChange={(event) => setFeatureDescription(event.target.value)} placeholder="For example: answer product category questions, ask when the request is ambiguous, and never invent results." />
            </Field>
            <Button type="button" disabled={busy || !view.current_inputs_match || featureDescription.trim().length < 8} onClick={() => void generateFeature()}>Generate design proposal</Button>
          </section>
          <details className="designer-home__editor"><summary>Customize the Agent goal, behaviors, and policies</summary><FieldGroup>
            <Field><FieldLabel htmlFor="designer-goal">Goal</FieldLabel><Input id="designer-goal" value={draft.goal} onChange={(event) => setDraft({ ...draft, goal: event.target.value })} /></Field>
            <Field><FieldLabel htmlFor="designer-instructions">Instructions</FieldLabel><Textarea id="designer-instructions" value={draft.instructions} onChange={(event) => setDraft({ ...draft, instructions: event.target.value })} /></Field>
            {(["features", "behaviors", "policies"] as const).map((field) => <Field key={field}><FieldLabel htmlFor={`designer-${field}`}>{field[0].toUpperCase() + field.slice(1)}</FieldLabel><Textarea id={`designer-${field}`} value={draft[field].join("\n")} onChange={(event) => setDraft({ ...draft, [field]: lines(event.target.value) })} /></Field>)}
            <section className="designer-home__locked-mapping" aria-label="Source-owned capability mapping"><div><strong>Capabilities and API tools</strong><span>Locked to the exact saved Source operation selections. Change them in Source setup, then create a new proposal.</span></div><ul>{draft.capabilities.map((capability) => <li key={capability}>{capability}</li>)}</ul></section>
          </FieldGroup></details>
          <div className="designer-home__actions">
            <Button type="button" disabled={busy} onClick={() => void action("customize")}>Save customization</Button>
            <Button type="button" variant="outline" disabled={busy || currentAccepted || !view.current_inputs_match} onClick={() => void action("approve")}>Review for approval</Button>
            <Button type="button" disabled={busy || !currentAccepted || currentBuildRequest !== null} onClick={() => void action("request_build")}>{currentBuildRequest === null ? "Request build" : "Build requested"}</Button>
            {currentBuildRequest === null ? null : <Button type="button" disabled={busy} onClick={() => void continueToBuilds()}>Continue to Builds</Button>}
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
    runtime_areas: value.runtime_areas.map((item) => ({ title: item.title, capability_titles: [...item.capability_titles] })),
  };
}
function message(error: unknown): string { return error instanceof Error ? error.message : "Agent Designer is unavailable."; }
