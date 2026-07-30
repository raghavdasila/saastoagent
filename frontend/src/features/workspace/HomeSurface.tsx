import { useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { BadgeCheck, DatabaseZap, LogOut, MailWarning } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ownerAuthClient } from "../lounge/authClient";
import { useOwnerSession } from "../lounge/OwnerSessionContext";

export function HomeSurface({ dispatchAffordance }: RouteDeckSurfaceComponentProps) {
  const { session, loading, setSession } = useOwnerSession();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
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
      <div className="workspace-auth-actions">
        <Button type="button" disabled={busy} onClick={() => void openSources()}><DatabaseZap data-icon="inline-start" />Open Sources debug</Button>
        {session.owner.is_verified ? null : <Button type="button" variant="outline" disabled={busy} onClick={() => void openVerification()}>Manage verification</Button>}
        <Button type="button" variant="outline" disabled={busy} onClick={() => void logout()}><LogOut data-icon="inline-start" />Sign out</Button>
      </div>
      {message === null ? null : <p role="status">{message}</p>}
    </section>
  );
}
