import { defineRouteDeckSurfaceRegistry } from "@routedeck/react";

import { LoungeSurface } from "../features/lounge/LoungeSurface";
import { RegisterSurface } from "../features/lounge/RegisterSurface";
import { SignInSurface } from "../features/lounge/SignInSurface";
import { ForgotPasswordSurface } from "../features/lounge/ForgotPasswordSurface";
import { ResetPasswordSurface } from "../features/lounge/ResetPasswordSurface";
import { VerifyEmailSurface } from "../features/lounge/VerifyEmailSurface";
import { VerificationPendingSurface } from "../features/lounge/VerificationPendingSurface";
import { HomeSurface } from "../features/workspace/HomeSurface";
import { SourceDebugSurface } from "../features/sources/SourceDebugSurface";

export const corpusSurfaceRegistry = defineRouteDeckSurfaceRegistry({
  "lounge.home": LoungeSurface,
  "lounge.sign_in": SignInSurface,
  "lounge.register": RegisterSurface,
  "lounge.forgot_password": ForgotPasswordSurface,
  "lounge.reset_password": ResetPasswordSurface,
  "lounge.verify_email": VerifyEmailSurface,
  "lounge.verification_pending": VerificationPendingSurface,
  "workspace.home": HomeSurface,
  "sources.debug": SourceDebugSurface,
});
