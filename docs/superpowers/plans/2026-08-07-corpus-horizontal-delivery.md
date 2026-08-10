# Corpus Behavior-Led Horizontal Delivery Plan

**Authoritative plan file:** `D:\Dev\AI Projects\saastoagent-v0.1\docs\superpowers\plans\2026-08-07-corpus-horizontal-delivery.md`

**Goal:** Deliver the complete Corpus lifecycle by integrating the proven sibling runtimes into Corpus, implementing the missing product behaviors through existing RouteDeck contracts, and proving every slice through real E2E, visual, persistence, and failure evidence.

## 1. Fixed Boundaries

- Corpus is the only writable product repository.
- RouteDeck remains read-only and owns navigation, operations, policies, guards, review, recovery, sessions, projections, and surfaces.
- `feature-behavior-notes.md` remains unchanged.
- ToolRouter remains the single routing, graph, and semantic evidence engine.
- Existing sibling runtimes provide proven capabilities; they are integrated, not rebuilt:
  - `source-hub-runtime`
  - `api-execution-runtime`
  - `agent-execution-runtime`
  - `agent-delivery-runtime`
- Import only necessary neutral modules behind narrow Corpus adapters. Do not copy sibling authentication, hosts, UI, queues, SQLite stores, proof state, or parallel ToolRouter/session implementations.
- No Git operations, RouteDeck changes, production deployment, custom-domain implementation, or AutomationBench access without separate authorization.

## 2. Behavior-Mapping Gate

Before implementing each feature slice:

1. Audit the behavior notes, current Studio state, current Corpus source, and current RouteDeck contracts.
2. Add or correct the product behavior in Studio.
3. Map every accepted behavior to:
   - RouteDeck feature, node, operation, surface, policy and review behavior;
   - Corpus domain/service/persistence owner;
   - frontend surface;
   - evaluator;
   - E2E and visual proof.
4. Distinguish product-owned behavior from framework-owned execution state.
5. Report unresolved or missing RouteDeck mappings as blockers.
6. Implement only after the slice's mapping and affected Corpus file plan are locked.

Launch completion requires every launch behavior to be represented in Studio and mapped in the implementation manifest.

## 3. Development Method

Development is behavior-led and audit-led.

For each slice:

1. Reproduce or inspect the current behavior.
2. Define the visible success, failure, waiting, recovery, permission and persistence outcomes.
3. Add focused tests only for critical contracts, deterministic rules, regressions, authorization, persistence and safety.
4. Implement the smallest complete real product path.
5. Exercise the running frontend, backend, database, RouteDeck runtime and real integration.
6. Inspect the rendered experience at representative desktop and mobile sizes.
7. Capture screenshots and video evidence.
8. Record exact commands, URLs, run IDs, counts, traces, artifact paths and limitations.
9. Update the owning architecture and test documentation.
10. Proceed only after the behavioral audit passes.

Test count and coverage are not completion criteria. Additional tests stop when the material behavior and integration risks are protected.

## 4. Delivery Steps

### Step 1: Persist and align the plan

- Save this plan to the authoritative plan path.
- Mark older overlapping plans as superseded without deleting their evidence.
- Confirm the current Corpus and RouteDeck heads, dirty-state boundaries and local runtime before source changes.

### Step 2: Correct Studio governance

- Prevent story approval when readiness or evaluation blockers remain.
- Correct stale Lounge capability guidance.
- Correct evaluation-result identity and aggregation so each definition shows its current result.
- Add the autonomous clarification behavior to the deployed-agent design.
- Preserve all user-owned design notes unchanged.

**Proof:** Studio behavior audit, readiness rejection, current-result display, parity check, screenshots and short interaction video.

### Step 3: Add shared infrastructure just in time

Introduce shared infrastructure only when required by the first consuming behavior:

- Huey-backed `DurableJobPort` for durable asynchronous work.
- PyNaCl-backed credential vault with environment-supplied key material.
- Corpus persistence for jobs, credential references and lifecycle records.
- Curated, hash-pinned integration snapshots and provenance manifests.
- Narrow Corpus adapters for API execution, agent execution and delivery.

Run official or verified reference workflows before integrating each dependency. Missing dependencies or failed reference behavior stop the slice; no fallback implementation is substituted.

### Step 4: Integrate Source Hub and API Source into Corpus

Reuse the completed Source Hub, ToolRouter and API-execution capabilities.

Deliver:

- owner-scoped source inventory;
- API YAML and markdown-description ingestion;
- durable asynchronous processing;
- base URL and authentication configuration;
- encrypted credential references;
- ToolRouter graph, process state, playback, routing evidence and semantic groups;
- failure, retry and deletion/dependency behavior;
- real operation execution through the API-execution adapter.

Corpus keeps one source inventory and one ToolRouter revision chain.

**Proof:** Upload -> process -> reload -> inspect graph -> configure -> route -> execute a real local Medusa operation, including failure/retry, owner isolation, redaction, desktop/mobile screenshots and a complete source-flow video.

### Step 5: Complete the Agents lifecycle

Deliver:

- attach an existing source;
- create and attach a new source;
- open an attached source;
- archive and delete with dependency constraints;
- selected-agent operations hub linking Designer, Builds, Sandbox and Evaluation;
- immutable references from historical builds to source revisions.

**Proof:** Real surface, chat and mixed interactions; reload/restart persistence; conflict handling; screenshots and lifecycle video.

### Step 6: Deliver Agent Designer

Deliver:

- prepopulation from the agent goal, selected source revision and ToolRouter operations;
- feature and behavior editing;
- policy, capability and tool proposals;
- approve, reject and customize flows;
- persistence of the accepted design;
- build initiation from the accepted design.

Studio remains product-facing and contains no RouteDeck implementation identifiers.

**Proof:** Proposal -> customization -> approval -> save -> reload -> build request, with manifest parity, desktop/mobile screenshots and design-flow video.

### Step 7: Integrate Agent Builder and the deployed-agent runtime

Reuse the completed neutral build and execution capabilities.

Deliver:

- immutable build assembly and content hashes;
- asynchronous generate, run, stop and delete behavior;
- separate build, run and session state;
- automatic evaluation-set creation;
- Sandbox launch;
- the Corpus-owned autonomous clarification resolver.

#### Autonomous clarification behavior

When ToolRouter returns `ASK_DISAMBIGUATE` or `ASK_PARAM`, the deployed agent attempts resolution before asking the user.

Permitted context:

- current user request;
- earlier messages in the same session;
- selected surface entities;
- current task state;
- accepted agent instructions;
- immutable allowed operations;
- prior verified results already present in the session;
- deterministic transformations such as relative dates using the session timezone.

Prohibited behavior:

- no additional API lookup calls for clarification;
- no invented IDs, dates, amounts, recipients, targets, statuses or defaults;
- no credential exposure;
- no cross-session or cross-tenant context;
- no operation outside the immutable build;
- no partial execution of a multi-call plan while any call remains unresolved.

A write may be selected autonomously only when the existing user request already establishes its target and intended effect. RouteDeck review remains mandatory where configured.

If unresolved, ask one concise natural question and resume the same run after the answer. Public users never see internal ToolRouter outcome names.

Persist safe clarification events:

- requested;
- resolved by agent;
- required from user;
- resolved by user.

**Proof:** Immutable build audit, asynchronous leave-and-return behavior, autonomous resolution, safe escalation, restart recovery, screenshots and execution video.

### Step 8: Integrate and prove Sandbox

Run the exact immutable build in a separate RouteDeck runtime/session scope against real local Medusa.

Deliver:

- real read and approved write operations;
- required-input, ambiguity, review and unknown-write behavior;
- owner-only NavGraph context, effective policies, assembled prompt and traces;
- separate state from Designer, Builder and deployed public sessions.

**Proof:** Real successful operation, autonomous clarification, user escalation, review, failure and unknown-write scenarios; diagnostics screenshots; desktop/mobile inspection; full Sandbox video.

### Step 9: Integrate the existing evaluation runtime into Corpus

Reuse the completed evaluation, immutable-result and eligibility capabilities.

Deliver:

- evaluation-set and case CRUD;
- categories and difficulty;
- exact Agent Build and source revision identity;
- immutable case and run results;
- eligible/ineligible decisions;
- Operations interaction promotion into an evaluation case;
- clarification-specific evaluation cases.

Required clarification evaluations:

- correctly resolve an operation from explicit context;
- correctly fill a parameter with provenance;
- escalate material ambiguity;
- reject missing unproven values;
- preserve write review;
- prevent clarification lookup calls;
- prevent secret exposure;
- resume the same run after a user answer.

**Proof:** Real exact-build evaluation runs, immutable reloadable results, eligibility change, failure remaining failure, screenshots and evaluation-run video.

### Step 10: Integrate the existing delivery runtime into Channels and Deployment

Reuse immutable deployment revisions, activation, rollback, pinned public sessions and redacted delivery evidence.

Deliver Channels:

- hosted Web channel;
- stable unique URL;
- enable/disable behavior;
- immutable build pinning;
- isolated public sessions.

Deliver Deployment:

- eligibility-gated deployment;
- durable asynchronous status;
- visible failure and explicit retry;
- activation of an immutable version;
- active public URL;
- rollback without mutating historical revisions.

Custom domains remain deferred.

**Proof:** Ineligible rejection, eligible deployment, public session, activation, version pinning, failure/retry and rollback; desktop/mobile screenshots; complete deployment/public-agent video.

### Step 11: Deliver Operations

Deliver:

- deployed interaction inventory;
- final user-visible results;
- redacted API and model/decision traces;
- clarification decision and provenance visibility;
- build, deployment and session identity;
- promotion of an interaction into an evaluation case.

Credentials, secret values and private runtime state must remain absent.

**Proof:** Public interaction -> owner Operations record -> trace inspection -> evaluation promotion, with redaction audit, screenshots and video.

### Step 12: Complete the full lifecycle audit

Exercise the complete real path:

```text
Create source
-> process ToolRouter revision
-> attach source
-> design agent
-> build immutable version
-> run Sandbox
-> evaluate exact build
-> create Web channel
-> deploy eligible build
-> use public agent
-> inspect Operations
-> promote interaction to evaluation
```

Run the lifecycle through:

- surface interactions;
- chat interactions;
- mixed surface/chat continuation;
- autonomous clarification;
- user-required clarification;
- success, failure, waiting, retry and recovery;
- reload and application restart;
- isolated owner and public sessions;
- representative desktop and mobile layouts.

## 5. Evidence Gate

Every user-visible slice must produce:

- successful real E2E execution;
- relevant failure and recovery execution;
- desktop screenshots;
- mobile screenshots;
- screenshots of important waiting, clarification, review and error states;
- video for the complete interaction sequence;
- saved runtime traces and identifiers;
- exact commands and smoke-test URLs;
- persistence/restart evidence;
- explicit limitations and unverified claims.

The final lifecycle receives one continuous E2E video plus a curated screenshot set. Evaluation results alone cannot close a feature.

Evidence must be stored under a clearly named repository artifact location and linked from the slice's validation log. Test fixtures and demos must remain explicitly labeled and cannot be presented as production evidence.

## 6. Primary File and Documentation Owners

Implementation primarily affects:

- Studio state, seed, readiness and evaluation-status components;
- `contracts/corpus-agent-design-routedeck-manifest.json`;
- existing Sources and Agents feature modules;
- new feature modules for Designer, Builder, Sandbox, Evaluation, Channels, Deployment and Operations;
- shared jobs, credentials, persistence and deployed-agent runtime modules;
- isolated integration adapters for API execution, agent execution and delivery;
- matching frontend feature clients, stores, surfaces and components.

After each slice, update only the applicable owners:

- `architecture/code-map.md`;
- relevant component documentation;
- `SYSTEM_FLOW_INDEX.md`;
- `test_index/README.md`;
- validation log and evidence index.

At Goal completion:

- refresh `context.md`;
- create the required session log and checkpoint;
- retain final commands, URLs, run IDs, counts, screenshots, videos and trace locations;
- report anything incomplete or unverified explicitly.

## 7. Completion Criteria

The Goal is complete only when:

- every launch behavior is accepted in Studio and mapped to current RouteDeck contracts;
- all launch features work through their real Corpus product surfaces;
- sibling runtime capabilities are integrated without duplicate product state or framework ownership;
- deployed agents autonomously resolve evidence-backed clarifications and safely escalate unresolved intent;
- the complete lifecycle works locally against real integrations;
- evaluation, E2E, screenshots, video, persistence, restart, failure and redaction evidence all pass;
- no mocks, fixtures, canned responses or silent fallbacks remain in product paths;
- RouteDeck and user-owned behavior notes remain unchanged;
- documentation accurately describes the delivered implementation.
