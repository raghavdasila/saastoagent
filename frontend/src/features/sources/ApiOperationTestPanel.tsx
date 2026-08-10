import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { Route } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

import {
  SourceClient,
  type ApiConnectionProfile,
  type ApiOperationCurationView,
  type ApiRoutePlanView,
  type SourceView,
} from "./sourceClient";
import type { RoutedExecutionStore } from "./routedExecutionStore";

const EFFECTIVE_HASH = "6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6";

export function ApiOperationTestPanel({
  props,
  sourceClient,
  dispatchAffordance,
  executionStore,
}: RouteDeckSurfaceComponentProps & {
  sourceClient: SourceClient;
  executionStore: RoutedExecutionStore;
}) {
  const generation = useRef(0);
  const activity = useRef(false);
  const [sources, setSources] = useState<readonly SourceView[]>([]);
  const [sourceId, setSourceId] = useState("");
  const [profiles, setProfiles] = useState<readonly ApiConnectionProfile[]>([]);
  const [profileId, setProfileId] = useState("");
  const [curation, setCuration] = useState<ApiOperationCurationView | null>(null);
  const [plan, setPlan] = useState<ApiRoutePlanView | null>(null);
  const [requestText, setRequestText] = useState("");
  const [knownInputName, setKnownInputName] = useState("");
  const [knownInputValue, setKnownInputValue] = useState("");
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const execution = useSyncExternalStore(executionStore.subscribe, executionStore.snapshot);
  const open = props.open === true;

  const refreshSelection = useCallback(async (selected: SourceView, ticket: number) => {
    const [nextProfiles, nextCuration, nextPlan] = await Promise.all([
      sourceClient.listApiConnections(selected.source_id),
      sourceClient.inspectApiOperationCuration(
        selected.source_id,
        selected.revision.revision_id,
      ),
      sourceClient.currentApiRoutePlan(
        selected.source_id,
        selected.revision.revision_id,
      ),
    ]);
    if (generation.current !== ticket) return;
    const matchingProfiles = nextProfiles.filter((profile) =>
      profile.revision_id === selected.revision.revision_id
    );
    setProfiles(matchingProfiles);
    setProfileId((current) =>
      matchingProfiles.some((profile) => profile.id === current)
        ? current
        : matchingProfiles.at(0)?.id ?? ""
    );
    setCuration(nextCuration);
    setPlan(nextPlan);
    if (nextPlan === null) executionStore.clear();
    else await executionStore.select(selected.source_id, nextPlan);
  }, [executionStore, sourceClient]);

  useEffect(() => {
    if (!open) return;
    const ticket = ++generation.current;
    activity.current = true;
    setBusy(true);
    setError(null);
    void sourceClient.list()
      .then(async (items) => {
        if (generation.current !== ticket) return;
        const eligible = items.filter(isEffectiveReadySource);
        setSources(eligible);
        const selected = eligible.find((item) => item.source_id === sourceId)
          ?? eligible.at(-1)
          ?? null;
        setSourceId(selected?.source_id ?? "");
        if (selected !== null) await refreshSelection(selected, ticket);
      })
      .catch((caught) => {
        if (generation.current === ticket) setError(errorMessage(caught));
      })
      .finally(() => {
        if (generation.current === ticket) {
          activity.current = false;
          setBusy(false);
        }
      });
    return () => {
      generation.current += 1;
      activity.current = false;
    };
  }, [open, refreshSelection, sourceClient]);

  async function selectSource(nextSourceId: string) {
    const selected = sources.find((item) => item.source_id === nextSourceId);
    setSourceId(nextSourceId);
    setProfiles([]);
    setProfileId("");
    setCuration(null);
    setPlan(null);
    executionStore.clear();
    setError(null);
    if (selected === undefined) return;
    const ticket = ++generation.current;
    activity.current = true;
    setBusy(true);
    try {
      await refreshSelection(selected, ticket);
    } catch (caught) {
      if (generation.current === ticket) setError(errorMessage(caught));
    } finally {
      if (generation.current === ticket) {
        activity.current = false;
        setBusy(false);
      }
    }
  }

  async function createPlan(event: FormEvent) {
    event.preventDefault();
    if (activity.current || selectedSource === null || curation?.current == null || !profileId) return;
    activity.current = true;
    setBusy(true);
    setError(null);
    try {
      const created = await sourceClient.createApiRoutePlan(selectedSource.source_id, {
        source_revision_id: selectedSource.revision.revision_id,
        profile_id: profileId,
        curation_id: curation.current.id,
        request_text: requestText,
        provided_inputs: knownInputName.trim() && knownInputValue.trim()
          ? { [knownInputName.trim()]: knownInputValue.trim() }
          : {},
      });
      setPlan(created);
      await executionStore.select(selectedSource.source_id, created);
      setAnswer("");
    } catch (caught) {
      setError(errorMessage(caught));
      await sourceClient.currentApiRoutePlan(
        selectedSource.source_id,
        selectedSource.revision.revision_id,
      ).then(async (current) => {
        setPlan(current);
        if (current === null) executionStore.clear();
        else await executionStore.select(selectedSource.source_id, current);
      }).catch(() => undefined);
    } finally {
      activity.current = false;
      setBusy(false);
    }
  }

  async function clarify(event: FormEvent) {
    event.preventDefault();
    if (activity.current || selectedSource === null || plan === null || !answer.trim()) return;
    const inputName = plan.state === "needs_operation_choice"
      ? "operation_id"
      : plan.missing_inputs.at(0);
    if (inputName === undefined) return;
    activity.current = true;
    setBusy(true);
    setError(null);
    try {
      const refreshed = await sourceClient.clarifyApiRoutePlan(
        selectedSource.source_id,
        plan.plan_id,
        {
          source_revision_id: selectedSource.revision.revision_id,
          expected_record_id: plan.record_id,
          answers: { [inputName]: answer.trim() },
        },
      );
      setPlan(refreshed);
      await executionStore.select(selectedSource.source_id, refreshed);
      setAnswer("");
    } catch (caught) {
      setError(errorMessage(caught));
      await sourceClient.currentApiRoutePlan(
        selectedSource.source_id,
        selectedSource.revision.revision_id,
      ).then(async (current) => {
        setPlan(current);
        if (current === null) executionStore.clear();
        else await executionStore.select(selectedSource.source_id, current);
      }).catch(() => undefined);
    } finally {
      activity.current = false;
      setBusy(false);
    }
  }

  if (!open) return null;
  const selectedSource = sources.find((item) => item.source_id === sourceId) ?? null;
  const selectedProfile = profiles.find((profile) => profile.id === profileId) ?? null;
  const canCreate = selectedSource !== null && curation?.current !== null
    && selectedProfile !== null && requestText.trim().length > 0 && plan === null
    && ((!knownInputName.trim() && !knownInputValue.trim())
      || (!!knownInputName.trim() && !!knownInputValue.trim()));

  return (
    <section className="api-operation-test" aria-labelledby="api-operation-test-title">
      <header>
        <Route aria-hidden="true" />
        <div>
          <p>Non-executing ToolRouter plan</p>
          <h2 id="api-operation-test-title">API operation test</h2>
          <span>Choose the exact approved revision, curation and saved profile before routing.</span>
        </div>
      </header>
      <p className="api-route-no-call" role="note">Planning only; no API request has been sent.</p>
      {error === null ? null : <p className="sources-debug-error" role="alert">{error}</p>}
      {busy && sources.length === 0 ? <p role="status">Loading exact route-planning context…</p> : null}
      {sources.length === 0 && !busy ? (
        <p role="status">Approve an effective API revision before preparing a route.</p>
      ) : (
        <form onSubmit={(event) => void createPlan(event)}>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="api-route-source">Effective API revision</FieldLabel>
              <select
                id="api-route-source"
                value={sourceId}
                disabled={busy || plan !== null}
                onChange={(event) => void selectSource(event.currentTarget.value)}
              >
                {sources.map((source) => (
                  <option key={source.source_id} value={source.source_id}>
                    {source.display_name} · {source.revision.revision_id}
                  </option>
                ))}
              </select>
              <FieldDescription>Exact contract {EFFECTIVE_HASH.slice(0, 12)}…</FieldDescription>
            </Field>
            <Field>
              <FieldLabel htmlFor="api-route-profile">Saved connection profile</FieldLabel>
              <select
                id="api-route-profile"
                value={profileId}
                disabled={busy || plan !== null}
                onChange={(event) => setProfileId(event.currentTarget.value)}
              >
                <option value="">Select a profile</option>
                {profiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.profile_name} · {profile.environment}
                  </option>
                ))}
              </select>
            </Field>
            <Field>
              <FieldLabel htmlFor="api-route-request">What should Corpus route?</FieldLabel>
              <Input
                id="api-route-request"
                value={requestText}
                disabled={busy || plan !== null}
                onChange={(event) => setRequestText(event.currentTarget.value)}
                placeholder="List orders for the selected customer"
              />
              <FieldDescription>
                Current curation {curation?.current?.id ?? "unavailable"} · included {curation?.current?.included_operation_ids.length ?? 0}
              </FieldDescription>
            </Field>
            <Field>
              <FieldLabel htmlFor="api-route-known-name">Known input name (optional)</FieldLabel>
              <Input
                id="api-route-known-name"
                value={knownInputName}
                disabled={busy || plan !== null}
                onChange={(event) => setKnownInputName(event.currentTarget.value)}
                placeholder="customer_id"
              />
              <FieldDescription>Use this only for a non-secret value already supplied in the current request.</FieldDescription>
            </Field>
            <Field>
              <FieldLabel htmlFor="api-route-known-value">Known input value (optional)</FieldLabel>
              <Input
                id="api-route-known-value"
                value={knownInputValue}
                disabled={busy || plan !== null}
                onChange={(event) => setKnownInputValue(event.currentTarget.value)}
                placeholder="cus_123"
              />
            </Field>
            <Button type="submit" disabled={busy || !canCreate}>
              {busy ? "Preparing route…" : "Prepare route"}
            </Button>
          </FieldGroup>
        </form>
      )}
      {plan === null ? null : <PlanResult plan={plan} answer={answer} setAnswer={setAnswer} busy={busy} clarify={clarify} />}
      {plan === null ? null : (
        <ExecutionControl
          plan={plan}
          snapshot={execution}
          busy={busy}
          dispatch={async (affordanceId) => {
            if (activity.current) return;
            activity.current = true;
            setBusy(true);
            setError(null);
            executionStore.clearError();
            try {
              const result = await dispatchAffordance(affordanceId, { plan_id: plan.plan_id });
              await executionStore.refresh();
              const completedRead = affordanceId === "run_routed_api_read"
                && result.disposition === "completed" && result.outcome === "observed";
              const stagedWrite = affordanceId === "review_routed_api_write"
                && result.disposition === "requires_review";
              if (!completedRead && !stagedWrite && executionStore.snapshot().result === null) {
                executionStore.reportError(
                  result.failure?.public_message ?? "Corpus could not complete this routed API request.",
                );
              }
            } catch (caught) {
              await executionStore.refresh().catch(() => undefined);
              executionStore.reportError(errorMessage(caught));
            } finally {
              activity.current = false;
              setBusy(false);
            }
          }}
        />
      )}
    </section>
  );
}

function ExecutionControl({
  plan,
  snapshot,
  busy,
  dispatch,
}: {
  plan: ApiRoutePlanView;
  snapshot: ReturnType<RoutedExecutionStore["snapshot"]>;
  busy: boolean;
  dispatch(affordanceId: "run_routed_api_read" | "review_routed_api_write"): Promise<void>;
}) {
  if (plan.state !== "ready" || plan.steps.length !== 1) return null;
  const step = plan.steps[0];
  if (step?.selected_operation_id == null || step.http_safety == null) return null;
  const result = snapshot.context?.plan.plan_id === plan.plan_id ? snapshot.result : null;
  const action = step.http_safety === "read" ? "run_routed_api_read" : "review_routed_api_write";
  return (
    <section className="api-routed-execution" aria-labelledby="api-routed-execution-title">
      <div>
        <p>{step.http_safety === "read" ? "One explicit routed read" : "Durable owner-reviewed write"}</p>
        <h3 id="api-routed-execution-title">Run the selected routed operation</h3>
        <span>{step.method} {step.path_template} · no automatic retry</span>
      </div>
      {snapshot.error === null ? null : <p className="sources-debug-error" role="alert">{snapshot.error}</p>}
      {result === null ? (
        <Button
          type="button"
          disabled={busy || snapshot.loading}
          onClick={() => void dispatch(action)}
        >
          {step.http_safety === "read" ? "Run routed read" : "Review routed write"}
        </Button>
      ) : <RoutedExecutionResult result={result} />}
    </section>
  );
}

export function RoutedExecutionResult({ result }: { result: NonNullable<ReturnType<RoutedExecutionStore["snapshot"]>["result"]> }) {
  return (
    <article className="api-routed-result" data-status={result.status}>
      <strong>{executionStatus(result.status)}</strong>
      <span>{result.operation_id} · {result.method} {result.path_template}</span>
      <dl>
        <div><dt>Delivery</dt><dd>{result.delivery.replaceAll("_", " ")}</dd></div>
        <div><dt>HTTP calls</dt><dd>{result.http_call_count ?? "Unknown after interruption"}</dd></div>
        <div><dt>Status</dt><dd>{result.status_code ?? "Not confirmed"}</dd></div>
        <div><dt>Validation issues</dt><dd>{result.validation_issue_count}</dd></div>
        <div><dt>Response bytes</dt><dd>{result.response_byte_count}</dd></div>
        <div><dt>Response identity</dt><dd><code>{result.response_body_sha256?.slice(0, 12) ?? "Unavailable"}</code></dd></div>
      </dl>
      {result.public_message === null ? null : <p>{result.public_message}</p>}
      {result.delivery === "possibly_sent" ? (
        <p role="alert">Delivery could not be confirmed. Do not retry automatically. Verify the external system state before any new attempt.</p>
      ) : null}
    </article>
  );
}

function PlanResult({
  plan,
  answer,
  setAnswer,
  busy,
  clarify,
}: {
  plan: ApiRoutePlanView;
  answer: string;
  setAnswer(value: string): void;
  busy: boolean;
  clarify(event: FormEvent): Promise<void>;
}) {
  return (
    <div className="api-route-result" data-state={plan.state}>
      <div className="api-route-result-summary">
        <strong>{stateLabel(plan.state)}</strong>
        <span>Plan {plan.plan_id} · record {plan.record_id}</span>
        <span>Fingerprint {plan.plan_fingerprint}</span>
        <span>External calls: {plan.api_call_count}</span>
      </div>
      <ol aria-label="Ordered routed operations">
        {plan.steps.map((step, index) => (
          <li key={`${step.query}:${index}`}>
            <strong>{step.selected_operation_id ?? "No operation selected"}</strong>
            <span>{step.method ?? "—"} {step.path_template ?? "—"} · {step.http_safety ?? "waiting"}</span>
            <small>{step.query}</small>
          </li>
        ))}
      </ol>
      {plan.input_provenance.length === 0 ? null : (
        <dl className="api-route-provenance" aria-label="Route input provenance">
          {plan.input_provenance.map((item) => (
            <div key={item.name}>
              <dt>{item.name}</dt>
              <dd>{item.source === "current_request" ? "Current request" : "User clarification"}</dd>
            </div>
          ))}
        </dl>
      )}
      {plan.managed_parameters.length === 0 ? null : (
        <dl className="api-route-provenance" aria-label="Profile-managed route inputs">
          {plan.managed_parameters.map((item) => (
            <div key={`${item.location}:${item.name}`}>
              <dt>{item.name}</dt>
              <dd>Managed by selected connection profile</dd>
            </div>
          ))}
        </dl>
      )}
      {plan.clarification_prompt === null ? null : (
        <form className="api-route-clarification" onSubmit={(event) => void clarify(event)}>
          <Field>
            <FieldLabel htmlFor="api-route-answer">{plan.clarification_prompt}</FieldLabel>
            {plan.state === "needs_operation_choice" ? (
              <select
                id="api-route-answer"
                value={answer}
                disabled={busy}
                onChange={(event) => setAnswer(event.currentTarget.value)}
              >
                <option value="">Select an included operation</option>
                {Array.from(new Set(
                  plan.steps.flatMap((step) => step.ranked_operations.map((item) => item.operation_id)),
                )).map((operationId) => (
                  <option key={operationId} value={operationId}>{operationId}</option>
                ))}
              </select>
            ) : (
              <Input
                id="api-route-answer"
                value={answer}
                disabled={busy}
                onChange={(event) => setAnswer(event.currentTarget.value)}
              />
            )}
          </Field>
          <Button type="submit" disabled={busy || !answer.trim()}>
            {busy ? "Updating plan…" : "Continue this plan"}
          </Button>
        </form>
      )}
      {plan.operation_choice === null ? null : (
        <p className="api-route-choice">
          Chosen operation {plan.operation_choice.operation_id} from this plan's clarification.
        </p>
      )}
    </div>
  );
}

function isEffectiveReadySource(source: SourceView): boolean {
  return source.connector_key === "api"
    && source.revision.state === "ready"
    && source.revision.summary.revision_kind === "reviewed_api_contract"
    && source.revision.summary.final_canonical_sha256 === EFFECTIVE_HASH;
}

function stateLabel(state: ApiRoutePlanView["state"]): string {
  if (state === "ready") return "Route ready for one explicit operation";
  if (state === "needs_input") return "Waiting for one required value";
  if (state === "needs_operation_choice") return "Waiting for an operation choice";
  return "No included operation can route this request";
}

function executionStatus(status: NonNullable<ReturnType<RoutedExecutionStore["snapshot"]>["result"]>["status"]): string {
  if (status === "succeeded") return "Routed API request succeeded";
  if (status === "outcome_unknown") return "Routed API write outcome is unknown";
  return "Routed API request failed";
}

function errorMessage(value: unknown): string {
  return value instanceof Error ? value.message : "The API route plan is unavailable.";
}
