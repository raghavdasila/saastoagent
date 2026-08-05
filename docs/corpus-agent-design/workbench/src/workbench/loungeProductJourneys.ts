import type { ProductJourneyEval } from "./types"

const surfaceJourney = (
  id: string,
  title: string,
  startingBehavior: string,
  startingAuthentication: ProductJourneyEval["startingAuthentication"],
  goal: string,
  preconditions: string[],
  requiredOutcomes: string[],
  forbiddenOutcomes: string[],
  finalBehavior: string,
  finalAuthentication: ProductJourneyEval["finalAuthentication"],
  stateAssertions: string[],
): ProductJourneyEval => ({
  id, title, enabled: true, blocking: true, interaction: "surface",
  startingBehavior, startingAuthentication, goal, preconditions,
  openingMessage: "", testerPersona: "", testerFacts: [], withholdUntilAsked: [],
  requiredOutcomes, forbiddenOutcomes, finalBehavior, finalAuthentication,
  stateAssertions, maxTurns: 0,
})

export const LOUNGE_PRODUCT_JOURNEYS: ProductJourneyEval[] = [
  surfaceJourney("lounge-journey-register-sign-in", "Register, sign out, and sign in", "Arrive in the Lounge", "public", "Create a new owner account, enter its Workspace, sign out, and authenticate again.", ["Use a unique public test mailbox and a new strong password."], ["Registration creates one owner Workspace and an authenticated session.", "The owner can sign out and sign in with the same credentials."], ["Do not claim registration before authenticated Workspace entry."], "Enter the Workspace", "authenticated", ["One owner, personal organization, owner membership, adopted conversation, and active owner session exist."]),
  surfaceJourney("lounge-journey-duplicate-registration", "Keep duplicate registration account-neutral", "Create an owner account", "public", "Submit an email that already owns a Corpus account without learning whether it exists.", ["The submitted email already belongs to an owner."], ["Registration remains unsuccessful with account-neutral recovery."], ["Do not reveal that the email is already registered.", "Do not create another owner or Workspace."], "Create an owner account", "public", ["Exactly one owner and one personal Workspace remain for the email."]),
  surfaceJourney("lounge-journey-password-reset", "Reset password and authenticate again", "Request password recovery", "public", "Receive a one-time reset link, change the password, and sign in with the new password.", ["A live owner account and public mailbox exist."], ["A reset request is accepted without account disclosure.", "A valid link changes the password and returns to sign in.", "The new password authenticates."], ["The old password must not authenticate after reset.", "No reset token appears in chat or persisted visible state."], "Enter the Workspace", "authenticated", ["Pre-reset sessions are revoked and a new authenticated owner session exists."]),
  surfaceJourney("lounge-journey-unknown-reset", "Keep unknown-account recovery neutral", "Request password recovery", "public", "Request recovery for an address that has no Corpus account.", ["The mailbox address does not belong to a Corpus owner."], ["The same generic acceptance shown for an existing account is presented."], ["Do not reveal that the account is absent.", "Do not create an owner or send a reset token."], "Request password recovery", "public", ["No owner, organization, membership, or reset state is created."]),
  surfaceJourney("lounge-journey-mail-outage", "Report a known reset-mail outage safely", "Request password recovery", "public", "Request password recovery while the mail service is independently known to be unavailable.", ["Corpus has recorded a service-wide mail outage before account lookup."], ["Mail-service unavailability remains visible with account-neutral copy."], ["Do not claim recipient delivery or reveal account existence."], "Request password recovery", "public", ["No password or owner state changes occur."]),
  surfaceJourney("lounge-journey-email-verification", "Resend and confirm email verification", "Resend email verification", "authenticated", "Request a verification message, consume its one-time link, and confirm refreshed owner state.", ["A signed-in owner has an unverified public mailbox."], ["The request is accepted without claiming delivery.", "A valid link verifies the owner and refreshed state confirms it."], ["No token remains in the visible URL, chat, or persisted visible state."], "Confirm email verification", "authenticated", ["The owner record and refreshed browser session both report verified email."]),
  surfaceJourney("lounge-journey-verification-rate-limit", "Rate-limit verification before token generation", "Resend email verification", "authenticated", "Exceed the verification resend limit without generating another token.", ["A signed-in unverified owner has reached the resend limit."], ["The next request is visibly rate-limited."], ["Do not generate or send another verification token.", "Do not block permitted Workspace use."], "Resend email verification", "authenticated", ["The rate-limit count changes as designed while verification state stays unverified."]),
  surfaceJourney("lounge-journey-invalid-verification", "Reject an invalid verification link", "Confirm email verification", "authenticated", "Open a missing, invalid, or expired verification link.", ["The owner is unverified and the supplied token is not valid."], ["The failure is explicit and offers safe recovery."], ["Do not claim verification or silently request another message."], "Confirm email verification", "authenticated", ["The owner and refreshed session remain unverified."]),
]

export function copyProductJourneyEvals(): ProductJourneyEval[] {
  return LOUNGE_PRODUCT_JOURNEYS.map((journey) => ({
    ...journey,
    preconditions: [...journey.preconditions],
    testerFacts: [...journey.testerFacts],
    withholdUntilAsked: [...journey.withholdUntilAsked],
    requiredOutcomes: [...journey.requiredOutcomes],
    forbiddenOutcomes: [...journey.forbiddenOutcomes],
    stateAssertions: [...journey.stateAssertions],
  }))
}
