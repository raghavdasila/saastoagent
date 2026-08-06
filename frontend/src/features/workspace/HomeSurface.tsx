import { useEffect, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { BadgeCheck, Bot, DatabaseZap, LogOut, MailWarning } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ownerAuthClient } from "../../auth/authClient";
import { useOwnerSession } from "../../auth/OwnerSessionContext";
import type { WorkspaceStore } from "./store";

export function HomeSurface({
  dispatchAffordance,
  workspaceStore,
}: RouteDeckSurfaceComponentProps & { workspaceStore: WorkspaceStore }) {
  const { session, loading, setSession } = useOwnerSession();
  const workspace = useSyncExternalStore(
    workspaceStore.subscribe,
    workspaceStore.snapshot,
  );
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => {
    void workspaceStore.refresh();
  }, [workspaceStore]);
  if (loading) return <section className="workspace-home" role="status">Loading owner Workspace…</section>;
  if (session === null) return <section className="workspace-home" role="alert">Owner session unavailable.</section>;
  const name = session.owner.display_name ?? session.owner.email;
  async function logout() {
    setBusy(true); setMessage(null);
    try {
      await ownerAuthClient.signOut();
      setSession(null);
      window.location.assign("/");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Sign-out failed.");
      setBusy(false);
    }
  }
  async function openSources() {
    setBusy(true); setMessage(null);
    try { await dispatchAffordance("open_sources", {}); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Sources could not be opened."); setBusy(false); }
  }
  async function openAgents() {
    setBusy(true); setMessage(null);
    try { await dispatchAffordance("open_agents", {}); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Agents could not be opened."); setBusy(false); }
  }
  async function openVerification() {
    setBusy(true); setMessage(null);
    try { await dispatchAffordance("open_verification", {}); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Email verification could not be opened."); setBusy(false); }
  }
  return (
    <section className="workspace-home" aria-labelledby="workspace-home-title">
      <header><p>Personal Workspace</p><h1 id="workspace-home-title">Welcome, {name}</h1><span>{session.organization.name} · {session.membership.role}</span></header>
      <div className="workspace-verification" data-verified={session.owner.is_verified}>
        {session.owner.is_verified ? <BadgeCheck /> : <MailWarning />}
        <span>{session.owner.is_verified ? "Email verified" : "Email verification is advisory and still pending"}</span>
      </div>
      {workspace.error === null ? null : <p role="alert">{workspace.error}</p>}
      {workspace.loading && workspace.overview === null ? <p role="status">Loading Workspace overview…</p> : null}
      {workspace.overview === null ? null : (
        <div className="workspace-overview" aria-label="Workspace overview">
          <article data-status={workspace.overview.agents.status}>
            <Bot aria-hidden="true" />
            <div><strong>Agents</strong><span>{workspace.overview.agents.message}</span></div>
            <em>{workspace.overview.agent_count}</em>
          </article>
          <article data-status={workspace.overview.sources.status}>
            <DatabaseZap aria-hidden="true" />
            <div><strong>Sources</strong><span>{workspace.overview.sources.message}</span></div>
          </article>
          <article data-status={workspace.overview.recent_activity.status}>
            <span aria-hidden="true">↻</span>
            <div><strong>Recent activity</strong><span>{workspace.overview.recent_activity.message}</span></div>
          </article>
        </div>
      )}
      <div className="workspace-auth-actions">
        <Button type="button" disabled={busy} onClick={() => void openAgents()}><Bot data-icon="inline-start" />Open Agents</Button>
        <Button type="button" disabled={busy} onClick={() => void openSources()}><DatabaseZap data-icon="inline-start" />Open Sources debug</Button>
        {session.owner.is_verified ? null : <Button type="button" variant="outline" disabled={busy} onClick={() => void openVerification()}>Manage verification</Button>}
        <Button type="button" variant="outline" disabled={busy} onClick={() => void logout()}><LogOut data-icon="inline-start" />Sign out</Button>
      </div>
      {message === null ? null : <p role="status">{message}</p>}
    </section>
  );
}
