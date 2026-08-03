# Lounge, RouteDeck, and Design Studio gap log

Date: 2026-08-03  
Scope: read-only audit findings for later work. RouteDeck references point to
the sibling checkout and do not authorize changes there.

## RouteDeck implementation gaps

- Legal model tools currently include every legal Operation, without filtering
  by invocation source. Evidence: `routedeck_langgraph/model_context.py` builds
  `legal_tools` from all `legal_operations`; Corpus rejects credential calls
  later in `backend/src/corpus/features/lounge/operations.py::_require_surface`.
  Result: execution fails closed, but the model can still select unusable tools
  and drift or loop.

## RouteDeck framework gaps

- `OperationSource` exists on requests, but an `Operation` cannot declare its
  allowed invocation sources. Evidence:
  `routedeck_core/contracts/operations.py::OperationSource` and `Operation`.
  Candidate upstream contract: `Operation.allowed_sources`, enforced during
  compilation, model-context projection, and execution. This requires explicit
  RouteDeck authorization before implementation.

## Corpus runtime gaps

- Product Help has no trusted current-product-facts context provider, so
  RouteDeck can constrain legal actions but cannot ground capability claims.
  Evidence: `backend/src/corpus/features/lounge/feature.py::PRODUCT_HELP_NODE`
  and the current Lounge feature providers. Prefer the existing RouteDeck
  context-provider contract; no new framework primitive is presently proven.
- Verification resend creates/resolves the token before applying delivery rate
  limits. Evidence:
  `backend/src/corpus/features/lounge/operations.py::RequestVerificationDeliveryHandler`
  calls `request_verification_for_route` before `_enforce_limits`.
- Email confirmation returns success after token verification, while the design
  promises refreshed owner-state evidence. Evidence:
  `backend/src/corpus/features/lounge/operations.py::ConfirmOwnerEmailHandler`
  and `backend/src/corpus/features/lounge/feature.py` title for
  `lounge.confirm_verification`.
- Registration can return `email_already_registered`, revealing account
  existence despite rate limiting. Evidence:
  `backend/src/corpus/auth/service.py::register` and the registration handler in
  `backend/src/corpus/features/lounge/operations.py`.

## Lounge design gaps

- Lounge arrival exposes password-reset and email-verification link Operations
  even though those paths require captured deep-link tokens. Evidence:
  `design-state.json`, behavior `Arrive in the Lounge`, and
  `backend/src/corpus/features/lounge/declarations.py` operations
  `lounge.arrival.open_reset_password` and
  `lounge.arrival.open_verify_email`.
- All 23 designed Lounge Operations omit inputs, outcomes, safety/review, and
  recovery contracts. Evidence: `design-state.json`, Lounge
  `stories[].operations[]`.
- Password recovery must promise only account-neutral request acceptance, not
  delivery. Evidence: mail failure is deliberately hidden in
  `backend/src/corpus/features/lounge/operations.py::RequestPasswordResetHandler`.
- Registration design describes partial identity-created/Workspace-entry
  success, but the current service transaction is atomic. Evidence:
  `backend/src/corpus/auth/service.py::register`. Remove the partial-success
  story unless a real post-commit boundary is identified.

## Design Studio gaps

- Studio permits an Operation to remain reviewable with empty inputs, outcomes,
  safety/review, and recovery fields. Evidence:
  `docs/corpus-agent-design/workbench/design-state.json` and the workbench
  operation editor/validation code under `docs/corpus-agent-design/workbench/`.
  Add completeness diagnostics before behavior approval; do not put technical
  RouteDeck identifiers into Studio state.

## Design-to-runtime mapping gaps

- Feature-prompt mapping was stale: it targeted nonexistent
  `Feature.agent_prompt`. Fixed in this slice by mapping `feature.prompt` to a
  designated feature-scoped `AgentPolicy` through the implementation manifest.
  Evidence: `docs/corpus-agent-design/routedeck-design-mapping.md`,
  `contracts/corpus-agent-design-routedeck-manifest.json`, and
  `scripts/check_agent_design_parity.py`.
- A broader parity run is still required after the Lounge redesign. The checker
  should remain the gate for prompt, policy-scope, Node, Capability, Surface,
  Operation, and SuggestedAction drift.

## Existing safeguards worth preserving

- Credential chat is disabled on credential Nodes; private form values remain
  encrypted/server-only; public arguments are rejected; credential handlers
  require Surface invocation; authentication and one-time tokens are validated;
  invalid sign-in is generic; password change revokes sessions. Evidence:
  `backend/src/corpus/features/lounge/feature.py`, `operations.py`, and
  `backend/src/corpus/auth/service.py`.
- Model prose is not state change. Canonical RouteDeck state and product UI must
  remain the evidence for completion, authentication, and verification claims.
