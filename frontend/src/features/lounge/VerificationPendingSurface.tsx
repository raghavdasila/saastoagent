import { useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { ArrowLeft, MailCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ownerAuthClient } from "./authClient";
import { useOwnerSession } from "./OwnerSessionContext";

export function VerificationPendingSurface({
  dispatchAffordance,
}: RouteDeckSurfaceComponentProps) {
  const { session, loading } = useOwnerSession();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function resend() {
    if (busy || session === null) return;
    setBusy(true);
    setMessage(null);
    try {
      await ownerAuthClient.sendVerification();
      setMessage("A fresh verification email was requested.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Verification delivery could not be requested.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <section className="workspace-auth" role="status">Checking owner account…</section>;
  }
  if (session === null) {
    return <section className="workspace-auth" role="alert">Sign in before requesting verification.</section>;
  }

  return (
    <section className="workspace-auth" aria-labelledby="verification-pending-title">
      <header>
        <p>Corpus account</p>
        <h1 id="verification-pending-title">Verify your email</h1>
        <span>
          Request a fresh verification link for {session.owner.email}. Pending
          verification does not block the rest of your Workspace.
        </span>
      </header>
      <div className="workspace-auth-actions workspace-auth-standalone-actions">
        <Button type="button" size="lg" disabled={busy || session.owner.is_verified} onClick={() => void resend()}>
          <MailCheck data-icon="inline-start" />
          {session.owner.is_verified ? "Email already verified" : busy ? "Requesting…" : "Resend verification"}
        </Button>
        <Button type="button" size="lg" variant="outline" disabled={busy} onClick={() => void dispatchAffordance("return_to_workspace", {})}>
          <ArrowLeft data-icon="inline-start" />
          Back to Workspace
        </Button>
      </div>
      {message === null ? null : <p role="status">{message}</p>}
    </section>
  );
}
