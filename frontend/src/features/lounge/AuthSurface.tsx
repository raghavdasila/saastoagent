import { useCallback, useId, useState, type FormEvent } from "react";
import {
  useRouteDeckStore,
  type RouteDeckPrivateFormBinding,
  type RouteDeckSurfaceComponentProps,
} from "@routedeck/react";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useOwnerSession } from "../../auth/OwnerSessionContext";
import { useInitialFieldFocus } from "./useInitialFieldFocus";
import { publicOperationFailureMessage, requireCompletedOperation } from "./operationResult";

export interface AuthSurfaceProps
  extends Pick<RouteDeckSurfaceComponentProps, "dispatchAffordance"> {
  mode: "sign_in" | "register";
  privateForm: RouteDeckPrivateFormBinding;
}

export function AuthSurface({ mode, privateForm, dispatchAffordance }: AuthSurfaceProps) {
  const store = useRouteDeckStore();
  const displayNameId = useId();
  const emailId = useId();
  const passwordId = useId();
  const [message, setMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const { session, loading, refresh } = useOwnerSession();
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
      try {
        await privateForm.save(
          isRegistration
            ? { email, password, ...(displayName ? { display_name: displayName } : {}) }
            : { email, password },
          { complete: true },
        );
        await store.resync();
        requireCompletedOperation(
          await dispatchAffordance(
            isRegistration ? "create_owner_account" : "authenticate_owner",
            {},
          ),
          isRegistration ? "Account creation failed." : "Sign-in failed.",
        );
        await refresh();
      } catch (caught) {
        const authenticated = await refresh().catch(() => null);
        setMessage(
          authenticated === null
            ? publicOperationFailureMessage(
                caught,
                `${isRegistration ? "Account creation" : "Sign-in"} failed.`,
              )
            : "Authenticated. Workspace continuation failed; continue when ready.",
        );
      } finally {
        setSubmitting(false);
      }
    },
    [dispatchAffordance, isRegistration, privateForm, refresh, store, submitting],
  );

  const continueToWorkspace = useCallback(async () => {
    setMessage(null);
    setSubmitting(true);
    try {
      requireCompletedOperation(
        await dispatchAffordance("continue_to_workspace", {}),
        "Workspace continuation failed; retry when ready.",
      );
    } catch (caught) {
      setMessage(
        publicOperationFailureMessage(
          caught,
          "Workspace continuation failed; retry when ready.",
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }, [dispatchAffordance]);

  if (loading) {
    return (
      <section className="workspace-auth" aria-labelledby="workspace-auth-title">
        <header><p>Corpus account</p><h1 id="workspace-auth-title">Checking session</h1></header>
        <p role="status">Checking authentication…</p>
      </section>
    );
  }

  if (session !== null) {
    return (
      <section className="workspace-auth" aria-labelledby="workspace-auth-title">
        <header>
          <p>Corpus account</p>
          <h1 id="workspace-auth-title">Continue to workspace</h1>
          <span>Your Corpus session is authenticated. No credentials are needed.</span>
        </header>
        <div className="workspace-auth-actions">
          <Button type="button" size="lg" disabled={submitting} onClick={() => void continueToWorkspace()}>
            {submitting ? "Continuing…" : "Continue to Workspace"}
          </Button>
        </div>
        {message === null ? null : <p role="alert">{message}</p>}
      </section>
    );
  }

  return (
    <section className="workspace-auth" aria-labelledby="workspace-auth-title">
      <header>
        <p>Corpus account</p>
        <h1 id="workspace-auth-title">{isRegistration ? "Create account" : "Sign in"}</h1>
        <span>{isRegistration ? "Create your account and enter your Workspace." : "Sign in to resume your Corpus Workspace."}</span>
      </header>
      <form onSubmit={submit}>
        <FieldGroup>
          {isRegistration ? (
            <Field><FieldLabel htmlFor={displayNameId}>Display name</FieldLabel><Input ref={firstFieldRef} id={displayNameId} name="displayName" autoComplete="name" /></Field>
          ) : null}
          <Field><FieldLabel htmlFor={emailId}>Email</FieldLabel><Input ref={isRegistration ? undefined : firstFieldRef} id={emailId} name="email" type="email" autoComplete="email" required aria-invalid={errors.email !== undefined} /><FieldError>{errors.email}</FieldError></Field>
          <Field><FieldLabel htmlFor={passwordId}>Password</FieldLabel><Input id={passwordId} name="password" type="password" autoComplete={isRegistration ? "new-password" : "current-password"} required minLength={12} maxLength={128} aria-invalid={errors.password !== undefined} /><FieldError>{errors.password}</FieldError></Field>
        </FieldGroup>
        <div className="workspace-auth-actions">
          <Button type="submit" size="lg" disabled={submitting}>{submitting ? "Working…" : isRegistration ? "Create account" : "Sign in"}</Button>
          {!isRegistration ? <Button type="button" size="lg" variant="ghost" disabled={submitting} onClick={() => void dispatchAffordance("open_password_recovery", {})}>Forgot password</Button> : null}
          <Button type="button" size="lg" variant="outline" disabled={submitting} onClick={() => void dispatchAffordance("return_to_lounge", {})}><ArrowLeft data-icon="inline-start" />Back to Lounge</Button>
        </div>
      </form>
      {message === null ? null : <p role="alert">{message}</p>}
    </section>
  );
}
