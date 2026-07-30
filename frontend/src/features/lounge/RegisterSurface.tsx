import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { AuthSurface } from "./AuthSurface";

export function RegisterSurface({
  dispatchAffordance,
}: RouteDeckSurfaceComponentProps) {
  return <AuthSurface mode="register" dispatchAffordance={dispatchAffordance} />;
}
