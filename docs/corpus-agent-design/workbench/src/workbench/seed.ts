import type { CapabilityDesign, DesignStory, OperationDesign, SuggestedActionDesign, SurfaceDesign, WorkbenchState } from "@/workbench/types"
import { copyConversationEvals, loungeBehaviorEvals } from "@/workbench/loungeEvaluations"

type StoryOptions = {
  suggestedActions?: Array<Pick<SuggestedActionDesign, "id" | "label">>
  surface?: string | null
  status?: DesignStory["status"]
}

type PolicySeed = [scope: "surface" | "operation", scopeName: string, instruction: string]

type NodeTemplate = {
  name: string
  context: string
  policies: string[]
  capabilities: Array<Omit<CapabilityDesign, "operationNames" | "surfaceNames">>
}

const BEHAVIOR_POLICY_SEED: Record<string, PolicySeed[]> = {
  "lounge-arrival": [
    ["surface", "Lounge home", "Present only public orientation and entry paths; never expose or imply access to private Workspace state."],
    ["surface", "Lounge home", "Keep this surface limited to Lounge orientation; product-help and account interactions belong to their own behaviors."],
    ["surface", "Lounge home", "Identify the active product location as Lounge and show only Lounge-scoped navigation; keep private Workspace and feature navigation hidden until authenticated entry succeeds."],
    ["operation", "Start product help", "Silently enter product-help context before answering a substantive Corpus product question from Lounge home; never mention the operation, tool, or Node name in product output."],
    ["operation", "Open owner registration", "Open account creation without implying that an account has already been created."],
    ["operation", "Open owner sign-in", "Open sign-in without implying that the visitor is already authenticated."],
  ],
  "lounge-product-help": [
    ["operation", "Return to Lounge", "Return to Lounge orientation without claiming that another product task completed."],
    ["operation", "Open owner registration", "Offer account creation when the visitor describes work they want Corpus to perform; do not continue planning or performing the task in Lounge."],
    ["operation", "Open owner sign-in", "Offer sign-in when the visitor describes work they want Corpus to perform; do not continue planning or performing the task in Lounge."],
  ],
  "owner-auth-register": [
    ["surface", "Create owner account surface", "Keep password values private and masked; never repeat credentials in chat, confirmation text, or persisted design-visible state."],
    ["operation", "Create owner account", "Submit account creation only after required fields are valid and only after the visitor explicitly chooses Create account."],
    ["operation", "Create owner account", "Claim success only after the owner identity, personal Workspace, authenticated session, and Workspace entry are established as one accepted result."],
    ["operation", "Continue to Workspace", "Continue only an already-authenticated owner into the authorized Workspace; never recreate the account or resubmit credentials."],
    ["operation", "Return to Lounge", "Leave account creation without submitting or retaining an incomplete credential form."],
  ],
  "owner-auth-sign-in": [
    ["surface", "Owner sign-in surface", "Keep credentials private and masked; never echo passwords or include them in conversational output."],
    ["operation", "Authenticate owner", "Resume only the Workspace authorized for the authenticated owner; invalid credentials remain a failure and expose no private state."],
    ["operation", "Continue to Workspace", "Continue only an already-authenticated owner into the authorized Workspace; never resubmit credentials."],
    ["operation", "Open password recovery", "Open account-neutral password recovery without revealing whether the entered email belongs to an account."],
    ["operation", "Return to Lounge", "Leave sign-in without submitting or retaining an incomplete credential form."],
  ],
  "owner-auth-request-reset": [
    ["surface", "Password reset request surface", "Use the same account-neutral confirmation whether or not the submitted email belongs to an account."],
    ["operation", "Request password recovery", "Do not reveal account existence; report delivery-system unavailability without disclosing whether the submitted account exists."],
    ["operation", "Request password recovery", "Treat submission as a recovery request only, not as proof that an account exists or that delivery succeeded."],
    ["operation", "Return to Lounge", "Return to Lounge without revealing whether the submitted email belongs to an account."],
  ],
  "owner-auth-confirm-reset": [
    ["surface", "Set new password surface", "Remove the one-time token from the visible URL and never render, repeat, or persist it in visible product state."],
    ["operation", "Change owner password", "Accept only a valid unexpired one-time token; on success change the password and revoke existing sessions."],
    ["operation", "Return to Lounge", "Leave password reset without changing the password or consuming the one-time token."],
  ],
  "owner-auth-request-verification": [
    ["operation", "Request verification delivery", "Request another verification message only after the owner explicitly asks; do not send automatically or repeatedly."],
    ["operation", "Request verification delivery", "Report request acceptance, rate limiting, or service unavailability without presenting acceptance as recipient delivery or successful verification."],
    ["operation", "Return to Workspace", "Return to the authenticated Workspace without treating pending verification as a blocker."],
  ],
  "owner-auth-confirm-verification": [
    ["surface", "Confirm owner email surface", "Remove the one-time token from the visible URL and never expose it in chat or visible confirmation state."],
    ["operation", "Confirm owner email", "Apply verification only to the owner account bound to a valid unexpired one-time token."],
    ["operation", "Return to Lounge", "Leave email confirmation without consuming or exposing the one-time token."],
  ],
  "enter-workspace": [
    ["surface", "Workspace overview", "Distinguish real counts and recent activity from truthful empty states and from temporarily unavailable information."],
    ["operation", "Navigate from Workspace overview", "Navigation to the owning feature does not create or modify agents, sources, operations, or other domain records."],
  ],
  "workspace-activity-help": [
    ["surface", "Workspace overview", "When structured state supports the answer, present the matching agents, sources, or activity without fabricating missing records."],
  ],
  "workspace-product-help": [
    ["operation", "Open relevant product feature", "Offer only currently available next steps and do not imply that choosing a destination completes the owner's task."],
  ],
  "workspace-route-task": [
    ["operation", "Navigate to owning feature", "Navigation changes location only and must never be reported as completion of the requested task."],
  ],
  "workspace-quick-actions": [
    ["surface", "Workspace overview", "Show only destinations currently available to this owner and keep unavailable or empty areas truthful."],
    ["operation", "Navigate to Workspace destination", "Navigate to the selected feature without creating, editing, archiving, deleting, deploying, or processing a resource."],
  ],
  "owner-auth-sign-out": [
    ["surface", "Owner sign-out surface", "Identify the current owner context and state clearly that signing out ends browser access but does not delete the Workspace or its resources."],
    ["operation", "Sign out", "Sign out only after the authenticated owner explicitly requests it; never infer sign-out from navigation or inactivity."],
    ["operation", "Sign out", "Success requires revoking the current browser session and owner route handle, clearing browser credentials, and returning to a fresh Lounge; failure remains visible."],
  ],
  "agents-view": [
    ["surface", "Agent list", "Distinguish configured, runnable, deployed, archived, empty, and unavailable states without inferring deployment from agent existence."],
    ["operation", "Open agent creation", "Opening agent creation does not create an agent, runnable version, or deployment."],
  ],
  "agents-create": [
    ["surface", "Create agent surface", "Collect name, description, and goal as agent identity inputs and do not imply that versioning or deployment is part of creation."],
    ["operation", "Create agent", "Submit the exact validated values once after explicit confirmation; invalid required fields must not create a record."],
    ["operation", "Create agent", "Success creates one Workspace-owned agent record only; it does not create a runnable version, evaluation result, channel, or deployment."],
  ],
  "agents-inspect": [
    ["surface", "Agent detail", "Present configured, runnable, and deployed state as distinct sections and show a public URL only when an active deployment actually exists."],
    ["surface", "Agent detail", "Do not expose source credentials, private bindings, or other secret configuration while presenting the agent record."],
  ],
  "agents-edit": [
    ["surface", "Agent detail edit", "Distinguish editable identity and configuration inputs from immutable historical versions and active deployment state."],
    ["operation", "Save agent changes", "Apply validated edits to the selected agent configuration only; never silently rewrite an existing runnable or deployed version."],
    ["operation", "Save agent changes", "Claim completion only after the exact changes are persisted; validation or persistence failure leaves the prior agent state authoritative."],
  ],
  "agents-attach-source": [
    ["surface", "Agent source picker", "Show only eligible sources from the same Workspace, including readiness and whether each source is already attached."],
    ["operation", "Attach source to agent", "Attach only the exact source selected by the owner and prevent duplicate attachment of the same source."],
    ["operation", "Attach source to agent", "Claim success only after the association is persisted and the originating agent shows the attached source."],
  ],
  "agents-create-source": [
    ["operation", "Open source creation", "Navigation to source creation does not attach a source and must not be presented as task completion."],
    ["operation", "Attach newly created source", "Attach only a successfully created eligible source; cancellation or source-creation failure returns without changing the agent."],
  ],
  "agents-open-source": [
    ["operation", "Open attached source", "Preserve the originating agent and return context when navigating to the selected source."],
  ],
  "agents-archive": [
    ["surface", "Agent lifecycle review", "Identify the exact agent and show relevant lifecycle and deployment consequences before archive confirmation."],
    ["operation", "Archive agent", "Archive only after explicit confirmation of the selected agent; never infer archive intent from list filtering or navigation."],
    ["operation", "Archive agent", "Archive is not deletion: preserve the agent record and report success only after it leaves the active list; blockers or failure remain visible."],
  ],
  "agents-delete": [
    ["surface", "Agent lifecycle review", "Identify the exact agent, active deployment, attached dependencies, and irreversible consequence before deletion can be confirmed."],
    ["operation", "Delete agent", "Require explicit confirmation after material blockers and consequences are shown; never treat archive intent as delete intent."],
    ["operation", "Delete agent", "Do not delete while declared blockers remain; claim success only after authoritative removal of the exact agent, and keep failure visible."],
  ],
  "sources-view": [
    ["surface", "Source Hub inventory", "Distinguish empty, processing, ready, failed, attached, and unavailable states; at launch present API as the only available source family."],
    ["operation", "Open API source creation", "Opening API Source starts the creation path but does not create, upload, process, or attach a source."],
  ],
  "sources-start-api": [
    ["operation", "Open API source creation", "Navigation to API Source does not create a source or imply that an API file has been accepted."],
  ],
  "sources-select-for-agent": [
    ["surface", "Source Hub picker", "Show same-Workspace sources eligible for the originating agent, including readiness and existing attachment state."],
    ["operation", "Attach selected source", "Use the exact owner-selected source and prevent duplicate attachment; do not auto-select based on name similarity."],
    ["operation", "Attach selected source", "Return to the originating agent and claim completion only after the selected source association is persisted."],
  ],
  "sources-delete": [
    ["surface", "Source deletion review", "Identify the exact source, attached agents, processing state, and other material blockers before confirmation."],
    ["operation", "Delete API source", "Require explicit confirmation of the selected source after dependencies and consequences are shown."],
    ["operation", "Delete API source", "Do not delete while declared dependencies block removal; claim success only after authoritative deletion and keep failure visible."],
  ],
  "sources-start-description": [
    ["operation", "Open API description editor", "Navigation to the description input does not upload, validate, save, or process description content."],
  ],
  "api-upload-yaml": [
    ["surface", "API intake and connection", "Accept only the documented OpenAPI YAML format and file limits, and show exact validation errors without substituting sample content."],
    ["operation", "Upload YAML", "Process only the file explicitly chosen by the owner and never replace missing or invalid input with a fixture or example specification."],
    ["operation", "Accept API revision", "Invalid input creates no accepted revision; successful acceptance creates an identifiable revision bound to the uploaded file."],
  ],
  "api-description": [
    ["surface", "API intake and connection", "Present Markdown description as supporting context distinct from the OpenAPI specification and enforce its documented file limits."],
    ["surface", "API description", "Render description content safely without executing embedded active content or exposing unrelated private files."],
    ["operation", "Save API description", "Persist valid description content only to the selected API source; invalid or failed uploads must not replace the prior description."],
  ],
  "api-configure-connection": [
    ["surface", "API intake and connection", "Distinguish base URL, authentication method, non-secret settings, and private credentials; keep secret values masked and out of chat."],
    ["operation", "Save API connection", "Persist only the exact validated settings and credential references supplied for the selected connection profile."],
    ["operation", "Test API connection", "Run a safe connection check only when explicitly requested and keep testing distinct from saving configuration."],
    ["operation", "Test API connection", "A failed or unavailable check remains a failure; never switch provider, environment, credentials, or endpoint silently."],
  ],
  "api-process-toolrouter": [
    ["surface", "API processing status", "Identify the exact accepted revision and show unmet prerequisites before processing can start."],
    ["operation", "Process API through ToolRouter", "Start processing only after explicit owner request and do not create duplicate concurrent runs for the same revision."],
    ["operation", "Process API through ToolRouter", "Use the real ToolRouter pipeline for the exact revision; never substitute cached success, a mock graph, or another processor."],
  ],
  "api-monitor-processing": [
    ["surface", "API processing status", "Show only observed phases, states, timestamps, and evidence; never invent a percentage, phase, or success state."],
    ["surface", "API processing status", "Keep actionable failure detail visible without exposing credentials, private bindings, or unrelated Workspace data."],
  ],
  "api-inspect-graph": [
    ["surface", "API graph explorer", "Render only the persisted graph for the selected revision and retain the identity of its nodes, edges, and source evidence."],
  ],
  "api-replay-graph": [
    ["surface", "API graph explorer", "Replay only persisted construction events in their recorded order and keep pause, resume, and step controls from mutating the graph."],
    ["operation", "Control graph replay", "Replay commands change only replay position; they do not rerun processing or create new graph artifacts."],
  ],
  "api-curate-operations": [
    ["surface", "API operation curation", "Show exact operations discovered for the selected revision and visibly distinguish included from excluded operations."],
    ["operation", "Save operation curation", "Persist only the owner's explicit inclusion decisions and never infer selection from inspection, filtering, or search."],
    ["operation", "Save operation curation", "Do not invent, rename, or silently broaden discovered operations; bind the saved selection to the exact source revision."],
  ],
  "api-recover-processing": [
    ["surface", "API processing recovery", "Keep the original failed step, evidence, affected revision, and valid corrective actions visible during recovery."],
    ["operation", "Retry API processing", "Retry only the affected step after explicit owner request; never retry automatically or conceal the original failure."],
    ["operation", "Retry API processing", "Use the corrected real input and required dependency; never substitute a mock, cached success, alternate processor, or generic successful result."],
  ],
}

const OPERATION_INTENDED_EFFECTS: Record<string, string> = {
  "Start product help": "Move the public conversation into product-help context so Corpus can answer under the product-help policies.",
  "Answer product help": "Return a public, product-grounded answer about Corpus and identify an available next path when one is needed.",
  "Open owner registration": "Move the Lounge visitor into owner registration while retaining the current conversation context.",
  "Open owner sign-in": "Move the Lounge visitor into owner sign-in while retaining the current conversation context.",
  "Open password recovery": "Move the Lounge visitor into the password-recovery request path.",
  "Open password reset link": "Open the password-reset location associated with a captured one-time recovery link without validating or consuming the token.",
  "Open email verification link": "Open the email-verification location associated with a captured one-time verification link without validating or consuming the token.",
  "Return to Lounge": "Return to public Lounge orientation without completing or retrying the behavior being left.",
  "Continue to Workspace": "Enter the Workspace already authorized to the authenticated browser session without repeating authentication or account creation.",
  "Return to Workspace": "Return to the authenticated Workspace without changing email-verification state.",
  "Create owner account": "Create the owner identity and personal Workspace, establish the authenticated session, and enter that Workspace.",
  "Authenticate owner": "Validate the submitted credentials, establish the owner session, and resume only the Workspace authorized for that owner.",
  "Request password recovery": "Create an account-neutral recovery request and request delivery of a one-time recovery link when an eligible account exists.",
  "Change owner password": "Replace the password using a valid one-time recovery token, revoke existing sessions, and return the owner to sign-in.",
  "Request verification delivery": "Request a fresh one-time verification link for the signed-in owner and report the observed request result without claiming recipient delivery.",
  "Confirm owner email": "Validate the one-time verification token, mark the bound owner email as verified, and refresh owner state.",
  "Navigate from Workspace overview": "Open the selected owning feature while preserving the authenticated Workspace and conversation context.",
  "Open relevant product feature": "Open the feature relevant to the product question while preserving the authenticated Workspace context.",
  "Navigate to owning feature": "Move the active task to its owning feature and carry forward the task and conversation context.",
  "Navigate to Workspace destination": "Open the owner-selected Workspace feature without creating or changing a domain record.",
  "Sign out": "Revoke the current browser session and owner route handle, clear browser credentials, and return to a fresh Lounge.",
  "Open agent creation": "Open the new-agent design path without creating an agent, runnable version, or deployment.",
  "Create agent": "Create one Workspace-owned agent from the validated identity fields and open the new agent for inspection.",
  "Save agent changes": "Persist the validated editable fields on the selected agent while leaving existing versions and deployments unchanged.",
  "Attach source to agent": "Persist one association between the selected eligible Workspace source and the originating agent.",
  "Open source creation": "Open Source Hub in creation mode while retaining the originating agent as the return context.",
  "Attach newly created source": "Attach the successfully created eligible source to the originating agent and return to that agent.",
  "Open attached source": "Open the selected source in its owning feature while retaining the originating agent as return context.",
  "Archive agent": "Move the confirmed agent out of the active list while preserving it as an archived record.",
  "Delete agent": "Permanently remove the confirmed agent only when its dependencies permit deletion.",
  "Open API source creation": "Open API Source for a new source while preserving any calling-agent attachment context.",
  "Attach selected source": "Persist the selected eligible source on the originating agent and return to that agent.",
  "Delete API source": "Permanently remove the confirmed API source only when its attachments and processing state permit deletion.",
  "Open API description editor": "Open the selected API source at its Markdown description input while preserving Source Hub return context.",
  "Upload YAML": "Submit the owner-selected OpenAPI YAML file for format and file-limit validation.",
  "Accept API revision": "Create an identifiable API source revision from the validated OpenAPI YAML file.",
  "Save API description": "Persist the validated Markdown description on the selected API source without changing its OpenAPI revision.",
  "Save API connection": "Persist the validated connection settings and private credential references on the selected API connection profile.",
  "Test API connection": "Run an explicitly requested safe check against the selected API connection profile and return the observed result.",
  "Process API through ToolRouter": "Run ToolRouter for the exact accepted revision, persist its real artifacts, and update that revision's processing state.",
  "Control graph replay": "Change the playback position of the persisted construction trace without rerunning processing or mutating the graph.",
  "Save operation curation": "Persist the owner's exact included and excluded discovered operations for the selected API revision.",
  "Retry API processing": "Start a new attempt for the failed processing step using the corrected input while retaining the original failure evidence.",
}

type OperationContract = Pick<OperationDesign, "inputs" | "outcomes" | "safetyAndReview" | "recovery">

const OPERATION_CONTRACTS: Record<string, OperationContract> = {
  "Start product help": {
    inputs: "A public question about Corpus or an explicit choice to ask for product help. No account credentials or private Workspace state.",
    outcomes: "Product-help context becomes active and the question can be answered under Lounge rules. If the context cannot open, Lounge home remains active and no answer is claimed.",
    safetyAndReview: "Keep the interaction about Corpus only. Do not perform the visitor's task, expose private state, or describe unknown product behavior as available.",
    recovery: "Keep Lounge home active, state that product help could not be opened, and invite the visitor to try again without substituting an ungrounded answer.",
  },
  "Open owner registration": {
    inputs: "The visitor explicitly chooses account creation. No account or credential submission occurs during navigation.",
    outcomes: "The owner-registration surface becomes visible while the public conversation remains available. Navigation failure leaves the current Lounge behavior unchanged.",
    safetyAndReview: "Do not imply that an account exists or has been created. Credentials remain outside chat and are collected only by the private registration surface.",
    recovery: "Remain in the current Lounge behavior, report that registration could not be opened, and allow another explicit attempt.",
  },
  "Open owner sign-in": {
    inputs: "The visitor explicitly chooses sign-in. No credential validation occurs during navigation.",
    outcomes: "The owner sign-in surface becomes visible while the public conversation remains available. Navigation failure leaves the current Lounge behavior unchanged.",
    safetyAndReview: "Do not imply that the visitor is authenticated. Credentials remain outside chat and are collected only by the private sign-in surface.",
    recovery: "Remain in the current Lounge behavior, report that sign-in could not be opened, and allow another explicit attempt.",
  },
  "Return to Lounge": {
    inputs: "The visitor explicitly cancels or chooses to return. No pending form is submitted.",
    outcomes: "Public Lounge orientation becomes active without claiming that the behavior being left completed. If navigation fails, the current behavior remains visible.",
    safetyAndReview: "Do not submit credentials, consume one-time tokens, or retain incomplete private-form values as part of returning.",
    recovery: "Keep the current behavior visible, report that Lounge could not be opened, and allow the visitor to retry or remain safely in place.",
  },
  "Create owner account": {
    inputs: "Valid private registration fields and the visitor's explicit Create account submission.",
    outcomes: "The owner identity, personal Workspace, authenticated session, and Workspace entry succeed as one accepted result. Validation, duplicate-account, persistence, or continuation failure produces no successful registration claim.",
    safetyAndReview: "Keep credentials private, do not reveal whether a submitted email is already registered, and claim completion only from the authenticated Workspace result.",
    recovery: "Keep the failure visible and allow the visitor to correct or resubmit the private form. Never retry automatically or claim a partially completed account flow.",
  },
  "Continue to Workspace": {
    inputs: "A valid authenticated owner session already established by the current browser context.",
    outcomes: "The Workspace authorized for that owner becomes active. Missing or invalid authenticated context remains a visible continuation failure.",
    safetyAndReview: "Never create an account, resubmit credentials, or accept a user-supplied Workspace identity while continuing.",
    recovery: "Remain on the current account surface, preserve the known authentication truth, and offer sign-in or another valid account path when authorization is unavailable.",
  },
  "Authenticate owner": {
    inputs: "Private email and password fields plus the visitor's explicit Sign in submission.",
    outcomes: "Valid credentials establish the owner session and open only the authorized Workspace. Every invalid, unavailable, or rejected attempt returns a generic sign-in failure and exposes no private state.",
    safetyAndReview: "Keep credentials outside chat, apply authentication limits, and do not distinguish unknown email, wrong password, disabled account, or other account-specific causes in public output.",
    recovery: "Keep the generic failure visible and allow an explicit retry or password-recovery choice. Never retry credentials automatically.",
  },
  "Open password recovery": {
    inputs: "The visitor explicitly chooses password recovery from sign-in. No account-existence check is exposed during navigation.",
    outcomes: "The account-neutral password-recovery request surface becomes visible. Navigation failure leaves sign-in unchanged.",
    safetyAndReview: "Do not reveal whether the entered or remembered email belongs to an account and do not transfer credentials from sign-in.",
    recovery: "Remain on sign-in, report that recovery could not be opened, and allow another explicit attempt or return to Lounge.",
  },
  "Request password recovery": {
    inputs: "A privately entered email address and the visitor's explicit recovery request.",
    outcomes: "Corpus accepts the request with the same generic confirmation regardless of account existence. Independently known delivery-service unavailability remains explicit; acceptance is not proof of delivery.",
    safetyAndReview: "Never reveal account existence, recipient-specific delivery status, a reset token, or the submitted email in chat. Apply request limits before accepting another request.",
    recovery: "Keep a delivery-system failure visible without identifying account existence. Allow a later explicit retry; never silently retry or substitute a success confirmation.",
  },
  "Change owner password": {
    inputs: "A captured valid one-time recovery token, valid private new-password fields, and explicit submission.",
    outcomes: "A valid request changes the password, revokes existing sessions, removes the token from visible state, and returns to sign-in. Missing, invalid, expired, or rejected requests leave the password unchanged.",
    safetyAndReview: "Never expose the token or passwords in chat or visible persisted state. Do not claim success until the password change and session revocation both complete.",
    recovery: "Show an explicit invalid, expired, or unavailable result and offer a new recovery request or return to Lounge. Never reuse or silently replace the token.",
  },
  "Request verification delivery": {
    inputs: "A signed-in owner with pending email verification and an explicit request for another verification message.",
    outcomes: "The request is accepted, rate-limited, or unavailable as observed. Acceptance is not proof of recipient delivery or successful verification, and permitted Workspace use remains available.",
    safetyAndReview: "Authorize the signed-in owner and enforce resend limits before requesting delivery. Do not expose tokens or recipient-specific mail-system details.",
    recovery: "Keep rate-limit or delivery-service failure visible and allow return to Workspace. Never resend automatically or present a failed request as accepted.",
  },
  "Return to Workspace": {
    inputs: "The signed-in owner explicitly chooses to return. No verification request or token confirmation is performed.",
    outcomes: "The authenticated Workspace becomes active without changing or overstating email-verification state.",
    safetyAndReview: "Do not treat pending verification as a blocker unless a separately designed product rule requires it.",
    recovery: "Keep the verification behavior visible, report that Workspace could not be opened, and preserve the actual verification state.",
  },
  "Confirm owner email": {
    inputs: "A captured one-time verification token from the matching verification route and the owner's explicit confirmation action.",
    outcomes: "A valid token updates the bound email and refreshed owner state confirms it as verified. Missing, invalid, expired, or rejected tokens remain explicit failures with no verified claim.",
    safetyAndReview: "Keep the token out of the visible URL, chat, and persisted visible state. Never claim verification from token acceptance alone; require refreshed owner-state evidence.",
    recovery: "Show the exact valid user-facing failure category, preserve the unverified state, and offer a new verification request or safe return without silently retrying.",
  },
}

function operationContract(operationName: string): OperationContract {
  return OPERATION_CONTRACTS[operationName] ?? { inputs: "", outcomes: "", safetyAndReview: "", recovery: "" }
}

function operationIntendedEffect(operationName: string): string {
  const intendedEffect = OPERATION_INTENDED_EFFECTS[operationName]
  if (!intendedEffect) throw new Error(`Missing intended effect for Operation: ${operationName}`)
  return intendedEffect
}

const NODE_TEMPLATE_SEED: Record<string, NodeTemplate[]> = {
  lounge: [
    {
      name: "Public Lounge",
      context: "Unauthenticated starting location for public product help and entry into owner account paths.",
      policies: [
        "Use public Corpus context only and never expose or imply access to a private Workspace.",
        "Present current public help and account paths truthfully, distinguishing unavailable or deferred behavior.",
      ],
      capabilities: [
        {
          name: "Lounge entry",
          purpose: "Establish the unauthenticated Lounge context and present Lounge home.",
          policies: [
            "Establish only unauthenticated public context.",
            "Complete entry when Lounge home is visible; do not start or claim completion of any downstream behavior.",
          ],
        },
        {
          name: "Product help",
          purpose: "Answer unauthenticated questions about Corpus and direct task requests to account access.",
          policies: [
            "Answer from current product knowledge and label planned, deferred, unknown, or unavailable behavior explicitly.",
            "Keep help about Corpus only; do not design, plan, troubleshoot, or perform the visitor's task in Lounge.",
            "When a visitor starts describing work they want Corpus to perform, explain the private Workspace boundary and ask them to sign in or sign up.",
          ],
        },
      ],
    },
    {
      name: "Owner registration",
      context: "Public account-creation location where a visitor supplies the information needed to become a Corpus owner.",
      policies: [
        "Keep credential input private and do not expose authenticated Workspace state before account creation and continuation succeed.",
        "Treat owner identity, personal Workspace, authenticated session, and Workspace entry as one accepted registration result.",
      ],
      capabilities: [
        {
          name: "Create owner account",
          purpose: "Validate account details, create the owner identity and personal Workspace, and continue into authenticated context.",
          policies: [
            "Create an account only from explicit valid input and never repeat password values in chat or visible confirmation.",
            "On validation, duplicate-account, persistence, or continuation failure, keep registration unsuccessful and expose no account-existence detail.",
          ],
        },
      ],
    },
    {
      name: "Owner sign-in",
      context: "Public credential location for resuming the Workspace authorized to an existing owner.",
      policies: [
        "Keep credentials private and expose no Workspace facts until authentication succeeds.",
        "Invalid authentication remains a visible failure and must not reveal whether unrelated private state exists.",
      ],
      capabilities: [
        {
          name: "Authenticate owner",
          purpose: "Validate owner credentials and resume only the authorized Workspace.",
          policies: [
            "Use the authenticated identity as the authority for Workspace selection; never accept a user-supplied Workspace target as authority.",
            "Describe sign-in as complete only after authentication and Workspace continuation both succeed.",
          ],
        },
      ],
    },
    {
      name: "Password recovery",
      context: "Public recovery location covering an account-neutral reset request and a one-time password-change continuation.",
      policies: [
        "Protect account existence during recovery requests and keep one-time recovery tokens out of visible URLs and product output.",
        "A missing, invalid, used, or expired token changes nothing and remains an explicit failure.",
      ],
      capabilities: [
        {
          name: "Request recovery",
          purpose: "Request password-reset delivery without disclosing whether the submitted account exists.",
          policies: [
            "Use the same account-neutral response for existing and non-existing accounts.",
            "Report delivery-system unavailability without disclosing account existence or claiming delivery success.",
          ],
        },
        {
          name: "Set new password",
          purpose: "Validate a one-time recovery link, change the password, and revoke existing sessions.",
          policies: [
            "Accept only a valid unexpired one-time token bound to the recovery request.",
            "Claim success only after the password changes and existing sessions are revoked; then return the owner to sign-in.",
          ],
        },
      ],
    },
    {
      name: "Email verification",
      context: "Owner-email verification location covering delivery of a new link and confirmation through a one-time link.",
      policies: [
        "Keep one-time verification tokens out of the visible URL, chat, and persisted visible state.",
        "Pending verification must not block otherwise permitted Workspace behavior unless a separate product rule explicitly requires it.",
      ],
      capabilities: [
        {
          name: "Request verification delivery",
          purpose: "Request a fresh verification message for the signed-in owner's pending email.",
          policies: [
            "Operate only on the signed-in owner and send only after an explicit request.",
            "Report request acceptance, rate limiting, or service unavailability without describing acceptance as recipient delivery or successful verification.",
          ],
        },
        {
          name: "Confirm owner email",
          purpose: "Validate a one-time verification link and refresh owner verification state.",
          policies: [
            "Apply verification only to the owner account bound to a valid unexpired token.",
            "Refresh and present verified state only after confirmation succeeds; token failure changes nothing.",
          ],
        },
      ],
    },
  ],
  workspace: [
    {
      name: "Workspace home",
      context: "Authenticated home for overviewing the owner's Workspace and continuing work in the feature that owns it.",
      policies: [
        "Use only the authenticated owner's authorized Workspace facts and distinguish empty state from unavailable information.",
        "Keep this location focused on overview, guidance, and navigation; do not mutate domain records here.",
      ],
      capabilities: [
        {
          name: "Workspace overview",
          purpose: "Present agents, sources, recent activity, and honest empty states for the current Workspace.",
          policies: [
            "Use authoritative current counts and activity only; never fabricate recent work or infer records from navigation history.",
            "Offer deeper inspection through the owning feature when the overview is insufficient.",
          ],
        },
        {
          name: "Product guidance",
          purpose: "Answer general Corpus questions without discarding authenticated Workspace context.",
          policies: [
            "Use current product knowledge and preserve the active Workspace while answering.",
            "Offer only next actions actually available to the owner in the current product state.",
          ],
        },
        {
          name: "Task routing",
          purpose: "Identify the feature that owns a requested task and continue the same conversation there.",
          policies: [
            "Ask for clarification when the intended feature or resource is materially ambiguous.",
            "Carry the task and relevant context forward; navigation is not task completion.",
          ],
        },
        {
          name: "Owner session",
          purpose: "End current browser access and return to a fresh public Lounge when the owner signs out.",
          policies: [
            "Sign out only after explicit owner intent and keep the Workspace and its resources unchanged.",
            "Claim completion only after current browser access and route capability are revoked and public Lounge context is established.",
          ],
        },
      ],
    },
  ],
  agents: [
    {
      name: "Agents home",
      context: "Authenticated inventory location for viewing Workspace agents and starting agent creation.",
      policies: [
        "Use only agents owned by the authenticated Workspace and present lifecycle state from authoritative records.",
        "Agent existence never implies that a runnable version or active deployment exists.",
      ],
      capabilities: [
        {
          name: "Agent inventory",
          purpose: "List agents with identity, lifecycle state, and valid next actions.",
          policies: [
            "Distinguish configured, runnable, deployed, archived, empty, and unavailable states.",
            "Never infer lifecycle state from an agent name, recent activity, or the presence of configuration alone.",
          ],
        },
        {
          name: "Agent creation",
          purpose: "Create a Workspace-owned agent from its required identity and goal inputs.",
          policies: [
            "Create one agent only from explicit valid name, description, and goal input.",
            "Creation produces an agent record only; it does not produce a runnable version, evaluation, channel, or deployment.",
          ],
        },
      ],
    },
    {
      name: "Agent detail",
      context: "Authenticated location for inspecting and changing one selected agent and coordinating its owned handoffs.",
      policies: [
        "Keep every presented or changed fact bound to the exact selected agent.",
        "Keep current configuration, historical runnable versions, and active deployment state distinct.",
      ],
      capabilities: [
        {
          name: "Agent configuration",
          purpose: "Inspect and edit the selected agent's identity and configuration inputs.",
          policies: [
            "Expose editable inputs separately from immutable historical versions and private bindings.",
            "Saving configuration never silently rewrites an existing runnable or deployed version.",
          ],
        },
        {
          name: "Source attachments",
          purpose: "Inspect, attach, create, and open sources associated with the selected agent.",
          policies: [
            "Attach only eligible sources from the same Workspace and prevent duplicate attachment.",
            "Preserve the selected agent across Source Hub and API Source handoffs; navigation alone does not attach or edit a source.",
          ],
        },
        {
          name: "Agent lifecycle",
          purpose: "Archive or permanently delete the exact selected agent with appropriate consequence awareness.",
          policies: [
            "Identify the target, lifecycle state, deployment state, dependencies, and blockers before confirmation.",
            "Archive and delete remain distinct; consequential actions require explicit confirmation and authoritative completion or visible failure.",
          ],
        },
      ],
    },
  ],
  "source-hub": [
    {
      name: "Source Hub",
      context: "Authenticated inventory and handoff location for Workspace sources that may be attached to agents.",
      policies: [
        "Use only sources owned by the authenticated Workspace and present type, readiness, and attachment state truthfully.",
        "At launch expose API sources only; navigation to another feature never implies that a source was created, changed, attached, or deleted.",
      ],
      capabilities: [
        {
          name: "Source inventory",
          purpose: "List Workspace sources, readiness, and the agents that use them.",
          policies: [
            "Distinguish empty, processing, ready, failed, attached, and unavailable source states.",
            "Do not imply support for database, knowledge, or MCP source families during the API-only launch scope.",
          ],
        },
        {
          name: "API source entry",
          purpose: "Start API-source creation or description work in the API Source feature.",
          policies: [
            "Enter API Source only from Source Hub with the exact selected source or new-source intent.",
            "Preserve any originating agent context and do not claim source creation before API Source completes it.",
          ],
        },
        {
          name: "Agent source selection",
          purpose: "Select an eligible existing source for the originating agent and return with it attached.",
          policies: [
            "Show only same-Workspace eligible sources, including readiness and existing attachment state.",
            "Attach only the exact owner-selected source and claim completion only after the association is persisted.",
          ],
        },
        {
          name: "Source lifecycle",
          purpose: "Delete an exact API source when its agent attachments and other dependencies permit removal.",
          policies: [
            "Show the selected source, attachments, processing state, and blockers before explicit confirmation.",
            "Do not delete while declared blockers remain; authoritative deletion or visible failure is required.",
          ],
        },
      ],
    },
  ],
  "api-source": [
    {
      name: "API intake",
      context: "API Source location for accepting an OpenAPI YAML revision and optional supporting Markdown description.",
      policies: [
        "Keep specification and description inputs distinct and bind every accepted change to the exact Workspace-owned API source.",
        "Reject invalid inputs explicitly and never substitute fixtures, samples, or synthetic content.",
      ],
      capabilities: [
        {
          name: "Specification revisions",
          purpose: "Validate an OpenAPI YAML file and create an identifiable accepted source revision.",
          policies: [
            "Enforce documented format and file limits; invalid input creates no accepted revision.",
            "Bind subsequent connection, processing, graph, and curation state to the exact accepted revision.",
          ],
        },
        {
          name: "Description context",
          purpose: "Validate and save Markdown guidance that helps Corpus understand the selected API.",
          policies: [
            "Treat Markdown as supporting context rather than as the API specification and render it without active content execution.",
            "A failed description update must not replace the previously persisted valid description.",
          ],
        },
      ],
    },
    {
      name: "API connection",
      context: "API Source location for configuring one source revision's environment, base URL, authentication, and credentials.",
      policies: [
        "Keep configuration bound to the exact source revision and named environment or profile.",
        "Keep credentials, tokens, and private connection bindings masked and out of chat, logs, and generated artifacts.",
      ],
      capabilities: [
        {
          name: "Connection profiles",
          purpose: "Save connection settings and perform an explicitly requested safe connection check.",
          policies: [
            "Keep saving configuration and testing a connection as distinct owner actions.",
            "A failed check remains a failure; never switch endpoint, environment, credentials, or provider silently.",
          ],
        },
      ],
    },
    {
      name: "API processing",
      context: "API Source location for running and monitoring the real ToolRouter pipeline for one accepted revision.",
      policies: [
        "Use the real ToolRouter pipeline for the exact revision and present only observed processing states and persisted artifacts.",
        "Never invent progress, substitute cached or synthetic success, or mark a revision ready before required processing completes.",
      ],
      capabilities: [
        {
          name: "ToolRouter processing",
          purpose: "Start one processing run, expose real phases, and produce the semantic graph and operation inventory.",
          policies: [
            "Start only after explicit owner request and satisfied prerequisites; avoid duplicate concurrent runs for the same revision.",
            "Keep active, completed, failed, and ready states distinct and supported by actual evidence.",
          ],
        },
        {
          name: "Processing recovery",
          purpose: "Preserve failure evidence, accept a valid correction, and explicitly retry the affected processing step.",
          policies: [
            "Keep the failed step, evidence, revision, and valid corrective actions visible; never retry automatically.",
            "If correction creates a new revision, preserve the prior failure and identify the new revision before reporting success.",
          ],
        },
      ],
    },
    {
      name: "API graph",
      context: "API Source location for inspecting the persisted semantic graph and replaying its recorded construction evidence.",
      policies: [
        "Use only graph artifacts produced for the exact selected revision and retain source evidence for presented nodes and edges.",
        "Do not describe persisted inspection or replay as live ToolRouter processing.",
      ],
      capabilities: [
        {
          name: "Graph inspection",
          purpose: "Explore persisted nodes and relationships for the selected API revision.",
          policies: [
            "If graph artifacts are unavailable, show that state explicitly rather than constructing a synthetic graph.",
            "Never mix nodes, edges, or evidence from another API source or revision.",
          ],
        },
        {
          name: "Construction replay",
          purpose: "Replay recorded graph-construction events with pause, resume, and step controls.",
          policies: [
            "Replay events only in recorded order and keep playback controls from mutating or rerunning the graph.",
            "Label replay as recorded evidence and never claim live streaming when no live stream exists.",
          ],
        },
      ],
    },
    {
      name: "API operation curation",
      context: "API Source location for reviewing discovered operations and saving the exact subset available to downstream agent design.",
      policies: [
        "Use only operations discovered for the selected revision and distinguish included from excluded operations visibly.",
        "Never invent, rename, infer, or silently broaden the owner's operation selection.",
      ],
      capabilities: [
        {
          name: "Operation selection",
          purpose: "Persist explicit inclusion decisions for the exact discovered operation inventory.",
          policies: [
            "Treat inspection, search, or filtering as non-mutating; save only explicit owner selections.",
            "Bind the saved selection to the revision and require review when a new revision changes the discovered inventory.",
          ],
        },
      ],
    },
  ],
}

const BEHAVIOR_NODE_TEMPLATE: Record<string, [featureId: string, nodeName: string, capabilityNames: string | string[]]> = {
  "lounge-arrival": ["lounge", "Public Lounge", "Lounge entry"],
  "lounge-product-help": ["lounge", "Public Lounge", "Product help"],
  "owner-auth-register": ["lounge", "Owner registration", "Create owner account"],
  "owner-auth-sign-in": ["lounge", "Owner sign-in", "Authenticate owner"],
  "owner-auth-request-reset": ["lounge", "Password recovery", "Request recovery"],
  "owner-auth-confirm-reset": ["lounge", "Password recovery", "Set new password"],
  "owner-auth-request-verification": ["lounge", "Email verification", "Request verification delivery"],
  "owner-auth-confirm-verification": ["lounge", "Email verification", "Confirm owner email"],
  "enter-workspace": ["workspace", "Workspace home", "Workspace overview"],
  "workspace-activity-help": ["workspace", "Workspace home", "Workspace overview"],
  "workspace-product-help": ["workspace", "Workspace home", "Product guidance"],
  "workspace-route-task": ["workspace", "Workspace home", "Task routing"],
  "workspace-quick-actions": ["workspace", "Workspace home", "Task routing"],
  "owner-auth-sign-out": ["workspace", "Workspace home", "Owner session"],
  "agents-view": ["agents", "Agents home", "Agent inventory"],
  "agents-create": ["agents", "Agents home", "Agent creation"],
  "agents-inspect": ["agents", "Agent detail", "Agent configuration"],
  "agents-edit": ["agents", "Agent detail", "Agent configuration"],
  "agents-attach-source": ["agents", "Agent detail", "Source attachments"],
  "agents-create-source": ["agents", "Agent detail", "Source attachments"],
  "agents-open-source": ["agents", "Agent detail", "Source attachments"],
  "agents-archive": ["agents", "Agent detail", "Agent lifecycle"],
  "agents-delete": ["agents", "Agent detail", "Agent lifecycle"],
  "sources-view": ["source-hub", "Source Hub", "Source inventory"],
  "sources-start-api": ["source-hub", "Source Hub", "API source entry"],
  "sources-select-for-agent": ["source-hub", "Source Hub", "Agent source selection"],
  "sources-delete": ["source-hub", "Source Hub", "Source lifecycle"],
  "sources-start-description": ["source-hub", "Source Hub", "API source entry"],
  "api-upload-yaml": ["api-source", "API intake", "Specification revisions"],
  "api-description": ["api-source", "API intake", "Description context"],
  "api-configure-connection": ["api-source", "API connection", "Connection profiles"],
  "api-process-toolrouter": ["api-source", "API processing", "ToolRouter processing"],
  "api-monitor-processing": ["api-source", "API processing", "ToolRouter processing"],
  "api-inspect-graph": ["api-source", "API graph", "Graph inspection"],
  "api-replay-graph": ["api-source", "API graph", "Construction replay"],
  "api-curate-operations": ["api-source", "API operation curation", "Operation selection"],
  "api-recover-processing": ["api-source", "API processing", "Processing recovery"],
}

const SUGGESTED_ACTION_OPERATION: Record<string, string> = {
  "product-help-sign-in": "Open owner sign-in",
  "product-help-sign-up": "Open owner registration",
  "register-submit": "Create owner account",
  "register-continue": "Continue to Workspace",
  "sign-in-submit": "Authenticate owner",
  "sign-in-continue": "Continue to Workspace",
  "request-reset-submit": "Request password recovery",
  "confirm-reset-submit": "Change owner password",
  "resend-verification": "Request verification delivery",
  "verification-return": "Return to Workspace",
  "confirm-verification": "Confirm owner email",
  "workspace-manage-agents": "Navigate to Workspace destination",
  "workspace-manage-sources": "Navigate to Workspace destination",
  "workspace-manage-operations": "Navigate to Workspace destination",
  "sign-out": "Sign out",
  "agents-create": "Open agent creation",
  "agents-create-confirm": "Create agent",
  "agents-save": "Save agent changes",
  "agents-attach-existing": "Attach source to agent",
  "agents-create-source": "Open source creation",
  "agents-archive-confirm": "Archive agent",
  "agents-delete-confirm": "Delete agent",
  "sources-add-api": "Open API source creation",
  "sources-open-api": "Open API source creation",
  "sources-select": "Attach selected source",
  "sources-delete-confirm": "Delete API source",
  "sources-add-description": "Open API description editor",
  "api-upload": "Upload YAML",
  "api-description-upload": "Save API description",
  "api-save-connection": "Save API connection",
  "api-test-connection": "Test API connection",
  "api-process": "Process API through ToolRouter",
  "api-replay-start": "Control graph replay",
  "api-replay-step": "Control graph replay",
  "api-save-operations": "Save operation curation",
  "api-retry": "Retry API processing",
}

function nodeDesign(id: string, operationNames: string[], surfaceNames: string[]): Pick<DesignStory, "nodePolicies" | "capabilities"> {
  const mapping = BEHAVIOR_NODE_TEMPLATE[id]
  if (!mapping) return { nodePolicies: [], capabilities: [] }
  const [featureId, nodeName, capabilitySelection] = mapping
  const capabilityNames = Array.isArray(capabilitySelection) ? capabilitySelection : [capabilitySelection]
  const node = NODE_TEMPLATE_SEED[featureId]?.find((item) => item.name === nodeName)
  const capabilities = node?.capabilities.filter((item) => capabilityNames.includes(item.name)) ?? []
  return {
    nodePolicies: [
      ...(node?.policies ?? []),
    ],
    capabilities: capabilities.map((capability) => ({
      ...capability,
      policies: [...capability.policies],
      operationNames,
      surfaceNames,
    })),
  }
}

function scopedDesign(id: string, title: string): { surfaces: SurfaceDesign[]; operations: OperationDesign[] } {
  const groupedSurfaces = new Map<string, string[]>()
  const groupedOperations = new Map<string, string[]>()
  for (const [scope, scopeName, instruction] of BEHAVIOR_POLICY_SEED[id] ?? []) {
    const target = scope === "surface" ? groupedSurfaces : groupedOperations
    target.set(scopeName, [...(target.get(scopeName) ?? []), instruction])
  }
  return {
    surfaces: [...groupedSurfaces].map(([name, policies]) => ({
      name,
      purpose: `Present the structured product UI required for “${title}”.`,
      policies,
    })),
    operations: [...groupedOperations].map(([name, policies]) => ({
      name,
      purpose: operationIntendedEffect(name),
      ...operationContract(name),
      policies,
    })),
  }
}

function story(
  id: string,
  title: string,
  userIntent: string,
  agentIntent: string,
  behavior: string,
  ownerMessage: string,
  corpusMessage: string,
  options: StoryOptions = {},
): DesignStory {
  const scoped = scopedDesign(id, title)
  const operations = [...scoped.operations]
  const suggestedActions = (options.suggestedActions ?? []).map((action) => {
    const operationName = SUGGESTED_ACTION_OPERATION[action.id] ?? action.label
    if (!operations.some((operation) => operation.name === operationName)) {
      operations.push({
        name: operationName,
        purpose: operationIntendedEffect(operationName),
        ...operationContract(operationName),
        policies: [],
      })
    }
    return { ...action, operationName, visibility: "" }
  })
  const node = nodeDesign(id, operations.map((operation) => operation.name), scoped.surfaces.map((surface) => surface.name))
  return {
    id,
    title,
    userIntent,
    agentIntent,
    expectedBehavior: behavior,
    messages: [
      { id: `${id}-owner`, actor: "Owner", content: ownerMessage },
      { id: `${id}-corpus`, actor: "Corpus", content: corpusMessage },
    ],
    mockSurfacePath: options.surface ?? null,
    ...node,
    surfaces: scoped.surfaces,
    operations,
    suggestedActions,
    behaviorEvals: loungeBehaviorEvals(id),
    evalExemptions: [],
    status: options.status ?? "draft",
    rejectionReason: "",
  }
}

function policies(_scopeName: string, instructions: string[]): string[] {
  return instructions
}

export function createSeedState(): WorkbenchState {
  return {
    features: [
      {
        id: "lounge",
        name: "Lounge",
        prompt: "You are Corpus in the public Lounge, an unauthenticated helpdesk about Corpus only. Answer questions about Corpus, its current features, and how the product works. Do not design, plan, troubleshoot, or perform the visitor's task in Lounge. When a visitor starts describing work they want Corpus to do, briefly explain that work happens in a private Workspace and ask them to sign in or sign up through the available product surfaces. Never collect credentials in chat. On an assistant-initiated Lounge turn, briefly establish that the visitor is in the Lounge, explain that you can answer questions about Corpus, and invite a question about the product.",
        policies: policies("Lounge", [
          "Keep unauthenticated help strictly about Corpus and never expose private Workspace state.",
          "Answer questions about Corpus, but do not design, plan, troubleshoot, or perform a visitor's task in Lounge.",
          "When a visitor starts describing work they want Corpus to perform, explain that work requires a private Workspace and ask them to sign in or sign up.",
          "Offer sign-in and sign-up through the available product surfaces without collecting credentials in chat or implying that the visitor is authenticated.",
          "Describe only currently available Corpus behavior as available; label planned, deferred, unknown, or unavailable behavior explicitly.",
          "While Lounge is active, identify the product location as Lounge and keep private Workspace and feature navigation hidden until authenticated entry succeeds.",
          "Describe Lounge choices in user-facing product language and never expose internal operation, tool, Node, AgentPolicy, or identifier names.",
        ]),
        conversationEvals: copyConversationEvals(),
        stories: [
          story(
            "lounge-arrival",
            "Arrive in the Lounge",
            "Enter Corpus before signing in.",
            "Establish the unauthenticated Lounge context and present Lounge home.",
            "An unauthenticated visitor opens Corpus. Corpus establishes Lounge as the active public context, renders Lounge home, and begins the public conversation. Entry is complete when the visitor can see they are in Lounge; no product-help or account behavior has started.",
            "Open Corpus.",
            "You are in the Lounge.",
            { surface: "/mock-surfaces/lounge/home.html" },
          ),
          story(
            "lounge-product-help",
            "Ask Lounge for product help",
            "Understand Corpus, its features, or how the product works before signing in.",
            "Answer Corpus product questions truthfully, keep Lounge out of task execution, and direct task requests to sign-in or sign-up.",
            "A visitor asks about Corpus. Corpus answers only about the product from current knowledge. If the visitor starts describing work they want performed, Corpus does not continue the task; it explains that work requires a private Workspace and asks the visitor to sign in or sign up. Unknown or unavailable product information remains explicit.",
            "I want to connect an agent to my ecommerce site.",
            "That is work you can do in a private Corpus Workspace. Sign in if you already have an account, or sign up to get started.",
            { suggestedActions: [{ id: "product-help-sign-in", label: "Sign in" }, { id: "product-help-sign-up", label: "Sign up" }] },
          ),
          story(
            "owner-auth-register",
            "Create an owner account",
            "Create an account and enter my private Workspace.",
            "Create the owner identity, personal Workspace, authenticated session, and Workspace entry as one accepted registration result.",
            "A Lounge visitor signs up with valid private account details. Corpus completes owner identity, personal Workspace, authenticated session, and Workspace entry before claiming success. Validation, duplicate-account, persistence, or continuation failure remains an unsuccessful registration result and does not reveal whether the email is already registered.",
            "I want to create an account.",
            "Sign up here. When account creation completes, I will take you into your Workspace.",
            { suggestedActions: [{ id: "register-submit", label: "Sign up" }, { id: "register-continue", label: "Continue to Workspace" }], surface: "/mock-surfaces/workspace/authentication.html#register" },
          ),
          story(
            "owner-auth-sign-in",
            "Sign in",
            "Return to the private Workspace associated with my account.",
            "Authenticate the owner and resume only the Workspace authorized for that account.",
            "An existing owner signs in from Lounge with email and password. Corpus resumes only that owner's Workspace. Invalid credentials remain a visible failure and do not open private state.",
            "I already have a Corpus account.",
            "Sign in to resume the Workspace associated with your account.",
            { suggestedActions: [{ id: "sign-in-submit", label: "Sign in" }, { id: "sign-in-continue", label: "Continue to Workspace" }], surface: "/mock-surfaces/workspace/authentication.html#sign-in" },
          ),
          story(
            "owner-auth-request-reset",
            "Request password recovery",
            "Regain access because I cannot use my current password.",
            "Accept a reset request without revealing whether the account exists and distinguish a known delivery-service outage from recipient-specific delivery results.",
            "A visitor submits an email for password recovery. Corpus shows the same generic confirmation whether or not the account exists. A delivery-service outage may be reported only when it is known independently of the submitted account; recipient-specific delivery results never reveal account existence.",
            "I forgot my password.",
            "Enter your email to request recovery. The confirmation will not reveal whether an account exists.",
            { suggestedActions: [{ id: "request-reset-submit", label: "Send recovery link" }], surface: "/mock-surfaces/workspace/authentication.html#request-reset" },
          ),
          story(
            "owner-auth-confirm-reset",
            "Set a new password",
            "Replace my password with a valid one-time recovery link.",
            "Validate the link, change the password, revoke existing access, and return the owner to sign-in.",
            "An owner opens a one-time reset link and chooses a new password. Corpus removes the token from the visible URL, changes the password, revokes existing sessions, and returns to sign-in. Missing, invalid, or expired links remain explicit failures.",
            "Use this recovery link and change my password.",
            "Choose a new password. Completing this will sign out existing sessions and return you to sign-in.",
            { suggestedActions: [{ id: "confirm-reset-submit", label: "Set new password" }], surface: "/mock-surfaces/workspace/authentication.html#reset-password" },
          ),
          story(
            "owner-auth-request-verification",
            "Resend email verification",
            "Receive a fresh verification email for my signed-in account.",
            "Request a new verification message and distinguish request acceptance, rate limiting, and service unavailability without claiming recipient delivery.",
            "A signed-in owner whose email is pending verification asks for another verification message. Corpus reports whether the request was accepted, rate-limited, or unavailable; acceptance is not presented as recipient delivery or successful verification, and permitted Workspace use remains available.",
            "Send the verification email again.",
            "I will request a fresh verification message and report whether the request is accepted, limited, or unavailable.",
            { suggestedActions: [{ id: "resend-verification", label: "Resend verification" }, { id: "verification-return", label: "Return to Workspace" }] },
          ),
          story(
            "owner-auth-confirm-verification",
            "Confirm email verification",
            "Confirm that the email address belongs to my owner account.",
            "Validate the one-time link, refresh owner state, and show confirmation or an explicit token failure.",
            "An owner opens a one-time verification link. Corpus removes its token from the visible URL, verifies the address, refreshes owner state, and shows the result. Missing, invalid, or expired links remain explicit failures.",
            "Verify this email address.",
            "I will validate the one-time link and show the verification result.",
            { suggestedActions: [{ id: "confirm-verification", label: "Verify email" }], surface: "/mock-surfaces/workspace/authentication.html#verify-email" },
          ),
        ],
      },
      {
        id: "workspace",
        name: "Workspace",
        conversationEvals: [],
        prompt: "You are Corpus in the owner's authenticated Workspace. Help the owner understand their current Workspace and move deliberately among the available private features, using only current RouteDeck context and legal operations.",
        policies: policies("Workspace", [
          "Use only the authenticated owner's authorized Workspace context.",
          "Keep Workspace home oriented toward overview, navigation, and continuation; do not edit domain records here.",
        ]),
        stories: [
          story(
            "enter-workspace",
            "Enter the Workspace",
            "See the current state of my private Workspace and choose what to do next.",
            "Establish the authenticated Workspace and provide a truthful overview of agents, sources, and activity.",
            "An authenticated owner enters their one launch Workspace. Corpus shows its agents, sources, and recent activity, including honest empty states. Workspace home does not add or modify domain records.",
            "Show me my Workspace.",
            "Here is the current overview of your agents, sources, and recent activity.",
          ),
          story(
            "workspace-activity-help",
            "Ask about Workspace activity",
            "Understand what exists or recently happened in my Workspace.",
            "Answer from authorized Workspace state and distinguish current facts from unavailable information.",
            "The owner asks about agents, sources, activity, or another Workspace fact. Corpus answers from the owner's authorized Workspace state and links the answer to the relevant feature when deeper inspection is useful.",
            "What changed in my Workspace today?",
            "I will summarize the activity visible in this Workspace and point you to the affected resources.",
          ),
          story(
            "workspace-product-help",
            "Ask about Corpus while signed in",
            "Get general product guidance without leaving my Workspace context.",
            "Answer the product question while preserving the authenticated Workspace as active context.",
            "An authenticated owner asks how Corpus or one of its features works. Corpus answers without discarding the current Workspace context and makes any relevant next action available.",
            "How do evaluations relate to an agent version?",
            "Evaluations run against an exact version and retain evidence. I can take you to Evaluation when you want to inspect or start one.",
          ),
          story(
            "workspace-route-task",
            "Continue a task in the correct feature",
            "Ask for any Corpus task and continue it where that work is owned.",
            "Recognize the owning feature, navigate there, and continue the same conversation without treating navigation as completion.",
            "The owner asks Workspace to perform a task owned elsewhere. Corpus navigates to the correct feature and continues the same conversation with the context needed for that task. Arrival at the feature is not presented as task completion.",
            "Attach the Orders API to my support agent.",
            "That work belongs with the agent's sources. I will open the relevant path and continue with the attachment choices there.",
          ),
          story(
            "workspace-quick-actions",
            "Use Workspace quick actions",
            "Move directly to a common area of my Workspace.",
            "Expose valid high-frequency destinations and navigate without modifying domain state.",
            "Workspace home presents quick actions for common destinations such as Agents, Sources, and Operations. Choosing one opens that feature; the quick action itself does not create or change a resource.",
            "I want to manage my agents.",
            "I will open Agents. Nothing changes until you choose an action there.",
            { suggestedActions: [
              { id: "workspace-manage-agents", label: "Manage agents" },
              { id: "workspace-manage-sources", label: "Manage sources" },
              { id: "workspace-manage-operations", label: "Manage operations" },
            ] },
          ),
          story(
            "owner-auth-sign-out",
            "Sign out to Lounge",
            "End access to my Workspace on this browser while keeping it private.",
            "Revoke current browser access and return to a fresh public Lounge without changing Workspace ownership.",
            "An authenticated owner signs out. Corpus revokes the browser session and owner route handle, clears browser credentials, and returns to a fresh Lounge. The Workspace and its resources remain private.",
            "Sign me out on this browser.",
            "I will end this browser session and return you to the Lounge. Your Workspace remains private.",
            { suggestedActions: [{ id: "sign-out", label: "Sign out" }], surface: "/mock-surfaces/workspace/authentication.html#sign-out", status: "approved" },
          ),
        ],
      },
      {
        id: "agents",
        name: "Agents",
        conversationEvals: [],
        prompt: "You are Corpus in the Agents feature. Help the owner define, inspect, test, and improve agents using the current agent design, evidence, and legal operations available in RouteDeck.",
        policies: policies("Agents", [
          "Keep every agent isolated to the authenticated owner's Workspace.",
          "Never describe an agent as runnable or deployed unless a corresponding version and deployment exist.",
          "Changes to an agent's current identity or configuration never rewrite existing runnable or deployed versions unless a separate versioning or deployment action explicitly does so.",
        ]),
        stories: [
          story(
            "agents-view",
            "View agents",
            "See the agents in my Workspace and their current lifecycle state.",
            "List only authorized agents with truthful status and useful next actions.",
            "The owner opens Agents. Corpus lists the Workspace's agents with enough identity and lifecycle information to distinguish them, including honest empty state and no implied deployment.",
            "Show me my agents.",
            "Here are the agents in this Workspace and the current state of each one.",
            { suggestedActions: [{ id: "agents-create", label: "Create agent" }] },
          ),
          story(
            "agents-create",
            "Create an agent",
            "Create an agent with a name, description, and goal.",
            "Collect the required identity fields, create the agent, and show the newly created agent without implying it is runnable or deployed.",
            "The owner provides an agent name, description, and goal. Corpus validates the required information, creates the agent in the Workspace, and opens it for inspection. Creating the agent does not create a runnable version or deployment.",
            "Create an agent for handling customer order questions.",
            "Provide its name, description, and goal. I will create the agent and then open it for you.",
            { suggestedActions: [{ id: "agents-create-confirm", label: "Create agent" }], surface: "/mock-surfaces/agents/create-agent.html" },
          ),
          story(
            "agents-inspect",
            "Inspect an agent",
            "Understand an agent's identity, configuration, sources, versions, and deployment state.",
            "Present the complete agent record and clearly distinguish configured, runnable, and deployed state.",
            "The owner opens an agent. Corpus brings together its identity, goals and non-goals, configuration inputs, attached sources, Agent Designer and RouteDeck configuration, runnable and deployed versions, and active deployment URL when one exists.",
            "Show me everything that defines this agent.",
            "I will show its identity, goals, configuration, sources, versions, and active deployment state in one place.",
          ),
          story(
            "agents-edit",
            "Edit an agent",
            "Change the agent's editable identity or configuration inputs.",
            "Validate and persist allowed edits while keeping versioned and deployed state truthful.",
            "The owner edits allowed agent fields such as name, description, goal, non-goals, or configuration inputs. Corpus shows what will change, saves valid edits, and does not silently rewrite existing runnable or deployed versions.",
            "Change this agent's goal to include order-status questions.",
            "I will update the agent's goal and keep existing version and deployment history distinct.",
            { suggestedActions: [{ id: "agents-save", label: "Save changes" }] },
          ),
          story(
            "agents-attach-source",
            "Attach an existing source",
            "Give this agent access to a source already in my Workspace.",
            "Present eligible sources, attach the selected source, and return to the agent with visible confirmation.",
            "The owner chooses to add a source to an agent and selects an existing Workspace source. Corpus attaches it once, returns to the agent, and shows the source in the agent's source list.",
            "Attach the Orders API source.",
            "I will attach that existing Workspace source and return to this agent.",
            { suggestedActions: [{ id: "agents-attach-existing", label: "Attach source" }] },
          ),
          story(
            "agents-create-source",
            "Create and attach a source",
            "Add a new source while working on an agent and return with it attached.",
            "Hand off to Source Hub, preserve the agent context, and attach the completed source on return.",
            "The owner chooses to add a source that does not yet exist. Corpus opens Source Hub in the context of the current agent. When source creation completes, Corpus returns to the agent and shows the new source attached; cancellation returns without attachment.",
            "This source is not in my Workspace yet.",
            "I will take you to Source Hub and return here with the completed source attached.",
            { suggestedActions: [{ id: "agents-create-source", label: "Add new source" }] },
          ),
          story(
            "agents-open-source",
            "Open an attached source",
            "Inspect or edit a source attached to this agent.",
            "Navigate to the source owner while preserving enough context to return to the agent.",
            "The owner selects an attached source for inspection or editing. Corpus navigates to that source in its owning feature and preserves the agent context for return. The Agents feature does not edit source-owned records itself.",
            "Open the Orders API source.",
            "I will open that source in its owning feature and keep this agent as the return context.",
          ),
          story(
            "agents-archive",
            "Archive an agent",
            "Remove an agent from my active working list without calling it deleted.",
            "Confirm the archive action, apply it to the selected agent, and show the resulting active-list state.",
            "The owner archives an agent after confirming the selected target. Corpus removes it from the active agent list and preserves a truthful distinction between archived and deleted state.",
            "Archive this agent.",
            "Confirm the agent you want to archive. It will leave the active list but will not be described as deleted.",
            { suggestedActions: [{ id: "agents-archive-confirm", label: "Archive agent" }] },
          ),
          story(
            "agents-delete",
            "Delete an agent",
            "Permanently remove an agent when it is safe and intended.",
            "Expose material dependencies, require confirmation, and either delete the exact agent or report blockers.",
            "The owner requests deletion. Corpus identifies the exact agent and any active deployment or other blockers before confirmation. It deletes only when permitted and visibly reports blocked or failed deletion without pretending success.",
            "Delete this agent permanently.",
            "I will check its dependencies and ask you to confirm the exact agent before permanent deletion.",
            { suggestedActions: [{ id: "agents-delete-confirm", label: "Delete permanently" }] },
          ),
        ],
      },
      {
        id: "source-hub",
        name: "Source Hub",
        conversationEvals: [],
        prompt: "You are Corpus in Source Hub. Help the owner understand, connect, inspect, and manage sources while keeping connection state and external outcomes grounded in RouteDeck and source-system evidence.",
        policies: policies("Source Hub", [
          "Expose only sources owned by the authenticated Workspace.",
          "At launch, offer API sources only; do not imply database, knowledge, or MCP support.",
          "Keep source readiness and agent-attachment state truthful; navigation between Source Hub, Agents, and API Source does not itself mutate either record.",
        ]),
        stories: [
          story(
            "sources-view",
            "View sources",
            "See the sources in my Workspace and which agents use them.",
            "List authorized sources with truthful type, status, and attachment context.",
            "The owner opens Source Hub. Corpus lists Workspace sources, their type and readiness, and the agents to which they are attached. At launch, API is the only available source family.",
            "Show me my sources.",
            "Here are your Workspace sources, their readiness, and their agent attachments.",
            { suggestedActions: [{ id: "sources-add-api", label: "Add API source" }] },
          ),
          story(
            "sources-start-api",
            "Start adding an API source",
            "Create a new API source from the one allowed launch entry point.",
            "Open API Source from Source Hub and preserve any calling-agent context.",
            "The owner chooses Add API source in Source Hub. Corpus opens API Source, the only launch source type, and carries forward the current agent context when the flow began from an attachment task.",
            "Add an API source.",
            "I will open API Source and keep your current attachment context if you arrived from an agent.",
            { suggestedActions: [{ id: "sources-open-api", label: "Add API source" }] },
          ),
          story(
            "sources-select-for-agent",
            "Select a source for an agent",
            "Choose an existing source and return to the agent with it attached.",
            "Show eligible sources, attach the selected one, and complete the handoff back to Agents.",
            "Source Hub is opened from an agent attachment task. The owner selects an eligible source. Corpus attaches it, returns to the originating agent, and shows the completed attachment.",
            "Use the Orders API for this agent.",
            "I will attach it and return to the agent that started this task.",
            { suggestedActions: [{ id: "sources-select", label: "Select source" }] },
          ),
          story(
            "sources-delete",
            "Delete an API source",
            "Remove an API source when its dependencies allow deletion.",
            "Show agent attachments and other blockers, require confirmation, and report the actual result.",
            "The owner requests deletion of an API source. Corpus shows attached agents or other material blockers before confirmation. It deletes only when permitted and keeps blocked or failed deletion visible.",
            "Delete this API source.",
            "I will show where it is used and ask for confirmation before deleting it.",
            { suggestedActions: [{ id: "sources-delete-confirm", label: "Delete source" }] },
          ),
          story(
            "sources-start-description",
            "Start adding an API description",
            "Provide helpful Markdown context for an API source.",
            "Open the selected API Source at its description input and preserve Source Hub context.",
            "The owner chooses to add a helpful Markdown description to an API source. Source Hub opens that source's API-specific description path, where file limits, validation, and persistence are owned, and returns to the source list afterward.",
            "Add a Markdown description to the Orders API.",
            "I will open that API source at its description input and return here when it is saved.",
            { suggestedActions: [{ id: "sources-add-description", label: "Add API description" }] },
          ),
        ],
      },
      {
        id: "api-source",
        name: "API Source",
        conversationEvals: [],
        prompt: "You are Corpus in the API Source feature. Help the owner configure and validate an API source from its declared contract, keeping credentials private and describing only connection and discovery outcomes that the product has confirmed.",
        policies: policies("API Source", [
          "Keep API specifications, credentials, artifacts, and processing isolated to the authenticated Workspace.",
          "Enter API Source only from Source Hub and keep processing failures explicit.",
          "Bind configuration, processing status, graph artifacts, operation selections, and recovery evidence to the exact API source revision they describe.",
          "Never expose stored credentials, tokens, or private connection bindings in chat, surfaces, logs, or generated artifacts.",
          "Present only real persisted ToolRouter results as processed artifacts; never substitute fixtures, synthetic graphs, cached success, or alternate processing paths.",
        ]),
        stories: [
          story(
            "api-upload-yaml",
            "Upload an API YAML file",
            "Create or revise an API source from an OpenAPI YAML file.",
            "Validate the file and size limits, persist an accepted revision, and report invalid input clearly.",
            "The owner uploads an OpenAPI YAML file from API Source. Corpus enforces the documented file limits and format, creates the source revision only when accepted, and shows validation failures without substituting sample data.",
            "Upload this OpenAPI YAML file.",
            "I will validate the file and create a source revision only if it is accepted.",
            { suggestedActions: [{ id: "api-upload", label: "Upload YAML" }] },
          ),
          story(
            "api-description",
            "Add or update the API description",
            "Give Corpus helpful Markdown context about how this API should be understood.",
            "Validate the Markdown file and save it to the selected API source without treating it as an API specification.",
            "The owner uploads a Markdown file that explains the API's purpose and usage. Corpus enforces explicit file limits, saves valid description content with the API source, and keeps invalid or failed uploads visible.",
            "Use this Markdown file to explain the Orders API.",
            "I will validate it as descriptive context and keep it separate from the OpenAPI specification.",
            { suggestedActions: [{ id: "api-description-upload", label: "Upload Markdown" }] },
          ),
          story(
            "api-configure-connection",
            "Configure the API connection",
            "Provide the base URL, authentication, and environment details needed to use this API.",
            "Collect non-secret configuration and private credentials safely, validate required fields, and report connection failures explicitly.",
            "The owner configures an environment or profile, base URL, authentication method, and required credentials. Corpus keeps secrets private, shows what will be used, and can perform an explicitly requested safe connection check. A failed check remains a failure.",
            "Configure the production base URL and API-key authentication.",
            "I will keep the credential private, show the non-secret connection settings, and only run a safe check when you request it.",
            { suggestedActions: [{ id: "api-save-connection", label: "Save connection" }, { id: "api-test-connection", label: "Test connection" }] },
          ),
          story(
            "api-process-toolrouter",
            "Process the API through ToolRouter",
            "Turn the accepted API revision into a semantic graph and operation inventory.",
            "Run the real ToolRouter pipeline for the exact revision and make success or failure visible.",
            "The owner starts processing for an accepted API revision. Corpus invokes ToolRouter for that exact revision, records its actual artifacts, and marks the revision ready only after required processing completes. Missing dependencies or processing errors remain failures.",
            "Process this API source.",
            "I will run ToolRouter against this exact revision and report each completed phase or failure.",
            { suggestedActions: [{ id: "api-process", label: "Process API" }] },
          ),
          story(
            "api-monitor-processing",
            "Monitor API processing",
            "Understand what ToolRouter is doing and whether the source is ready.",
            "Expose real processing phases, current status, and actionable failure details without inventing progress.",
            "While processing is active or after it ends, Corpus shows the known phase and status for the selected revision. Completed, failed, and ready states are distinct; no synthetic progress or success is shown.",
            "What is happening with this API?",
            "I will show the latest recorded processing phase and the exact failure if processing stopped.",
          ),
          story(
            "api-inspect-graph",
            "Inspect the semantic graph",
            "Understand the structure ToolRouter produced for this API revision.",
            "Present the persisted graph with enough context to inspect nodes, edges, and their source revision.",
            "After processing succeeds, the owner opens the semantic graph for the exact API revision. Corpus shows the persisted nodes and relationships and keeps the source revision identifiable.",
            "Show me the semantic graph.",
            "I will open the graph produced for this revision and keep every node tied to its source evidence.",
          ),
          story(
            "api-replay-graph",
            "Replay graph construction",
            "See how ToolRouter built the graph node by node.",
            "Replay the persisted construction trace in order without claiming live streaming that is not available.",
            "After graph processing completes, the owner replays the persisted graph-construction trace node by node. Corpus supports pause, resume, and step-through over recorded events. This baseline does not claim that construction streams live while ToolRouter is still running.",
            "Show me how this graph was built.",
            "I will replay the recorded construction events in order, one node at a time.",
            { suggestedActions: [{ id: "api-replay-start", label: "Replay construction" }, { id: "api-replay-step", label: "Step" }] },
          ),
          story(
            "api-curate-operations",
            "Curate API operations",
            "Choose which discovered API operations should be available for agent design.",
            "Present exact discovered operations and persist the owner's inclusion decisions for the source revision.",
            "The owner reviews operations discovered from the processed API revision and includes or excludes exact operations for downstream Agent Designer use. Corpus does not invent operations or silently broaden the selection.",
            "Only include order lookup and shipment tracking.",
            "I will keep those exact discovered operations and exclude the others from downstream agent design.",
            { suggestedActions: [{ id: "api-save-operations", label: "Save operation selection" }] },
          ),
          story(
            "api-recover-processing",
            "Recover from API processing failure",
            "Correct a failed API source and retry without losing the failure evidence.",
            "Keep the failed result visible, identify valid corrective actions, and retry only when the owner requests it.",
            "When upload, configuration, or ToolRouter processing fails, Corpus shows the failure and retains its evidence. The owner can correct the relevant input and explicitly retry the affected step. Corpus never substitutes a mock graph, cached success, or alternate processor.",
            "Fix the base URL and retry processing.",
            "I will save the corrected input and retry only the failed processing step when you confirm.",
            { suggestedActions: [{ id: "api-retry", label: "Retry processing" }] },
          ),
        ],
      },
    ],
  }
}
