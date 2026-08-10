# Studio And Lounge Evaluation Authoring Implementation Plan

> **Status:** Superseded on 2026-08-07 by
> `docs/superpowers/plans/2026-08-07-corpus-horizontal-delivery.md`. Retained as
> historical implementation evidence; do not use its unchecked items as the
> active execution authority.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add intuitive, persisted behavior and conversation evaluation authoring to the Agent Design Studio and provide complete level-1 and level-2 Lounge evaluation definitions without claiming runtime proof.

**Architecture:** Evaluation definitions remain product-semantic data in `design-state.json`. Behavior cases live on their owning behavior; adaptive conversation scenarios live on their owning feature. Pure readiness functions validate definition completeness and product-design references. The Studio presents compact inventories with focused editors and a truthful read-only `Not run` state; execution, immutable results, implementation mapping, and backend-state benchmarks remain outside this change.

**Tech Stack:** React 19, TypeScript 7, Vite 8, Vitest, Testing Library, existing shadcn-style primitives, repository-owned JSON persistence.

## Global Constraints

- Do not modify the sibling RouteDeck repository or introduce RouteDeck identifiers into Studio state.
- Do not modify `docs/corpus-agent-design/feature-behavior-notes.md`.
- Preserve file-to-Studio-to-save-to-file persistence without schema versions or migrations.
- Reference responses are optional semantic examples and are never exact-string expectations.
- Deterministic expectations describe product/runtime facts only; they do not judge prose.
- Conversation scenarios use an adaptive tester contract, not a fixed transcript.
- Runtime results remain external to `design-state.json`; this implementation may only show the truthful status `Not run`.
- Level-3 product outcome benchmarks remain documented and unimplemented.
- Do not use mocks, fixtures, canned assistant responses, or synthetic runtime success as product proof.
- Keep new implementation changes staged but uncommitted after verification.

---

### Task 1: Persisted Evaluation Contracts And Structural Validation

**Files:**
- Modify: `docs/corpus-agent-design/workbench/src/workbench/types.ts`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/storage.ts`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/seed.ts`
- Modify: `docs/corpus-agent-design/workbench/src/App.tsx`
- Test: `docs/corpus-agent-design/workbench/src/tests/workbench.test.tsx`

**Interfaces:**
- Produces: `EvalCoverageTag`, `BehaviorEvalCase`, `DeterministicExpectations`, `FeatureConversationEvalScenario`, and `EvaluationExemption`.
- Extends: `DesignStory.behaviorEvals`, `DesignStory.evalExemptions`, and `DesignFeature.conversationEvals`.
- Preserves: strict structural load validation and ordinary JSON autosave.

- [ ] **Step 1: Write a failing persistence test**

Add a test that loads the persisted Lounge design, verifies behavior cases and conversation scenarios are present, edits a case title through Studio state, and confirms the saved JSON contains the change while containing no result payload or RouteDeck identifier field.

- [ ] **Step 2: Run the focused test and confirm the missing contract failure**

Run: `pnpm test -- --run src/tests/workbench.test.tsx`

Expected: FAIL because evaluation fields and authoring controls do not exist.

- [ ] **Step 3: Add explicit product-semantic types**

Use these stable shapes:

```ts
export type EvalCoverageTag = "normal" | "boundary" | "failure" | "privacy" | "adversarial"

export interface DeterministicExpectations {
  startingBehavior: string
  finalBehavior: string
  authentication: "public" | "authenticated" | "unchanged"
  requiredOperations: string[]
  allowedOperations: string[]
  forbiddenOperations: string[]
  requiredSurfaces: string[]
  requiredSuggestedActions: string[]
  forbiddenOutcomes: string[]
}

export interface BehaviorEvalCase {
  id: string
  title: string
  enabled: boolean
  blocking: boolean
  coverage: EvalCoverageTag[]
  input: string
  referenceResponse: string
  requiredCriteria: string[]
  forbiddenCriteria: string[]
  expectations: DeterministicExpectations
}

export interface EvaluationExemption {
  coverage: EvalCoverageTag
  reason: string
}

export interface FeatureConversationEvalScenario {
  id: string
  title: string
  enabled: boolean
  blocking: boolean
  openingMessage: string
  hiddenGoal: string
  persona: string
  facts: string[]
  mayDisclose: string[]
  withholdUntilAsked: string[]
  bypassAttempts: string[]
  perTurnCriteria: string[]
  finalRequiredCriteria: string[]
  finalForbiddenCriteria: string[]
  expectations: DeterministicExpectations
  successCondition: string
  failureConditions: string[]
  stoppingConditions: string[]
  maxTurns: number
}
```

- [ ] **Step 4: Extend structural validation and new-object defaults**

Require every persisted behavior and feature to contain the new arrays and validate every nested primitive. New behaviors receive empty `behaviorEvals` and `evalExemptions`; features retain their persisted conversation scenarios. Reject malformed files visibly instead of normalizing or fabricating missing content.

- [ ] **Step 5: Run typecheck and focused persistence tests**

Run: `pnpm typecheck && pnpm test -- --run src/tests/workbench.test.tsx`

Expected: the contract tests pass; UI-control expectations may remain failing until Tasks 3 and 4.

### Task 2: Evaluation Completeness Diagnostics

**Files:**
- Create: `docs/corpus-agent-design/workbench/src/workbench/evaluationReadiness.ts`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/readiness.ts`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/ReadinessPanel.tsx`
- Test: `docs/corpus-agent-design/workbench/src/tests/evaluationReadiness.test.ts`
- Test: `docs/corpus-agent-design/workbench/src/tests/readiness.test.ts`

**Interfaces:**
- Produces: `getBehaviorEvalReadiness(story): EvaluationReadiness`.
- Produces: `getFeatureConversationEvalReadiness(feature): EvaluationReadiness`.
- Produces: `getBehaviorEvalCaseIssues(story, evalCase)` and `getConversationScenarioIssues(feature, scenario)` for focused row status.
- Extends: `ReadinessSection` with `evals` and includes evaluation blockers in behavior approval readiness.

- [ ] **Step 1: Write failing readiness tests**

Cover missing normal coverage, uncovered applicable categories, reasonless exemptions, empty prompts/criteria, duplicate IDs, invalid `maxTurns`, and references to missing Operations, Surfaces, or SuggestedActions. Also prove an optional reference response may be empty and wording is never compared.

- [ ] **Step 2: Run readiness tests and confirm failures**

Run: `pnpm test -- --run src/tests/evaluationReadiness.test.ts src/tests/readiness.test.ts`

Expected: FAIL because evaluation readiness functions do not exist.

- [ ] **Step 3: Implement pure diagnostics**

Treat all five coverage categories as applicable unless explicitly exempted with a non-empty reason. Require at least one enabled normal case. Require each enabled case to have an ID, title, input, at least one required or forbidden semantic criterion, and valid product-semantic references. Require conversation scenarios to have an opening message, hidden goal, persona, final criteria, stopping condition, and `maxTurns` from 2 through 20.

- [ ] **Step 4: Integrate behavior approval diagnostics**

Add evaluation blockers to `getStoryReadiness`; point them to `behavior-evals-heading` or the specific eval row. Keep runtime status separate so `Not run` does not block design approval.

- [ ] **Step 5: Run readiness tests**

Run: `pnpm test -- --run src/tests/evaluationReadiness.test.ts src/tests/readiness.test.ts`

Expected: PASS.

### Task 3: Compact Behavior Eval Authoring

**Files:**
- Create: `docs/corpus-agent-design/workbench/src/workbench/BehaviorEvalEditor.tsx`
- Create: `docs/corpus-agent-design/workbench/src/workbench/EvaluationStatus.tsx`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/BehaviorDesignEditor.tsx`
- Modify: `docs/corpus-agent-design/workbench/src/styles/studio.css`
- Test: `docs/corpus-agent-design/workbench/src/tests/workbench.test.tsx`

**Interfaces:**
- Consumes: `DesignStory`, `getBehaviorEvalReadiness`, and `getBehaviorEvalCaseIssues`.
- Produces: a behavior-level `Evals` section with coverage summary, list inventory, and one focused modal/drawer editor.
- Produces: truthful `Not run` presentation with copy that execution evidence is external.

- [ ] **Step 1: Add failing interaction tests**

Test the flow `Arrive in the Lounge -> Evals inventory -> open one case -> edit semantic criteria -> Done -> autosaved JSON`. Assert the optional reference field is labelled as semantic guidance and no exact-output control exists. Verify coverage and blocking status are visible without opening every case.

- [ ] **Step 2: Run the focused UI test and confirm failure**

Run: `pnpm test -- --run src/tests/workbench.test.tsx`

Expected: FAIL because the behavior eval UI does not exist.

- [ ] **Step 3: Implement the compact inventory**

Use a table-like open layout aligned with the existing Operation inventory: case name, coverage, blocking/optional status, completeness, and `Not run`. Keep the primary behavior document scannable and avoid nested card grids.

- [ ] **Step 4: Implement the focused editor**

Provide fields for title, enabled/blocking switches, coverage, user input, optional semantic reference, repeatable required/forbidden criteria, and product-semantic expectation associations. Use existing buttons, fields, textarea, association-chip, and drawer visual language. All controls must have explicit labels and keyboard focus treatment.

- [ ] **Step 5: Implement responsive behavior**

At narrow widths, collapse inventory columns into a readable two-line row and make the focused editor a full-pane overlay with a sticky header/footer. Prevent horizontal overflow and preserve the existing mobile navigation and review switcher.

- [ ] **Step 6: Run focused UI tests and typecheck**

Run: `pnpm typecheck && pnpm test -- --run src/tests/workbench.test.tsx`

Expected: PASS.

### Task 4: Feature Conversation Eval Workspace

**Files:**
- Create: `docs/corpus-agent-design/workbench/src/workbench/ConversationEvalEditor.tsx`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/FeatureRail.tsx`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/studioConfig.ts`
- Modify: `docs/corpus-agent-design/workbench/src/App.tsx`
- Modify: `docs/corpus-agent-design/workbench/src/styles/studio.css`
- Test: `docs/corpus-agent-design/workbench/src/tests/workbench.test.tsx`

**Interfaces:**
- Extends: `selectedView` with `conversation-evals`.
- Consumes: `DesignFeature`, `getFeatureConversationEvalReadiness`, and `getConversationScenarioIssues`.
- Produces: feature-level scenario inventory and focused adaptive-tester editor.

- [ ] **Step 1: Add failing navigation and editing tests**

Test `Lounge -> Conversation evals -> Credential in chat -> edit withheld fact -> autosave`. Assert the UI describes an adaptive tester, exposes max turns/stopping rules, and does not render a fixed assistant/user transcript builder.

- [ ] **Step 2: Run the focused test and confirm failure**

Run: `pnpm test -- --run src/tests/workbench.test.tsx`

Expected: FAIL because the feature destination does not exist.

- [ ] **Step 3: Add the feature destination and summary**

Place `Conversation evals` beside feature guidance and feature rules in the rail. Show scenario count and completeness issues. The main workspace header must explain that the tester adapts to Corpus clarification order while retaining its hidden goal.

- [ ] **Step 4: Build inventory and focused scenario editor**

Use a compact list plus a focused drawer. Group fields into `Scenario`, `Tester knowledge`, `Bypass behavior`, `Evaluation criteria`, and `Stop conditions`; do not expose one giant undifferentiated form. Include enabled/blocking controls and truthful `Not run` status.

- [ ] **Step 5: Run UI tests and typecheck**

Run: `pnpm typecheck && pnpm test -- --run src/tests/workbench.test.tsx`

Expected: PASS.

### Task 5: Lounge V1 Evaluation Pack

**Files:**
- Modify: `docs/corpus-agent-design/workbench/src/workbench/seed.ts`
- Modify: `docs/corpus-agent-design/workbench/design-state.json`
- Test: `docs/corpus-agent-design/workbench/src/tests/evaluationReadiness.test.ts`
- Test: `docs/corpus-agent-design/workbench/src/tests/readiness.test.ts`

**Interfaces:**
- Produces: level-1 cases for all eight Lounge behaviors.
- Produces: eight approved level-2 scenario definitions: grounded help, task redirection, auth routing, recovery enumeration, credentials in chat, Workspace leakage, multi-turn bypass, and unavailable claims.

- [ ] **Step 1: Add failing Lounge pack assertions**

Assert every Lounge behavior has normal coverage plus every other category covered or exempted with reason. Assert the feature has all eight named scenario purposes, all definitions are blocking and enabled for V1, and Lounge evaluation readiness has zero blockers. Assert all cases remain `Not run` because results are not persisted.

- [ ] **Step 2: Author behavior cases**

Write concise product-language prompts and semantic criteria that vary wording and attack shape. Include success and material failure paths. Use optional reference responses only when they materially clarify expected meaning; never use exact matching.

- [ ] **Step 3: Author adaptive conversation scenarios**

Give each tester a stable hidden goal, bounded facts, disclosure rules, one or more bypass tactics, criteria, and terminal conditions. Do not prescribe Corpus's clarification order or generated user utterances after the opening message.

- [ ] **Step 4: Mirror seed and persisted design state**

Regenerate the persisted Studio state from the real seed structure or update both sources mechanically, then verify semantic equality for all evaluation fields. Preserve existing review statuses and unrelated design content.

- [ ] **Step 5: Run pack tests**

Run: `pnpm test -- --run src/tests/evaluationReadiness.test.ts src/tests/readiness.test.ts`

Expected: PASS with eight Lounge behaviors and eight feature scenarios free of evaluation-definition blockers.

### Task 6: Owned Documentation And Full Verification

**Files:**
- Modify: `docs/corpus-agent-design/workbench/README.md`
- Modify: `architecture/code-map.md`
- Modify: `docs/superpowers/specs/2026-08-05-corpus-self-evaluation-design.md`
- Modify only the evaluation hunk: `context.md`

**Interfaces:**
- Documents: ownership, authoring workflow, non-proof `Not run` semantics, and deferred runner/level-3 work.
- Preserves: unrelated dirty-worktree content and user-owned notes.

- [ ] **Step 1: Update owned documentation**

Mark the design approved for authoring implementation. Document the two Studio destinations and state explicitly that runtime execution, external results, mapping alignment, and level-3 benchmarks remain pending.

- [ ] **Step 2: Run complete Studio checks**

Run from `docs/corpus-agent-design/workbench`:

```powershell
pnpm test
pnpm build
```

Expected: all tests and TypeScript/Vite build pass.

- [ ] **Step 3: Run Browser/IAB desktop verification**

Start locally with `pnpm dev -- --host 0.0.0.0`, record the exact URL, then verify `Lounge -> Arrive in the Lounge -> behavior eval inventory -> focused case editor` and `Lounge -> Conversation evals -> focused adaptive scenario editor`. Check title/URL, meaningful DOM, no framework overlay, console health, autosave, and screenshots.

- [ ] **Step 4: Run Browser/IAB responsive verification**

Repeat at a mobile-sized viewport. Verify no clipping or horizontal overflow, usable navigation, readable inventory rows, full-pane editors, sticky controls, and accessible focus/labels.

- [ ] **Step 5: Inspect screenshots against the accepted Studio design system**

Use the prior accepted Studio redesign as the reference and inspect current desktop/mobile screenshots with `view_image`. Compare layout hierarchy, compact rail/list model, typography, true-white/slate palette, spacing, editor overlay behavior, and responsive collapse. Fix every material mismatch.

- [ ] **Step 6: Stage only this implementation**

Stage the implementation plan, evaluation spec, Studio source/tests/design state, owned documentation changes, and only the evaluation-specific `context.md` hunk. Do not stage unrelated source-hub, runbook, mockrun, evidence, or test changes. Confirm the staged diff and leave it uncommitted.
