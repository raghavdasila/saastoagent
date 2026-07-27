import { defineRouteDeckSurfaceRegistry } from "@routedeck/react";

import { LoungeSurface } from "../features/workspace/LoungeSurface";
import { RegisterSurface } from "../features/workspace/RegisterSurface";
import { SignInSurface } from "../features/workspace/SignInSurface";
import { ForgotPasswordSurface } from "../features/workspace/ForgotPasswordSurface";
import { ResetPasswordSurface } from "../features/workspace/ResetPasswordSurface";
import { VerifyEmailSurface } from "../features/workspace/VerifyEmailSurface";
import { HomeSurface } from "../features/workspace/HomeSurface";
import { SourceDebugSurface } from "../features/sources/SourceDebugSurface";

export const corpusSurfaceRegistry = defineRouteDeckSurfaceRegistry({
  "workspace.lounge": LoungeSurface,
  "workspace.sign_in": SignInSurface,
  "workspace.register": RegisterSurface,
  "workspace.forgot_password": ForgotPasswordSurface,
  "workspace.reset_password": ResetPasswordSurface,
  "workspace.verify_email": VerifyEmailSurface,
  "workspace.home": HomeSurface,
  "sources.debug": SourceDebugSurface,
});
