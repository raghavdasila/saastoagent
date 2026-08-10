import { useId, useState, type FormEvent } from "react";
import {
  useRouteDeckStore,
  type RouteDeckPrivateFormBinding,
  type RouteDeckSurfaceComponentProps,
} from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PrivateFormGate, requireFormHandle } from "../../routedeck/PrivateFormGate";
import { clearCapturedTokenFragment, useCapturedTokenFragment } from "./tokenFragment";
import { useInitialFieldFocus } from "./useInitialFieldFocus";
import { publicOperationFailureMessage, requireCompletedOperation } from "./operationResult";

export function ResetPasswordSurface(props: RouteDeckSurfaceComponentProps) {
  const token = useCapturedTokenFragment("password_reset");
  return (
    <PrivateFormGate formId={requireFormHandle(props.props)}>
      {(privateForm) => <ResetPasswordForm {...props} privateForm={privateForm} token={token} />}
    </PrivateFormGate>
  );
}

function ResetPasswordForm({ privateForm, token, dispatchAffordance }: RouteDeckSurfaceComponentProps & { privateForm: RouteDeckPrivateFormBinding; token: string | null }) {
  const store = useRouteDeckStore();
  const passwordId = useId();
  const firstFieldRef = useInitialFieldFocus();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(token === null ? "This reset link is missing its token." : null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || token === null) return;
    const newPassword = String(new FormData(event.currentTarget).get("password") ?? "");
    if (newPassword.length < 12 || newPassword.length > 128) {
      setPasswordError("Password must be between 12 and 128 characters.");
      return;
    }
    setPasswordError(null);
    setBusy(true);
    setMessage(null);
    try {
      await privateForm.save({ token, new_password: newPassword }, { complete: true });
      await store.resync();
      requireCompletedOperation(
        await dispatchAffordance("change_owner_password", {}),
        "Password reset failed.",
      );
      clearCapturedTokenFragment("password_reset");
    } catch (error) {
      setMessage(publicOperationFailureMessage(error, "Password reset failed."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="workspace-auth" aria-labelledby="reset-password-title">
      <header><p>Corpus account</p><h1 id="reset-password-title">Reset password</h1><span>Choose a new 12–128 character password.</span></header>
      <form onSubmit={(event) => void submit(event)}>
        <FieldGroup><Field><FieldLabel htmlFor={passwordId}>New password</FieldLabel><Input ref={firstFieldRef} id={passwordId} name="password" type="password" autoComplete="new-password" minLength={12} maxLength={128} required aria-invalid={passwordError !== null} /><FieldError>{passwordError}</FieldError></Field></FieldGroup>
        <div className="workspace-auth-actions">
          <Button type="submit" size="lg" disabled={busy || token === null}>{busy ? "Changing…" : "Change password"}</Button>
          <Button type="button" size="lg" variant="outline" disabled={busy} onClick={() => void dispatchAffordance("return_to_lounge", {})}>Back to Lounge</Button>
        </div>
      </form>
      {message === null ? null : <p role="alert">{message}</p>}
    </section>
  );
}
