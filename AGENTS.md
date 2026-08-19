# Corpus Repository Instructions

These instructions apply to the entire `saastoagent-v0.1` repository.

## Repository Authority

- This repository is the authoritative Corpus checkout.
- The sibling RouteDeck checkout at `D:\Dev\AI Projects\routedeck` is a
  separate repository and is **read-only by default**.
- A request to design, implement, debug, test, or finish Corpus does not grant
  permission to edit RouteDeck.
- RouteDeck may be inspected read-only to understand its current contracts.
- Do not edit, format, generate files in, stage, commit, revert, reset, clean,
  or otherwise mutate RouteDeck unless the user explicitly authorizes a named
  RouteDeck change.
- Runtime debugging, failing tests, missing framework support, and end-to-end
  validation do not expand that authority.
- If Corpus cannot be implemented through existing RouteDeck contracts, stop.
  Report the exact missing contract and wait for an explicit decision.
- Do not create a workaround that silently duplicates or replaces RouteDeck
  behavior inside Corpus.

## User-Owned Design Notes

- `docs/corpus-agent-design/feature-behavior-notes.md` is owned exclusively by
  the user. Never modify, reformat, regenerate, or overwrite it.
- Treat those notes as design input. Put Codex-authored interpretations in the
  Design Studio and its implementation manifest.

## Design Studio Boundary

- The RouteDeck Agent Design Studio defines product behavior, interaction
  shape, prompts, policies, operations, suggested actions, surfaces, and scope
  boundaries. It must not dictate technical implementation.
- Do not place RouteDeck identifiers, references, bindings, providers, guards,
  or other compiled implementation details in Studio state.
- `contracts/corpus-agent-design-routedeck-manifest.json` owns the mapping from
  accepted Studio design to implementation identifiers.
- Improve or correct the Studio design before implementing a materially
  different product behavior.
- Feature-level instructions map to feature-scoped RouteDeck `AgentPolicy`
  values through `Feature.agent_policies`. Do not invent a parallel
  `Feature.agent_prompt` framework field.
- Policies attached below the feature level belong to their owning Node,
  Capability, Surface, or Operation. Behaviour is not a RouteDeck policy scope.

## Mandatory RouteDeck Mapping Gate

Before implementing a Studio behavior in Corpus:

1. Inspect the current RouteDeck source and contracts read-only.
2. Produce a mapping of `Studio concept -> existing RouteDeck contract ->
   Corpus implementation location`.
3. Distinguish product-owned text and behavior from framework-owned state and
   execution semantics.
4. Identify every missing or ambiguous mapping as a blocker.
5. Present material design corrections in the Studio first.
6. Implement only after the mapping and affected Corpus file plan are clear.

Never interpret a product term as proof that RouteDeck needs a new primitive.
Prove the gap against current RouteDeck source first.

## Behavior-First Delivery Process

- Follow `docs/corpus-behavior-first-delivery-process.md` for every product
  behavior change from owner intent through Studio, RouteDeck mapping, Corpus
  implementation, isolated validation, ledger retest, and closeout.
- Use `docs/corpus-behavior-evidence-ledger.md` and
  `skills/audit-corpus-behaviors/SKILL.md` for observed behavior truth and the
  canonical audit workflow. Do not create a second ledger, runner, dashboard,
  schema, or competing status vocabulary.
- Keep audit and product-fix lanes separate. An as-is behavior campaign is
  read-only for product source; an implementation task must not edit evidence
  to manufacture a pass.
- Do not use a complete horizontal journey to debug one feature. Validate the
  feature in isolation, retest it through the supported canonical audit path,
  and run release-level chat/surface/hybrid journeys only at the documented
  gate.

## Working Rules

- Follow the read order in `AGENTIC_CODING_GUIDE.md`: `critical_prompt.md`,
  `context.md`, the latest checkpoint, `instructions.md`,
  `context_pipeline.md`, the relevant code-map and component documents, and
  active plans.
- Identify the owning `architecture/code-map.md` subsystem before changing
  source.
- Keep changes inside the user-authorized repository and feature boundary.
- Do not perform Git operations unless the user explicitly asks for them.
- Do not introduce migration work, compatibility preservation, or broad TDD
  ceremony unless the user requests it. Use focused tests proportional to the
  actual product risk.
- Validate the real product path. Passing unit tests alone is not completion.
- Do not ship mocks, fixtures, canned responses, silent fallbacks, or
  test-only product behavior.
- Fail clearly when a required dependency or contract is unavailable.

## Cross-Repository Stop Condition

When progress appears to require a change outside this repository, stop before
making that change and report:

- the repository and exact files that would need modification;
- the existing contract that is insufficient;
- why a Corpus-owned adapter cannot correctly solve it;
- the smallest proposed upstream change; and
- the validation that would prove it.

Proceed only after the user explicitly authorizes that cross-repository work.

