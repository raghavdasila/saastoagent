import { useState } from "react";
import {
  useRouteDeckStore,
  type RouteDeckPrivateFormBinding,
  type RouteDeckSurfaceComponentProps,
} from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { PrivateFormGate, requireFormHandle } from "./PrivateFormGate";
import { useOwnerSession } from "./OwnerSessionContext";
import { clearCapturedTokenFragment, useCapturedTokenFragment } from "./tokenFragment";

export function VerifyEmailSurface(props: RouteDeckSurfaceComponentProps) {
  const token = useCapturedTokenFragment("verification");
  return (
    <PrivateFormGate formId={requireFormHandle(props.props)}>
      {(privateForm) => <VerifyEmailForm {...props} privateForm={privateForm} token={token} />}
    </PrivateFormGate>
  );
}

function VerifyEmailForm({ privateForm, token, dispatchAffordance }: RouteDeckSurfaceComponentProps & { privateForm: RouteDeckPrivateFormBinding; token: string | null }) {
  const store = useRouteDeckStore();
  const { refresh } = useOwnerSession();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(token === null ? "This verification link is missing its token." : null);

  async function verify() {
    if (token === null || busy) return;
    setBusy(true);
    setMessage(null);
    try {
      await privateForm.save({ token }, { complete: true });
      await store.resync();
      await dispatchAffordance("confirm_owner_email", {});
      clearCapturedTokenFragment("verification");
      const refreshed = await refresh();
      if (refreshed?.owner.is_verified !== true) {
        throw new Error("Email verification could not be confirmed from the refreshed owner state.");
      }
      setMessage("Email verified.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Email verification failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="workspace-auth" aria-labelledby="verify-email-title">
      <header><p>Corpus account</p><h1 id="verify-email-title">Verify email</h1><span>Confirm the address associated with your owner account.</span></header>
      <div className="workspace-auth-actions workspace-auth-standalone-actions">
        <Button type="button" size="lg" disabled={busy || token === null} onClick={() => void verify()}>{busy ? "Verifying…" : "Verify email"}</Button>
        <Button type="button" size="lg" variant="outline" disabled={busy} onClick={() => void dispatchAffordance("return_to_lounge", {})}>Back to Lounge</Button>
      </div>
      {message === null ? null : <p role="status">{message}</p>}
    </section>
  );
}
