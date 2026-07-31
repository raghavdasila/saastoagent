# Lounge RouteDeck Conversion Implementation Plan

Status: closed 2026-07-31. The Lounge design/implementation conversion and the
subsequent bearer/conversation correction are delivered. Current evidence and
remaining prompt-wiring/browser-proof caveats are owned by
`logs/20260731_server_owned_conversations.md` and
`context_checkpoints/2026-07-31-server-owned-conversations.md`; this file is no
longer an active plan. Unchecked boxes below preserve the original planning
record and must not be interpreted as current work state.

> **For agentic workers:** Execute inline and preserve the Design Studio as the
> product-shape authority. Do not add RouteDeck IDs or implementation mechanisms
> to Studio state.

**Goal:** Make every designed Lounge behavior execute through RouteDeck with the
designed Node, Capability, Surface, Operation, SuggestedAction, prompt, and
AgentPolicy boundaries.

**Architecture:** Product-visible changes are authored in the Design Studio
first. Credential and token values use RouteDeck private forms; Lounge operation
handlers read the encrypted form server-side and call Corpus owner-auth services.
A product-neutral RouteDeck FastAPI operation adapter supplies request-scoped
host context and decorates the completed HTTP response, allowing Corpus to keep
cookie ownership without bypassing RouteDeck supervision.

**Tech stack:** Python 3.11, FastAPI, RouteDeck core/FastAPI/SQLAlchemy,
FastAPI Users, React 19, TypeScript 7, `@routedeck/react`, Vitest, pytest.

## Global Constraints

- `docs/corpus-agent-design/feature-behavior-notes.md` is user-owned and must not
  be modified.
- Studio owns product shape and text; the implementation manifest owns technical
  RouteDeck IDs.
- No direct account mutation may remain in a Lounge React surface.
- Passwords and one-time tokens must use RouteDeck private forms and must never
  enter chat, public projections, or public operation arguments.
- Existing owner-auth rate limits, same-origin enforcement, cookie security,
  account-neutral recovery, and loud delivery failures must remain intact.
- No new dependency, migration, fixture fallback, or mock product path.
- No further Git commit is authorized by this plan.

---

### Task 1: Correct Lounge product shape in Studio

**Files:**
- Modify: `docs/corpus-agent-design/workbench/src/workbench/seed.ts`
- Modify: `docs/corpus-agent-design/workbench/design-state.json`
- Modify: `docs/corpus-agent-design/workbench/src/tests/workbench.test.tsx`
- Modify: `contracts/corpus-agent-design-routedeck-manifest.json`

**Produces:** One Node per Lounge behavior plus explicit product operations for
entering product help, opening account paths, leaving account flows, and
continuing an already-authenticated account into Workspace.

- [ ] Add product-help and account-path navigation operations to the behavior
  whose Node legally offers them.
- [ ] Add `Continue to Workspace` recovery after partial registration/sign-in
  continuation without allowing account recreation.
- [ ] Keep resend-verification surface-free and expose its operations through
  SuggestedActions.
- [ ] Update seed/state tests and confirm Studio autosave-compatible state.

### Task 2: Add product-neutral RouteDeck HTTP operation integration seams

**Files in `D:\Dev\AI Projects\routedeck`:**
- Modify: `routedeck_core/contracts/surfaces.py`
- Modify: `routedeck_fastapi/dependencies.py`
- Modify: `routedeck_fastapi/router.py`
- Modify: `routedeck_fastapi/routes/operations.py`
- Modify: `routedeck_fastapi/__init__.py`
- Test: focused core/FastAPI private-form and operation-route tests

**Produces:**
- `PrivateFormBinding.form_id` for an explicitly declared static, session-scoped
  private form, mutually exclusive with `form_id_prop`.
- `RouteDeckOperationHttpAdapter.request_context(request, operation_request)`
  and `decorate_response(request, response, result)` hooks passed explicitly to
  the runtime router factory.

- [ ] Authorize static private-form IDs without projecting secret or session
  identifiers.
- [ ] Wrap surface dispatch execution in the optional host request context.
- [ ] Let the host decorate only the outgoing HTTP response after supervision.
- [ ] Prove default RouteDeck behavior remains unchanged when no adapter exists.

### Task 3: Implement Lounge private-form and auth operation handlers

**Files:**
- Create: `backend/src/corpus/features/lounge/private_forms.py`
- Create: `backend/src/corpus/features/lounge/operations.py`
- Create: `backend/src/corpus/auth/operation_http.py`
- Modify: `backend/src/corpus/features/lounge/bindings.py`
- Modify: `backend/src/corpus/bindings.py`
- Modify: `backend/src/corpus/runtime/application.py`
- Modify: `backend/src/corpus/app/host.py`
- Modify: `backend/src/corpus/main.py`

**Produces:** RouteDeck handlers for owner registration, authentication,
password-reset request/confirmation, verification delivery/confirmation, and
authenticated Workspace continuation. `CorpusOperationHttpAdapter` preserves
request IP/auth context and applies the issued browser cookies to the dispatch
response.

- [ ] Load and validate exactly one complete encrypted private draft for the
  current RouteDeck session and declared form ID.
- [ ] Apply existing auth rate limits and mail semantics inside the operation
  handlers.
- [ ] Map domain failures to explicit RouteDeck business/transport failures.
- [ ] Publish issued owner-session cookies even when RouteDeck continuation
  fails after identity creation, preserving the designed partial-success truth.

### Task 4: Convert Lounge declarations to the exact Studio contract

**Files:**
- Modify: `backend/src/corpus/features/lounge/declarations.py`
- Modify: `backend/src/corpus/features/lounge/feature.py`
- Modify: `backend/src/corpus/features/lounge/policies.py`
- Modify: `backend/src/corpus/features/lounge/__init__.py`
- Modify: `backend/src/corpus/features/workspace/feature.py` only for the
  Studio-authored entry into verification delivery

**Produces:** Eight unique Lounge Nodes, exact scoped policy text, real account
Operations, exact Capability membership, surface affordances, transitions, and
SuggestedActions.

- [ ] Split arrival and product help into distinct reachable Nodes.
- [ ] Replace `authentication_completed` with the designed account Operation
  plus explicit `Continue to Workspace` recovery.
- [ ] Remove the undesigned resend-verification surface.
- [ ] Keep all implementation identifiers in declarations/manifest only.

### Task 5: Route Lounge surfaces through private forms and affordances

**Files:**
- Modify: `frontend/src/features/lounge/AuthSurface.tsx`
- Modify: `frontend/src/features/lounge/ForgotPasswordSurface.tsx`
- Modify: `frontend/src/features/lounge/ResetPasswordSurface.tsx`
- Modify: `frontend/src/features/lounge/VerifyEmailSurface.tsx`
- Delete: `frontend/src/features/lounge/VerificationPendingSurface.tsx`
- Modify: `frontend/src/features/lounge/authClient.ts`
- Modify: `frontend/src/features/lounge/useAuthenticationContinuation.ts`
- Modify: `frontend/src/routedeck/surfaces.tsx`
- Modify: focused frontend tests

**Produces:** Each surface saves private values through
`RouteDeckPrivateForm`, then dispatches only the declared affordance with the
non-secret static form handle. Authentication session reads remain host-owned;
account mutations no longer call `/api/auth/**` from React.

- [ ] Save exact private fields and dispatch the matching operation.
- [ ] Resync after cookie-changing operations and render precise failure or
  partial-success copy.
- [ ] Clear token fragments only after the supervised operation succeeds.
- [ ] Render verification delivery as chat SuggestedActions without a surface.

### Task 6: Prove parity and the real product path

**Files:**
- Modify affected architecture, runtime flow, test-index, and current-context
  owners only.

- [ ] Export/check the compiled frontend contract.
- [ ] Run Studio, parity-checker, backend, frontend, RouteDeck focused, typecheck,
  and production-build gates.
- [ ] Start the local Docker services, report the exact commands and URLs, and
  exercise registration, sign-in failure/success, password recovery, reset,
  verification delivery/confirmation, partial continuation, product help, and
  desktop/mobile Lounge rendering.
- [ ] Keep Workspace/Sources parity failures separate from the Lounge result and
  report any remaining unverified external mail evidence explicitly.
