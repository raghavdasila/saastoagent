# OpenAPI ToolRouter Future Integration Plan

## Summary

Promote the standalone ToolRouter prep bundle into SaaStoAgent only after Corpus/RouteDeck has a stable execution surface. The production integration should call one adapter function, render the returned decision through Corpus-authored proposals/surfaces, and log every correction as feedback.

## Implementation Sequence

1. Package boundary
   - Extract or vendor `toolrouter.integration` as a SaaStoAgent backend dependency.
   - Keep OpenAPI artifact generation separate from Corpus turns.
   - Store tenant/integration artifacts under a controlled tenant path, not inside the frontend.

2. Corpus routing surface
   - Add a Corpus legal operation for "route API request" that calls `route_tool_request`.
   - Return the decision as evidence and proposal payload, not raw action chips.
   - Route `ASK_PARAM`, `ASK_POLICY`, and `SHOW_TOPK` into active surfaces only after user initiation or accepted proposal.

3. Guardrails and execution
   - Resolve guardrails by hierarchy: SaaSAgent default, connection override, endpoint override.
   - Treat `ROUTE` as a dry-run preview until the separate execution layer confirms permission.
   - Require explicit confirmation for writes when guardrails say `confirm_write`.
   - Block writes when guardrails say `block_write`.

4. Feedback and training
   - Log every decision and every user/agent/validator correction.
   - Train tenant-specific feedback models first.
   - Use global models only for high-quality explicit feedback.
   - Keep synthetic feedback separate and report it separately.
   - Shadow-evaluate before model promotion.

5. Sandbox and onboarding
   - Replace API-first training with outcome-first sandbox workflows.
   - Ask for sandbox credentials or explicit permission to sign up for a sandbox account.
   - Never store plaintext sandbox secrets in feedback logs.

## Acceptance Criteria

- SaaStoAgent can call one function and receive `ToolRouteDecision`.
- Corpus UI can render every decision type without endpoint-specific hardcoding.
- No OpenAPI-derived write executes without guardrail permission and confirmation.
- Feedback events are tenant and integration scoped.
- Medusa artifacts route through the generic OpenAPI adapter with no Medusa-specific endpoint map.
