# Corpus Sandbox Agent Design

**Status:** Product boundaries and deployment-mode architecture approved on 2026-08-19; implementation authorized.

## Purpose

Corpus Sandbox is the owner's private, RouteDeck-powered deployment of an exact immutable Agent build. It behaves like a deployed Agent: the owner can create conversations, send messages, resolve clarifications and reviewed writes, and exercise the real model, ToolRouter, API, source, policy, and credential paths compiled into that build.

Sandbox also provides the execution target for defined evaluation sets. The owner can launch an evalset against the private Sandbox Agent and inspect its results without publishing an Agent or contaminating a normal playground conversation.

The Sandbox is not an owner-workspace operation that merely invokes a diagnostic service. It is a real Agent runtime with a private admission boundary, its own lifecycle, sessions, persistence, and product surface.

## Product Definition

For an immutable Agent build, Corpus can create RouteDeck-powered deployments in two modes:

1. `sandbox`, admitted only to the authenticated owning user; and
2. `delivery`, admitted through its configured public or channel boundary.

Both modes use the same Agent deployment, activation, session, message, review, and RouteDeck execution services. Mode policies change admission, exposure, allowed session purposes, and evidence projection. Deployments never share sessions, conversations, interaction history, activation state, or operational projections.

The Sandbox product surface has three owner-facing capabilities:

- **Playground:** persistent, multi-turn conversations with the private Agent;
- **Evaluations:** select and run a defined evalset against isolated Sandbox sessions; and
- **Diagnostics:** inspect Sandbox-owned runtime evidence without inserting diagnostics into the conversation transcript.

## Boundaries

### Owned by Sandbox

- provisioning and lifecycle of a private Sandbox Agent instance for an exact build;
- owning-user-authenticated admission to that instance;
- playground conversation creation and continuation;
- Sandbox session and interaction persistence;
- execution-target controls used to launch an evalset against the Sandbox Agent;
- owner-facing Playground, Evaluations, and Diagnostics presentation.

### Owned by Evaluation

- evalset definitions, cases, revisions, and versioning;
- ToolRouter-generated and owner-authored evalset provenance;
- durable batch and case-run state;
- case results, metrics, eligibility, retry lineage, and comparisons;
- the rule that every case executes in a fresh isolated Sandbox session.

The Sandbox UI may initiate and present Evaluation-owned work. That placement does not transfer result or lifecycle ownership into Sandbox conversation history.

### Owned by Delivery

- deployment and channel admission;
- public or channel session identity;
- Delivery conversation and interaction persistence;
- public projection and Delivery Operations evidence.

### Owned by the shared Agent deployment runtime

- mode-neutral deployment targets, revisions, verification, and activation;
- session purposes: `playground`, `evaluation_case`, and `delivered_conversation`;
- exact-build RouteDeck application restoration;
- RouteDeck session provisioning and loading;
- model and ToolRouter execution;
- API, source, policy, capability, and credential enforcement;
- bounded same-session context;
- clarification and reviewed-write semantics;
- neutral conversation projection.

The shared runtime owns neutral mechanics, not Corpus authentication, channel configuration, Evaluation results, or product-facing evidence ownership.

### Explicitly unchanged by this feature

- Studio authoring and immutable build compilation;
- public channel and deployed-Agent admission contracts;
- the owner workspace RouteDeck application;
- credential ownership and secret storage;
- ToolRouter generation contracts;
- Evaluation's authority over definitions and results;
- Operations' authority over deployed-Agent evidence.

## Selected Architecture

Generalize `agent-delivery-runtime` from a Web-channel host into a mode-neutral Agent deployment host without renaming the package. Its v0.2 contract introduces `DeploymentMode`, `SessionPurpose`, neutral deployment targets, revisions, activations, sessions, interactions, and an `AgentHostService`. The existing `ChannelHostService` remains a compatibility wrapper over the generic host.

Corpus supplies product policies around that shared host:

- Sandbox resolves the authenticated owner and the Agent's one private deployment target, allows `playground` and `evaluation_case` sessions, and projects private diagnostics.
- Delivery resolves channel/public admission, allows `delivered_conversation` sessions, and projects deployed Operations evidence.
- Both use the existing `CorpusDeployedAgentRuntimePort`, `AgentRouteDeckSupervisor`, and neutral execution adapter for the exact compiled build.

```text
Immutable Agent build
        |
        v
Agent deployment target + immutable mode
        |
        v
Shared Agent deployment host
        |
        v
Corpus deployed-Agent runtime port
        |
        v
Exact per-build RouteDeck application

sandbox policy --> owner admission + Playground/eval + private diagnostics
delivery policy -> channel admission + delivered sessions + Operations
```

The shared host's conceptual contract is:

```text
request_deployment(target, mode, immutable_bundle, request_id) -> deployment
activate_ready_deployment(target, deployment) -> activation
create_session(target, purpose) -> session + projection
projection(target, session) -> AgentConversationProjection
invoke(target, session, message, request_id) -> interaction + projection
resolve_review(target, session, review_id, decision, request_id) -> interaction + projection
```

The concrete contract requires target, deployment, mode, build, and session binding on every call. A bare conversation ID is insufficient authority.

## Alternatives Considered

### Owner workspace operations as the chat transport

Rejected. Adding operations such as `sandbox.start` and `sandbox.send_message` to the owner workspace would keep the owner-host RouteDeck surface in control of the conversation. That produces a diagnostic tool invocation flow, not a separately deployed private Agent.

### Hidden Delivery channel or private fake deployment

Rejected. Reusing public Delivery endpoints or fabricating a private channel would blur Sandbox and Delivery ownership, couple private testing to channel lifecycle, and risk mixing session and Operations evidence.

### Separate Sandbox execution adapter

Rejected. Even with a shared low-level kernel, separate Sandbox and Delivery host services would duplicate deployment, activation, session, interaction, and review behavior. The correct reuse boundary is one mode-neutral deployment host with explicit mode policies.

## Sandbox Instance Lifecycle

1. The owner selects an Agent with a ready immutable build and explicitly chooses **Deploy to Sandbox**.
2. Corpus requests a `sandbox` deployment revision on the Agent's one owner-private Sandbox target. Evaluation eligibility is not required.
3. The shared host verifies the exact compiled application and dependencies before atomically activating the revision.
4. A failed replacement leaves the prior ready deployment active. A successful replacement supersedes it without mutating it or its sessions.
5. Existing sessions stay pinned to their original deployment and build and are never silently upgraded.
6. Publishing the same build creates a separate `delivery` deployment revision on a channel target. It does not promote, rename, or reuse the Sandbox deployment.

Provisioning failure is terminal for that attempt and visible to the owner. Corpus must not fall back to another build, provider, model, cached response, mock runtime, or generic Agent.

## Playground Conversation Lifecycle

1. The owner opens the Sandbox instance and creates a new conversation.
2. Sandbox creates a Sandbox-owned session pinned to the instance and exact build.
3. Every message continues that same RouteDeck session until the owner starts a new conversation.
4. The runtime preserves bounded same-session context and returns the same neutral conversation states used by a deployed Agent, including clarification and reviewed-write states.
5. Review acceptance or rejection is scoped to the same owner, instance, session, and pending review identity.
6. Reloading the UI or restarting the backend restores the persisted Sandbox conversation and exact build binding.

A normal Playground conversation never shares a session with an evaluation case.

## Evaluation Execution Lifecycle

1. In the Sandbox Evaluations surface, the owner selects a defined evalset version and an exact Sandbox instance.
2. The Sandbox control delegates to the Evaluation application service to create a durable Evaluation run targeting that exact Sandbox deployment.
3. Evaluation snapshots the case revisions and required execution identities before dispatch.
4. For every case, the runner creates a fresh `evaluation_case` session through the shared Agent host.
5. The case executes through the same deployed-Agent runtime port and exact compiled RouteDeck application as an interactive `playground` session.
6. Evaluation records the resulting output, operation evidence, failure, metrics, and identity lineage in Evaluation-owned storage.
7. The case session is never reused by another case, a retry, or the Playground. A retry creates a new session and links explicitly to the failed attempt.
8. The owner sees durable queued, running, succeeded, and failed batch and case states in the Sandbox Evaluations surface.

There is no automatic retry and no fallback execution path. Dependency, credential, model, ToolRouter, source, policy, or API failures remain failures and are attributed to the exact case attempt.

## API and Transport Boundary

Sandbox Agent endpoints are owner-authenticated and distinct from both the owner workspace RouteDeck operation API and public Delivery endpoints. The endpoint family must expose these capabilities:

- provision or resolve an exact-build Sandbox instance;
- create a Sandbox conversation session;
- read the owner-safe conversation projection;
- send a message;
- accept or reject a pending review;
- create an Evaluation-owned run targeting the Sandbox instance;
- read Evaluation-owned run and case projections for presentation in Sandbox.

Every request resolves tenant partition, owning user, Agent, Sandbox instance, session, and build binding server-side. The tenant partition is not an additional Sandbox audience: access still requires the authenticated owning user. The browser does not gain authority by presenting an opaque ID. Public Delivery credentials or slugs cannot address a Sandbox session, and Sandbox authentication cannot address a public Delivery session through these endpoints.

## Identity and Persistence

Every Sandbox instance records at least:

- tenant and owning-user identity;
- Agent identity;
- immutable build ID and build hash;
- compiled RouteDeck application identity;
- effective model, ToolRouter, source/profile, capability, policy, API, and credential-version identities;
- lifecycle state and timestamps.

Every Sandbox conversation and interaction records at least:

- Sandbox instance and session identity;
- exact build binding;
- request and interaction identity;
- neutral result state;
- clarification or review identity when applicable;
- runtime evidence references and timestamps.

Existing `agent_sandbox_sessions` and `agent_sandbox_runs` remain read-only v0.1 evidence and receive no fabricated deployment lineage. New Sandbox deployments, activations, sessions, and interactions use the generalized deployment contracts and stores, partitioned by target, mode, deployment, and session purpose.

Evaluation records additionally pin evalset, evalset version, case, case revision, batch, attempt, Sandbox instance, fresh Sandbox session, build, runtime configuration, result, and retry lineage identities.

## Owner-Facing Experience

The Sandbox page presents the private Agent, not a form for invoking owner workspace operations.

### Playground

- conversation shell with Agent and owner messages;
- new-conversation control;
- persistent conversation history for the selected Sandbox instance;
- clarification inputs and reviewed-write decisions;
- explicit loading, failure, unavailable, and stale-build states.

The interaction model may reuse presentational components from the deployed Agent shell, but it must use the Sandbox adapter and owner-authenticated Sandbox APIs.

### Evaluations

- list of defined evalsets and their versions;
- explicit target Sandbox build and instance;
- launch control;
- durable batch and per-case progress;
- result, metric, failure, and retry-lineage inspection;
- no insertion of case traffic into Playground history.

### Diagnostics

- exact build and runtime identities;
- ToolRouter and operation evidence appropriate for the owner;
- source, policy, capability, credential-readiness, and failure diagnostics;
- no leakage into the Agent-facing conversation projection.

## Failure, Privacy, and Isolation Semantics

- Sandbox admission is private to the authenticated owning user and denied by default.
- A Sandbox session is accessible only through its owning Sandbox instance and authenticated owner boundary.
- A deployed Agent cannot read, continue, review, or enumerate Sandbox sessions.
- Sandbox actions do not create channel deployments, public slugs, or deployed Operations entries.
- Evaluation case sessions are isolated from Playground sessions and from each other.
- Wrong or unavailable credentials fail explicitly; they are never substituted.
- Build mismatch, stale instance identity, missing RouteDeck application, or unavailable dependency fails loudly.
- Secret values remain server-side and are never included in owner projections, transcripts, eval results, or diagnostics.
- Idempotency keys prevent duplicate message, review, and eval-launch effects without converting a failed operation into success.

## Behavior-First Delivery Sequence

After this written spec is approved, delivery follows the Corpus behavior-first process:

1. correct the Sandbox and Evaluation behavior notes to state the private-deployment model and isolated eval-case sessions;
2. update the accepted Studio/Sandbox experience and feature-to-code mapping before source changes;
3. generalize `agent-delivery-runtime` to the neutral deployment-mode contract with focused boundary tests;
4. preserve deployed Delivery behavior through the channel compatibility wrapper;
5. implement Corpus Sandbox target policy, explicit deployment, persistence, and authenticated transport;
6. deliver the persistent Playground vertical path through the real RouteDeck runtime;
7. connect Evaluation-owned batch execution to fresh Sandbox sessions;
8. deliver Evaluations and Diagnostics surfaces;
9. validate the complete local product path against a real integration target;
10. run the canonical full audit only after isolated Sandbox and Evaluation evidence passes.

The existing `2026-08-19-v02-sandbox-playground.md` plan must be replaced after approval because its owner-workspace-operation transport is not the accepted architecture.

## Verification Strategy

Verification must exercise the running local product and real integration path. Unit tests protect identity, lifecycle, isolation, projection, and failure contracts, but do not substitute for product proof.

Required evidence includes:

- provisioning a private Sandbox instance for a real ready build;
- multi-turn Playground conversation continuity across browser reload and backend restart;
- clarification and reviewed-write behavior through the Sandbox UI;
- real model, ToolRouter, API, source, policy, and credential execution where the selected Agent requires them;
- the same immutable build running simultaneously as Sandbox and deployed Agent without shared state;
- rejection of cross-owner, public-to-Sandbox, Sandbox-to-public, and wrong-build session access;
- running a defined evalset from Sandbox with a distinct fresh session for every case and retry;
- durable Evaluation-owned batch, case, result, metric, failure, and lineage projection;
- proof that eval traffic does not appear in Playground history or deployed Operations;
- explicit dependency and credential failure with no fallback;
- rendered desktop and mobile inspection of Playground, Evaluations, Diagnostics, and failure states.

## Acceptance Criteria

The feature is complete only when all of the following are true:

1. Sandbox is visibly and operationally an owner-only deployment of an exact immutable Agent build.
2. The owner can create and continue persistent, multi-turn conversations through the real per-build RouteDeck application.
3. Sandbox and deployed Agent instances share execution semantics but have separate admission, lifecycle, sessions, stores, and evidence.
4. Public or channel identities cannot access Sandbox sessions, and Sandbox identities cannot access Delivery sessions.
5. The owner can launch a defined evalset against the selected Sandbox instance.
6. Every eval case and retry uses a fresh isolated Sandbox session.
7. Evaluation owns durable definitions, progress, results, metrics, eligibility, and retry lineage, even when presented inside Sandbox.
8. Eval traffic does not contaminate Playground conversation history or deployed Operations.
9. Reload and backend restart preserve exact Sandbox instance, build, conversation, and Evaluation-run identity.
10. Required integration failures are explicit and no mock, fixture, alternate provider, cached output, or generic response appears in the product path.
11. The local end-to-end path is proven against the real target integration and the exact smoke-test commands and URLs are recorded.

## Explicit Exclusions

- automatic promotion of Sandbox sessions or eval results into deployed sessions;
- a hidden or fake Delivery channel for private testing;
- owner workspace operations as the primary Sandbox conversation transport;
- automatic retries or fallback providers;
- shared sessions between Playground and evals or between eval cases;
- changing Studio authoring, build immutability, channel deployment, credential ownership, or public Agent behavior as part of the Sandbox feature;
- treating standalone RouteDeck or ToolRouter proof as completion of the Corpus Sandbox product path.
