import { useId, useState, type FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ownerAuthClient } from "./authClient";
import {
  clearCapturedTokenFragment,
  useCapturedTokenFragment,
} from "./tokenFragment";
import { useInitialFieldFocus } from "./useInitialFieldFocus";

export function ResetPasswordSurface({ dispatchAffordance }: RouteDeckSurfaceComponentProps) {
  const passwordId = useId();
  const firstFieldRef = useInitialFieldFocus();
  const token = useCapturedTokenFragment("password_reset");
  const [busy, setBusy] = useState(false);
  const [complete, setComplete] = useState(false);
  const [message, setMessage] = useState<string | null>(
    token === null ? "This reset link is missing its token." : null,
  );
  const [passwordError, setPasswordError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || token === null) return;
    const password = String(new FormData(event.currentTarget).get("password") ?? "");
    if (password.length < 12 || password.length > 128) {
      setPasswordError("Password must be between 12 and 128 characters.");
      return;
    }
    setPasswordError(null);
    setBusy(true);
    setMessage(null);
    try {
      await ownerAuthClient.confirmPasswordReset(token, password);
      clearCapturedTokenFragment("password_reset");
      setComplete(true);
      setMessage("Password changed. All sessions were signed out; return to sign in.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Password reset failed.");
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
          {complete ? (
            <Button type="button" size="lg" onClick={() => window.location.assign("/")}>Continue to sign in</Button>
          ) : (
            <Button type="submit" size="lg" disabled={busy || token === null}>{busy ? "Changing…" : "Change password"}</Button>
          )}
          {complete ? null : <Button type="button" size="lg" variant="outline" disabled={busy} onClick={() => void dispatchAffordance("return_to_lounge", {})}>Back to Lounge</Button>}
        </div>
      </form>
      {message === null ? null : <p role="status">{message}</p>}
    </section>
  );
}
