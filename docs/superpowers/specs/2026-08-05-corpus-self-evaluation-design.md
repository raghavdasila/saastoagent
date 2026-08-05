# Corpus Self-Evaluation Design

Status: Approved. Studio authoring and the Lounge V1 definition pack are implemented; compiled-runtime execution and external results remain pending.

## Purpose

Corpus needs evidence that its designed behavior survives real model execution. Existing Studio completeness checks prove that a design is structurally reviewable, while the current live conversation smoke proves transport, persistence, reconnect, and non-empty model output. Neither proves that Corpus follows its product boundaries, resists conversational bypasses, avoids unsupported claims, or leaves authoritative product state in the required condition.

This design establishes one Corpus-wide self-evaluation foundation with Lounge as the first implemented evaluation pack. It defines three proof levels:

1. behavior evals for atomic single-turn behavior;
2. feature conversation evals for adaptive multi-turn behavior; and
3. deferred product outcome benchmarks for complete user goals and authoritative backend state.

The first two levels will be authored through the Agent Design Studio and executed against the actual compiled Corpus runtime. The third level is documented now and remains unimplemented until the corresponding Corpus product pathways work end to end.

## Boundaries

- The Agent Design Studio owns product-semantic evaluation definitions and review state.
- Studio evaluation definitions contain no RouteDeck IDs, provider bindings, database table names, or compiled implementation details.
- The implementation manifest maps accepted Studio behaviors, Operations, Surfaces, and SuggestedActions to runtime identifiers.
- A dedicated Corpus self-evaluation runner owns execution, tester and judge invocation, runtime assertions, result artifacts, and failure reporting.
- ToolRouter evalsets continue to evaluate generated agents and API-source behavior. They are not reused as Corpus self-evaluation evidence.
- Evaluation results never enter `design-state.json`.
- A Studio preview or prompt simulation is not runtime proof. Only execution against the actual compiled Corpus application may produce a passing runtime result.
- Missing runtime, model, tester, judge, mapping, or required evidence fails visibly. No alternate provider, canned response, heuristic answer, or mock product result may substitute for it.

## Selected Architecture

The selected approach combines Studio-owned case authoring with an external Corpus-owned runner and result store.

### Alternatives considered

1. **Studio-only prompt simulation** would be fast, but could pass a prompt that the compiled runtime does not actually assemble or execute. It is rejected as proof.
2. **Studio authoring plus a Corpus self-evaluation runner** keeps design language in the Studio and executes the real product path with durable evidence. This is selected.
3. **A full product benchmark platform** would combine case authoring, distributed runs, databases, dashboards, and outcome verification. It is premature and belongs to the deferred third level.

The initial implementation may expose runner results read-only in the Studio without making the Vite development server responsible for Python process orchestration. Execution remains an explicit runner responsibility. A later run control may call a narrow local evaluation API if that boundary is separately designed and approved.

## Shared Evaluation Lifecycle

Each evaluation definition has a stable product-owned ID and review state. Each execution records immutable identities for:

- the evaluation definition and its content hash;
- the selected Studio design hash;
- the implementation-manifest hash;
- the Corpus source revision and compiled application identity;
- the RouteDeck version;
- the Corpus model and configuration;
- the tester model and configuration when used;
- the judge model, rubric version, and configuration;
- the isolated runtime and conversation identities;
- start and completion timestamps.

The runner performs this sequence:

1. validate the case and its Studio ownership;
2. resolve product-semantic references through the implementation manifest;
3. create an isolated Corpus runtime and conversation state;
4. verify the required starting behavior, authentication state, and design/runtime hashes;
5. execute the real Corpus interaction;
6. capture transcript, transitions, Operations, Surfaces, suggested actions, failures, and relevant authoritative state;
7. evaluate deterministic runtime assertions;
8. invoke the independent LLM judge only when the required evidence exists;
9. combine hard assertion results with semantic criterion results without averaging away critical failures;
10. persist one immutable result artifact and update the external latest-result index.

## Level 1: Behavior Evals

Behavior evals are authored inside one Studio behavior and inherit its feature guidance, behavior rules, Capabilities, Surfaces, Operations, SuggestedActions, and starting context.

Each case contains:

- stable ID and title;
- enabled and blocking status;
- one user input prompt;
- an optional reference response for semantic direction, never exact matching;
- required semantic criteria;
- forbidden semantic criteria;
- applicable coverage tags;
- product-semantic runtime expectations where relevant.

Reference responses are examples, not golden strings. Wording, tone, ordering, and sentence structure may vary. The judge evaluates whether the response satisfies the required meaning and avoids forbidden behavior.

### Coverage categories

Studio completeness requires coverage by applicable category rather than an arbitrary number of cases:

- normal behavior;
- boundary or refusal;
- failure or unavailable state;
- privacy or safety;
- adversarial or indirect bypass.

A behavior may mark a category not applicable with a reviewable reason. Missing applicable coverage blocks design approval. Runtime execution is not required for design approval because implementation follows design.

### Deterministic assertions

Deterministic assertions evaluate product and runtime facts, not conversational wording. Depending on the behavior, they may verify:

- the expected starting and final product behavior;
- authentication remaining public, becoming authenticated, or remaining unchanged;
- required, allowed, and forbidden Operations;
- exposed Surfaces and SuggestedActions;
- absence of unintended product mutations;
- absence of private Workspace state in an unauthenticated conversation;
- credentials remaining outside chat and RouteDeck-visible state;
- visible failure and recovery state after an unsuccessful action;
- absence of raw RouteDeck identifiers, state codes, or framework errors in product output.

Hard deterministic failures are reported before semantic judging. They do not attempt to decide whether natural-language meaning is correct.

## Level 2: Feature Conversation Evals

Feature conversation evals are authored at feature level. They exercise behavior routing, clarification, continuity, recovery, and boundaries across multiple turns.

Each scenario contains:

- stable ID and title;
- enabled and blocking status;
- opening user message;
- hidden user goal;
- tester persona and facts;
- information the tester may disclose;
- information the tester must withhold until Corpus asks;
- adversarial or bypass behavior the tester should attempt;
- per-turn semantic and runtime checkpoints where required;
- final required and forbidden criteria;
- product-semantic runtime expectations;
- one primary terminal behavior plus explicitly authored acceptable alternatives when the product intentionally permits multiple routes;
- success, failure, and stopping conditions;
- maximum turn count.

### Adaptive tester

The conversation is not a fixed transcript. An independently configured LLM tester plays the user and adapts to Corpus's clarification order. It receives only the scenario contract and visible conversation, not hidden runtime state or expected implementation identifiers.

The tester must not:

- change the scenario goal;
- invent facts outside its persona;
- inspect internal traces or state;
- decide whether Corpus passed;
- coach Corpus toward the expected answer;
- continue beyond a terminal condition or maximum turn count.

The tester configuration and every generated user turn are recorded. A separate judge evaluates the completed transcript and runtime evidence. Fixed-turn probes remain permitted for exact regressions such as pasting a password into chat or explicitly requesting another owner's Workspace data, but they are not the primary conversation model.

## Judging And Pass Semantics

The judge is independent from Corpus and, where possible, uses a separately configured model. Every run records its provider, model, rubric, temperature, and other material configuration.

The judge receives:

- the evaluation definition;
- the visible transcript;
- the optional reference response;
- required and forbidden criteria;
- sanitized deterministic evidence;
- no credentials, one-time tokens, or unrelated private state.

The judge returns a strict structured result with one decision and rationale per criterion plus an overall decision. It does not award a free-form aggregate score that can conceal a critical violation.

A case passes only when:

- every blocking deterministic assertion passes;
- every required semantic criterion passes;
- every critical forbidden criterion is absent;
- the run reaches an allowed terminal condition;
- all required evidence is present.

Judge unavailability, invalid structured output, missing evidence, or runtime failure produces an explicit non-pass result. It does not silently retry with another model.

## Studio Experience

### Behavior level

Each behavior gains an **Evals** authoring destination containing:

- coverage summary;
- compact case inventory;
- focused case editor;
- required and forbidden criteria;
- optional reference response;
- product-semantic runtime expectations;
- design review status;
- latest external result and staleness status.

### Feature level

Each feature gains a **Conversation evals** destination containing:

- scenario coverage summary;
- compact scenario inventory;
- adaptive tester contract editor;
- per-turn and final criteria;
- product-semantic checkpoints;
- maximum-turn and stopping rules;
- latest external result and staleness status.

Studio statuses are **Not run**, **Passed**, **Failed**, and **Stale**. Results are loaded from the external result index and remain read-only in Studio state.

Design approval requires complete applicable evaluation definitions. A separate **implementation-ready** result requires every blocking runtime evaluation to pass against the current design, mapping, implementation, runtime, and model identities.

## Result Storage And Staleness

Local runs write immutable artifacts below an ignored runtime-owned Corpus evaluation directory. An intentionally retained proof may be promoted to the repository's evidence area through an explicit command; ordinary execution does not modify tracked documentation.

Each artifact contains:

- run manifest and identities;
- case snapshot and hashes;
- visible transcript;
- tester turns and configuration;
- deterministic assertion results;
- sanitized runtime evidence and trace references;
- judge request identity and structured result;
- final pass, fail, or infrastructure-failure status.

A prior result becomes stale when any material input changes, including:

- behavior or feature evaluation definition;
- owning Studio behavior or feature design;
- implementation manifest;
- compiled Corpus revision;
- RouteDeck version;
- Corpus model configuration;
- tester model or scenario contract;
- judge model or rubric.

Stale evidence remains inspectable but cannot satisfy implementation readiness.

## Lounge V1 Evaluation Pack

Level-1 coverage will be authored for all eight Lounge behaviors:

1. Arrive in the Lounge;
2. Ask Lounge for product help;
3. Create an owner account;
4. Sign in;
5. Request password recovery;
6. Set a new password;
7. Resend email verification;
8. Confirm email verification.

The initial level-2 scenarios cover:

- grounded Corpus product help;
- redirecting task requests to sign-in or sign-up;
- sign-up and sign-in routing;
- password recovery without account enumeration;
- credential-in-chat attempts;
- private Workspace leakage attempts;
- indirect and multi-turn boundary bypass;
- unknown, planned, or unavailable product claims.

The pack must test both successful behavior and material failure paths. It must not encode the current stale runtime as the expected behavior. Runtime execution begins only after the current Lounge implementation and implementation manifest map to the accepted Studio design.

## Level 3: Deferred Product Outcome Benchmarks

Product outcome benchmarks evaluate complete user goals rather than isolated responses. Inputs may be single-shot statements or adaptive conversations. Passing requires both acceptable interaction behavior and authoritative backend evidence.

Future examples include:

- create an agent and prove the correct owner-scoped records and configuration;
- attach a ready source and prove the selected immutable source revision;
- build an agent version and prove its exact RouteDeck application identity;
- deploy an eligible version and prove the active deployment and channel binding;
- execute a public interaction and prove its recorded result, trace, and version identity.

Every future benchmark must define preconditions, allowed interaction modes, expected domain state, forbidden side effects, cleanup, and evidence ownership. Database assertions belong to the owning Corpus modules and may reference implementation fields outside Studio design state.

This level is deliberately not implemented now. Corpus does not yet provide all required end-to-end product paths, and fixtures or synthetic success would create false evidence. The benchmark architecture will be designed when the first real product outcome is runnable.

## Failure Handling

- Invalid evaluation definitions block save or approval with focused diagnostics.
- Missing product-to-runtime mappings block execution before conversation creation.
- Runtime startup or readiness failure produces infrastructure failure.
- Tester or judge failure identifies the failing dependency and preserves available evidence.
- A Corpus failure remains visible; the runner does not substitute another model or path.
- Secrets are redacted from judge input and persisted artifacts.
- Partial artifacts are retained only when they can be clearly marked incomplete and contain no sensitive values.

## Verification Strategy

Implementation verification will include:

- focused schema and readiness tests for behavior and conversation eval definitions;
- Studio authoring, persistence, approval, result, and responsive UI tests;
- manifest-resolution tests proving product-semantic references map to current runtime contracts;
- runner unit tests for assertion and staleness logic;
- isolated real-runtime tests for conversation execution and evidence capture;
- independent tester and judge contract tests using their real configured providers;
- real Lounge level-1 and level-2 evaluation runs;
- browser review of behavior and feature evaluation authoring and results.

Passing unit tests or mocked judge output alone does not prove Lounge behavior. Completion requires real compiled Corpus execution, real configured models, immutable result artifacts, and reviewable failures.

## Implementation Order

1. Add Studio-owned level-1 and level-2 evaluation definitions and completeness diagnostics.
2. Author and review the Lounge v1 evaluation pack without claiming runtime proof.
3. Align the Lounge implementation manifest and compiled runtime with the accepted Studio design.
4. Build the isolated Corpus self-evaluation runner and immutable result schema.
5. Add Studio read-only result and staleness presentation.
6. Execute the real Lounge pack, inspect failures, and iterate through Studio design or owning implementation as evidence requires.
7. Leave level-3 benchmarks deferred until a real Corpus product outcome is available.

## Acceptance Criteria

- Behavior and feature evaluation definitions are product-semantic and contain no RouteDeck implementation IDs.
- Exact assistant wording is never required.
- Adaptive testers may follow different clarification orders without changing scenario goals.
- Deterministic assertions verify runtime facts and never replace semantic judging.
- Critical failures cannot be averaged into a passing result.
- Results are immutable, external to Studio state, identity-complete, and stale when inputs change.
- All eight Lounge behaviors have reviewed level-1 coverage.
- The initial Lounge level-2 scenario set covers the approved feature boundaries.
- Passing evidence comes only from the real compiled Corpus runtime.
- Product outcome benchmarks are documented and remain explicitly unimplemented.
