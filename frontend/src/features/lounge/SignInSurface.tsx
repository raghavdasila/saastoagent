import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { AuthSurface } from "./AuthSurface";
import { PrivateFormGate, requireFormHandle } from "./PrivateFormGate";

export function SignInSurface({
  dispatchAffordance,
  props,
}: RouteDeckSurfaceComponentProps) {
  return (
    <PrivateFormGate formId={requireFormHandle(props)}>
      {(privateForm) => <AuthSurface mode="sign_in" privateForm={privateForm} dispatchAffordance={dispatchAffordance} />}
    </PrivateFormGate>
  );
}
