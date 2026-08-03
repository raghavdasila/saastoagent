import {
  RouteDeckPrivateForm,
  type RouteDeckPrivateFormBinding,
} from "@routedeck/react";
import type { ReactNode } from "react";

export function PrivateFormGate({
  formId,
  children,
}: {
  formId: string;
  children(binding: RouteDeckPrivateFormBinding): ReactNode;
}) {
  return (
    <RouteDeckPrivateForm formId={formId} loadOnMount>
      {(binding) => {
        if (binding.snapshot === null) {
          return binding.error === null ? (
            <section className="workspace-auth" role="status">
              Loading private form…
            </section>
          ) : (
            <section className="workspace-auth" role="alert">
              Corpus could not load this form. Try again.
            </section>
          );
        }
        return children(binding);
      }}
    </RouteDeckPrivateForm>
  );
}


export function requireFormHandle(props: Readonly<Record<string, unknown>>): string {
  const value = props.form_handle;
  if (typeof value !== "string" || value.length === 0) {
    throw new Error("The Lounge surface requires a projected private-form handle.");
  }
  return value;
}
