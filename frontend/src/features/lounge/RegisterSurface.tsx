import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { AuthSurface } from "./AuthSurface";
import { PrivateFormGate, requireFormHandle } from "./PrivateFormGate";

export function RegisterSurface({
  dispatchAffordance,
  props,
}: RouteDeckSurfaceComponentProps) {
  return (
    <PrivateFormGate formId={requireFormHandle(props)}>
      {(privateForm) => <AuthSurface mode="register" privateForm={privateForm} dispatchAffordance={dispatchAffordance} />}
    </PrivateFormGate>
  );
}
