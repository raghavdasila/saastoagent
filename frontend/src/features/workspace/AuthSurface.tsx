import { useCallback, useId, useState, type FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ownerAuthClient } from "./authClient";
import { useOwnerSession } from "./OwnerSessionContext";
import { useInitialFieldFocus } from "./useInitialFieldFocus";

export interface AuthSurfaceProps
  extends Pick<RouteDeckSurfaceComponentProps, "dispatchAffordance"> {
  mode: "sign_in" | "register";
}

export function AuthSurface({ mode, dispatchAffordance }: AuthSurfaceProps) {
  const displayNameId = useId();
  const emailId = useId();
  const passwordId = useId();
  const [message, setMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [continuationPending, setContinuationPending] = useState(false);
  const { setSession } = useOwnerSession();
  const firstFieldRef = useInitialFieldFocus();
  const isRegistration = mode === "register";

  const submit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (submitting) return;
      const data = new FormData(event.currentTarget);
      const email = String(data.get("email") ?? "").trim().toLowerCase();
      const password = String(data.get("password") ?? "");
      const displayName = String(data.get("displayName") ?? "").trim();
      const nextErrors: Record<string, string> = {};
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        nextErrors.email = "Enter a valid email address.";
      }
      if (password.length < 12 || password.length > 128) {
        nextErrors.password = "Password must be between 12 and 128 characters.";
      } else if (email && password.toLowerCase().includes(email)) {
        nextErrors.password = "Password must not contain your email address.";
      }
      setErrors(nextErrors);
      if (Object.keys(nextErrors).length > 0) return;
      setSubmitting(true);
      setMessage(null);
      setContinuationPending(false);
      try {
        const owner = isRegistration
          ? await ownerAuthClient.register({
              email,
              password,
              ...(displayName ? { display_name: displayName } : {}),
            })
          : await ownerAuthClient.signIn({ email, password });
        setSession(owner);
        try {
          await dispatchAffordance("authentication_completed", {});
        } catch {
          setContinuationPending(true);
          setMessage(
            "Signed in. Workspace continuation failed; retry when ready.",
          );
        }
      } catch (caught) {
        setMessage(
          caught instanceof Error
            ? caught.message
            : `${isRegistration ? "Account creation" : "Sign-in"} failed.`,
        );
      } finally {
        setSubmitting(false);
      }
    },
    [dispatchAffordance, isRegistration, setSession, submitting],
  );
  const continueToWorkspace = useCallback(async () => {
    setSubmitting(true);
    setMessage(null);
    try {
      await dispatchAffordance("authentication_completed", {});
      setContinuationPending(false);
    } catch {
      setMessage("Signed in. Workspace continuation failed; retry when ready.");
    } finally {
      setSubmitting(false);
    }
  }, [dispatchAffordance]);
  const returnToLounge = useCallback(async () => {
    setMessage(null);
    try {
      await dispatchAffordance("return_to_lounge", {});
    } catch (caught) {
      setMessage(
        caught instanceof Error
          ? caught.message
          : "The Lounge could not be opened.",
      );
    }
  }, [dispatchAffordance]);
  const openForgotPassword = useCallback(async () => {
    setMessage(null);
    try {
      await dispatchAffordance("open_forgot_password", {});
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "Password reset could not be opened.");
    }
  }, [dispatchAffordance]);

  return (
    <section className="workspace-auth" aria-labelledby="workspace-auth-title">
      <header>
        <p>Corpus account</p>
        <h1 id="workspace-auth-title">
          {isRegistration ? "Create account" : "Sign in"}
        </h1>
        <span>
          {isRegistration
            ? "Create your account here. Corpus will continue after authentication succeeds."
            : "Sign in to continue to your Corpus workspace."}
        </span>
      </header>
      <form onSubmit={submit}>
        <FieldGroup>
          {isRegistration ? (
            <Field>
              <FieldLabel htmlFor={displayNameId}>Display name</FieldLabel>
              <Input ref={firstFieldRef} id={displayNameId} name="displayName" autoComplete="name" />
            </Field>
          ) : null}
          <Field>
            <FieldLabel htmlFor={emailId}>Email</FieldLabel>
            <Input ref={isRegistration ? undefined : firstFieldRef} id={emailId} name="email" type="email" autoComplete="email" required aria-invalid={errors.email !== undefined} />
            <FieldError>{errors.email}</FieldError>
          </Field>
          <Field>
            <FieldLabel htmlFor={passwordId}>Password</FieldLabel>
            <Input
              id={passwordId}
              name="password"
              type="password"
              autoComplete={isRegistration ? "new-password" : "current-password"}
              required
              minLength={12}
              maxLength={128}
              aria-invalid={errors.password !== undefined}
            />
            <FieldError>{errors.password}</FieldError>
          </Field>
        </FieldGroup>
        <div className="workspace-auth-actions">
          <Button type="submit" size="lg" disabled={submitting}>
            {submitting ? "Working…" : isRegistration ? "Create account" : "Sign in"}
          </Button>
          {continuationPending ? (
            <Button type="button" size="lg" disabled={submitting} onClick={() => void continueToWorkspace()}>
              Retry Workspace continuation
            </Button>
          ) : null}
          {!isRegistration ? (
            <Button type="button" size="lg" variant="ghost" disabled={submitting} onClick={() => void openForgotPassword()}>
              Forgot password
            </Button>
          ) : null}
          <Button type="button" size="lg" variant="outline" disabled={submitting} onClick={() => void returnToLounge()}>
            <ArrowLeft data-icon="inline-start" />
            Back to Lounge
          </Button>
        </div>
      </form>
      {message === null ? null : <p role="alert">{message}</p>}
    </section>
  );
}
