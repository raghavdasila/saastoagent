import { useCallback, useEffect, useState, type FormEvent } from "react";
import type {
  RouteDeckPrivateFormBinding,
  RouteDeckSurfaceComponentProps,
} from "@routedeck/react";
import { useRouteDeckStore } from "@routedeck/react";
import { KeyRound, ShieldCheck, TestTubeDiagonal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

import {
  type ApiAuthenticationMethod,
  type ApiConnectionProfile,
  type ApiConnectionCheckRecord,
  SourceClient,
} from "./sourceClient";


export function ApiConnectionPanel({
  sourceId,
  sourceRevisionId,
  safeCheckEnabled,
  sourceClient,
  privateForm,
  dispatchAffordance,
}: {
  sourceId: string;
  sourceRevisionId: string;
  safeCheckEnabled: boolean;
  sourceClient: SourceClient;
  privateForm: RouteDeckPrivateFormBinding;
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"];
}) {
  const store = useRouteDeckStore();
  const [profiles, setProfiles] = useState<readonly ApiConnectionProfile[]>([]);
  const [checks, setChecks] = useState<readonly ApiConnectionCheckRecord[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [safeOperationId, setSafeOperationId] = useState<"GetProductTypes" | "GetProductTags">("GetProductTypes");
  const [authenticationMethod, setAuthenticationMethod] =
    useState<ApiAuthenticationMethod>("none");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [current, currentChecks] = await Promise.all([
      sourceClient.listApiConnections(sourceId),
      safeCheckEnabled
        ? sourceClient.listApiConnectionChecks(sourceId, sourceRevisionId)
        : Promise.resolve([]),
    ]);
    setProfiles(current);
    setChecks(currentChecks);
    setSelectedProfileId((selected) =>
      current.some((profile) => profile.id === selected)
        ? selected
        : current.at(0)?.id ?? "",
    );
  }, [safeCheckEnabled, sourceClient, sourceId, sourceRevisionId]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    void refresh()
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Connection profiles could not be loaded.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [refresh]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const profileName = String(data.get("profileName") ?? "").trim();
    const environment = String(data.get("environment") ?? "").trim();
    const baseUrl = String(data.get("baseUrl") ?? "").trim();
    const credentialName = String(data.get("credentialName") ?? "").trim();
    const credentialValue = String(data.get("credentialValue") ?? "");
    setSubmitting(true);
    setError(null);
    try {
      await privateForm.save(
        {
          source_id: sourceId,
          profile_name: profileName,
          environment,
          base_url: baseUrl,
          authentication_method: authenticationMethod,
          ...(authenticationMethod === "api_key"
            ? { credential_name: credentialName, credential_value: credentialValue }
            : authenticationMethod === "bearer"
              ? { credential_value: credentialValue }
              : {}),
        },
        { complete: true },
      );
      await store.resync();
      const result = await dispatchAffordance("save_api_connection", {});
      if (result.outcome !== "saved") {
        throw new Error(result.failure?.public_message ?? "The API connection could not be saved.");
      }
      privateForm.clear();
      await privateForm.load();
      await refresh();
      form.reset();
      setAuthenticationMethod("none");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The API connection could not be saved.");
    } finally {
      setSubmitting(false);
    }
  }

  async function checkConnection() {
    if (checking || selectedProfileId === "" || !safeCheckEnabled) return;
    setChecking(true);
    setError(null);
    try {
      const result = await dispatchAffordance("test_api_connection", {
        source_id: sourceId,
        source_revision_id: sourceRevisionId,
        connection_profile_id: selectedProfileId,
        operation_id: safeOperationId,
      });
      await refresh();
      if (result.outcome !== "checked") {
        throw new Error(result.failure?.public_message ?? "The API connection check failed.");
      }
    } catch (caught) {
      await refresh().catch(() => undefined);
      setError(caught instanceof Error ? caught.message : "The API connection check failed.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <section className="api-connection-panel" aria-labelledby="api-connection-title">
      <div className="api-connection-heading">
        <div>
          <p>Revision-bound configuration</p>
          <h3 id="api-connection-title"><KeyRound aria-hidden="true" /> API connections</h3>
        </div>
        <span><ShieldCheck aria-hidden="true" /> Credentials are encrypted and never returned.</span>
      </div>

      {loading ? <p role="status">Loading connection profiles…</p> : null}
      {error === null ? null : <p role="alert" className="sources-debug-error">{error}</p>}
      {profiles.length === 0 ? null : (
        <p role="status" className="source-ready">
          {checks.length === 0
            ? "Saved profile metadata is revision-bound. Credentials remain protected. No connection check was run."
            : "Saved profile metadata and redacted check history are revision-bound. Credentials remain protected."}
        </p>
      )}

      <div className="api-connection-grid">
        <section aria-labelledby="saved-profiles-title">
          <h4 id="saved-profiles-title">Saved profiles</h4>
          {profiles.length === 0 && !loading ? <p>No connection profiles yet.</p> : null}
          <ul className="api-connection-list">
            {profiles.map((profile) => (
              <li key={profile.id}>
                <div><strong>{profile.profile_name}</strong><span>{profile.environment}</span></div>
                <code>{profile.base_url}</code>
                <small>
                  {profile.authentication_method === "none"
                    ? "No authentication"
                    : `Protected ${profile.authentication_method.replace("_", " ")} · credential v${profile.credential_version}`}
                </small>
              </li>
            ))}
          </ul>
        </section>

        <form onSubmit={(event) => void save(event)}>
          <h4>Add connection profile</h4>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="api-profile-name">Profile name</FieldLabel>
              <Input id="api-profile-name" name="profileName" required maxLength={80} placeholder="Production" />
            </Field>
            <Field>
              <FieldLabel htmlFor="api-environment">Environment</FieldLabel>
              <Input id="api-environment" name="environment" required maxLength={80} placeholder="production" />
            </Field>
            <Field>
              <FieldLabel htmlFor="api-base-url">Base URL</FieldLabel>
              <Input id="api-base-url" name="baseUrl" type="url" required placeholder="https://api.example.com" />
            </Field>
            <Field>
              <FieldLabel htmlFor="api-authentication">Authentication</FieldLabel>
              <select
                id="api-authentication"
                name="authenticationMethod"
                value={authenticationMethod}
                onChange={(event) => setAuthenticationMethod(event.target.value as ApiAuthenticationMethod)}
              >
                <option value="none">None</option>
                <option value="api_key">API key</option>
                <option value="bearer">Bearer token</option>
              </select>
            </Field>
            {authenticationMethod === "api_key" ? (
              <Field>
                <FieldLabel htmlFor="api-credential-name">Header name</FieldLabel>
                <Input id="api-credential-name" name="credentialName" required maxLength={128} placeholder="X-API-Key" />
              </Field>
            ) : null}
            {authenticationMethod === "none" ? null : (
              <Field>
                <FieldLabel htmlFor="api-credential-value">
                  {authenticationMethod === "api_key" ? "API key" : "Bearer token"}
                </FieldLabel>
                <Input id="api-credential-value" name="credentialValue" type="password" required autoComplete="off" />
                <FieldDescription>The value travels only through the protected form and encrypted vault.</FieldDescription>
              </Field>
            )}
            <Button type="submit" disabled={submitting || privateForm.pending}>
              <ShieldCheck data-icon="inline-start" />{submitting ? "Saving…" : "Save connection"}
            </Button>
            <FieldDescription>Saving does not test the endpoint. Run a safe check explicitly below.</FieldDescription>
          </FieldGroup>
        </form>
      </div>
      <section className="api-connection-checks" aria-labelledby="api-connection-check-title">
        <div>
          <p>Explicit safe read</p>
          <h4 id="api-connection-check-title"><TestTubeDiagonal aria-hidden="true" /> Test API connection</h4>
          <span>One selected read, validated against this exact revision. No automatic retry.</span>
        </div>
        {!safeCheckEnabled ? (
          <p>Approve the reviewed effective API contract before running a connection check.</p>
        ) : profiles.length === 0 ? (
          <p>Save a connection profile before running a check.</p>
        ) : (
          <div className="api-connection-check-controls">
            <Field>
              <FieldLabel htmlFor="api-check-profile">Connection profile</FieldLabel>
              <select
                id="api-check-profile"
                value={selectedProfileId}
                onChange={(event) => setSelectedProfileId(event.target.value)}
              >
                {profiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>{profile.profile_name} · {profile.environment}</option>
                ))}
              </select>
            </Field>
            <Field>
              <FieldLabel htmlFor="api-check-operation">Safe check operation</FieldLabel>
              <select
                id="api-check-operation"
                value={safeOperationId}
                onChange={(event) => setSafeOperationId(event.target.value as "GetProductTypes" | "GetProductTags")}
              >
                <option value="GetProductTypes">Get product types</option>
                <option value="GetProductTags">Get product tags</option>
              </select>
            </Field>
            <Button type="button" disabled={checking || selectedProfileId === ""} onClick={() => void checkConnection()}>
              <TestTubeDiagonal data-icon="inline-start" />{checking ? "Checking…" : "Test connection"}
            </Button>
          </div>
        )}
        {checks.length === 0 ? null : (
          <ol className="api-connection-check-list">
            {[...checks].reverse().map((check) => (
              <li key={check.id} data-status={check.status}>
                <div>
                  <strong>{check.status === "succeeded" ? "Connection check succeeded" : "Connection check failed"}</strong>
                  <span>{check.operation_id} · {check.method} {check.path_template}</span>
                </div>
                <dl>
                  <div><dt>HTTP calls</dt><dd>{check.http_call_count}</dd></div>
                  <div><dt>Status</dt><dd>{check.status_code ?? "Not sent"}</dd></div>
                  <div><dt>Validation issues</dt><dd>{check.validation_issue_count}</dd></div>
                  <div><dt>Contract</dt><dd><code>{check.effective_contract_sha256.slice(0, 12)}…</code></dd></div>
                </dl>
                {check.public_message === null ? null : <p>{check.public_message}</p>}
              </li>
            ))}
          </ol>
        )}
      </section>
    </section>
  );
}
