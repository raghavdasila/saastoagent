import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { AuthSurface } from "./AuthSurface";

export function SignInSurface({
  dispatchAffordance,
}: RouteDeckSurfaceComponentProps) {
  return <AuthSurface mode="sign_in" dispatchAffordance={dispatchAffordance} />;
}
