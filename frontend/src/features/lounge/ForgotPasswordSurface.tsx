import { useId, useState, type FormEvent } from "react";
import {
  useRouteDeckStore,
  type RouteDeckPrivateFormBinding,
  type RouteDeckSurfaceComponentProps,
} from "@routedeck/react";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PrivateFormGate, requireFormHandle } from "./PrivateFormGate";
import { useInitialFieldFocus } from "./useInitialFieldFocus";

export function ForgotPasswordSurface(props: RouteDeckSurfaceComponentProps) {
  return (
    <PrivateFormGate formId={requireFormHandle(props.props)}>
      {(privateForm) => <ForgotPasswordForm {...props} privateForm={privateForm} />}
    </PrivateFormGate>
  );
}

function ForgotPasswordForm({ privateForm, dispatchAffordance }: RouteDeckSurfaceComponentProps & { privateForm: RouteDeckPrivateFormBinding }) {
  const store = useRouteDeckStore();
  const emailId = useId();
  const firstFieldRef = useInitialFieldFocus();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const email = String(new FormData(event.currentTarget).get("email") ?? "").trim().toLowerCase();
    setBusy(true);
    setMessage(null);
    try {
      await privateForm.save({ email }, { complete: true });
      await store.resync();
      await dispatchAffordance("request_password_recovery", {});
      setMessage("If that account exists, a password-reset email has been requested.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Password reset could not be requested.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="workspace-auth" aria-labelledby="forgot-password-title">
      <header><p>Corpus account</p><h1 id="forgot-password-title">Forgot password</h1><span>Request a one-hour reset link without revealing whether an account exists.</span></header>
      <form onSubmit={(event) => void submit(event)}>
        <FieldGroup><Field><FieldLabel htmlFor={emailId}>Email</FieldLabel><Input ref={firstFieldRef} id={emailId} name="email" type="email" autoComplete="email" required /></Field></FieldGroup>
        <div className="workspace-auth-actions">
          <Button type="submit" size="lg" disabled={busy}>{busy ? "Requesting…" : "Request reset"}</Button>
          <Button type="button" size="lg" variant="outline" disabled={busy} onClick={() => void dispatchAffordance("return_to_lounge", {})}><ArrowLeft data-icon="inline-start" />Back to Lounge</Button>
        </div>
      </form>
      {message === null ? null : <p role="status">{message}</p>}
    </section>
  );
}
