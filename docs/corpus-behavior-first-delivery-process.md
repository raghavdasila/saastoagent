# Corpus Behavior-First Delivery Process

Status: controlling process for behavior-led product changes

This document defines how an intended Corpus behavior moves from owner intent
to accepted implementation. It is separate from the behavior evidence ledger:
the process governs product delivery, while the ledger records what the real
application visibly did.

## Truth Owners

| Concern | Owner |
| --- | --- |
| Product intent and launch baseline | User-owned `docs/corpus-agent-design/feature-behavior-notes.md` |
| Product interaction design | Accepted Design Studio state in `docs/corpus-agent-design/workbench/design-state.json` |
| Studio-to-runtime identifier mapping | `contracts/corpus-agent-design-routedeck-manifest.json` |
| Framework mechanics | Current RouteDeck contracts, read-only unless a named change is authorized |
| Product implementation | Corpus source in the owning feature/module |
| Observed behavior truth | `docs/corpus-behavior-evidence-ledger.md` and `audits/2026-08-v0.2-behavior-audit/` |
| Repeatable audit operation | `skills/audit-corpus-behaviors/SKILL.md` |
| Architecture ownership | `architecture/code-map.md` and the relevant component document |
| Test meaning and commands | `test_index/README.md` |
| Current restart state | `context.md` and the latest checkpoint |

The Behavior Notes are read-only to implementation agents. They are never
rewritten to make an implementation appear correct. Studio owns product
meaning, not technical identifiers. The manifest maps accepted Studio meaning
to compiled contracts but is not a substitute for product design.

## Delivery Flow

```text
Owner behavior
  -> accepted Studio design
  -> RouteDeck mapping gate
  -> Corpus vertical implementation
  -> isolated real-product validation
  -> canonical ledger retest
  -> release-level horizontal acceptance
```

Tests protect the flow. Test counts do not replace it.

## Two Lanes That Must Not Be Mixed

### Audit lane

The audit lane observes the authoritative application as-is. Product source,
Studio behavior, RouteDeck, and the database are read-only during the audit.
The canonical recorder produces `ledger.json`, `tasks.json`, the dashboard,
and screenshot evidence under `audits/2026-08-v0.2-behavior-audit/`.

Use `skills/audit-corpus-behaviors/SKILL.md` and
`docs/corpus-behavior-evidence-ledger.md` for the exact audit procedure. A
failed, blocked, or pending record remains evidence truth. Editing its task does
not create a pass.

### Product-fix lane

The product-fix lane starts from an evidence-backed ledger task or an explicit
owner request. It may change only the authorized Corpus owners needed to
deliver the behavior. It must not edit ledger results to match the fix.

After a fix, narrow runtime evidence may prove the implementation slice, but
the canonical ledger changes only after a fresh real-product observation under
the audit contract.

The current audit recorder has no selective behavior, feature, resume, or
from-depth filter. Do not manufacture an incremental ledger update. If a
selective retest is required, stop and obtain explicit authorization for that
recorder capability; otherwise follow the existing full-campaign contract.

## Step 1: Establish Authority And Scope

Before the first mutation:

1. Read `critical_prompt.md`, `context.md`, the latest checkpoint,
   `instructions.md`, `context_pipeline.md`, `architecture/code-map.md`, the
   relevant component document, and any active plan.
2. Read the relevant owner-authored Behavior Note, accepted Studio behavior,
   manifest mapping, current ledger record/task, Corpus implementation, and
   RouteDeck contract.
3. Record what visibly works, what is merely implemented, what is integrated,
   and what is absent, broken, confusing, or unproven.
4. Identify the owning architecture row and both neighboring feature handoffs.
5. Declare the mutation allowlist: exact files, modules, repositories,
   services, environments, and data identities that may change. Everything
   else is read-only.
6. State the owner-visible acceptance evidence and failure semantics required
   for completion.

If the behavior cannot be delivered inside that boundary, stop before changing
an adjacent owner and request an explicit decision.

## Step 2: Define One Owner-Observable Behavior

Translate the intended behavior into:

- initiating owner intent or product event;
- visible intermediate, waiting, and review states;
- successful outcome;
- failure, retry, and recovery semantics;
- persisted identities and lineage that must survive;
- incoming and outgoing handoffs;
- chat-only, surface-only, and hybrid expectations; and
- sensitive values that must remain surface-only.

Use ordinary product language. Do not put feature names, operation IDs,
RouteDeck nodes, routes, entity IDs, or recorder-oriented click instructions in
owner chat prompts.

## Step 3: Correct Product Design First

If the intended behavior materially differs from Studio, correct and accept
Studio before implementing it. Studio may define:

- user stories and natural owner intent;
- policies and safety boundaries;
- operations and product consequences;
- suggested actions;
- surfaces and navigation;
- review and clarification behavior; and
- explicit scope and deferred behavior.

Studio must not prescribe backend classes, providers, guards, bindings,
storage, or RouteDeck identifiers. Those belong to mapping and implementation.

## Step 4: Pass The RouteDeck Mapping Gate

Write this mapping before implementation:

```text
Studio concept -> existing RouteDeck contract -> Corpus implementation owner
```

Separate ownership explicitly:

- RouteDeck owns legal topology, reviews, projection, session mechanics, and
  supervised operation execution.
- Corpus owns product meaning, persistence, identities, services, adapters,
  routes, copy, and rendered product surfaces.
- The manifest owns accepted Studio-to-compiled identifier mapping.

Inspect RouteDeck before declaring a primitive missing. If a genuine gap is
proven, stop and report the exact repository/files, insufficient contract,
smallest proposed change, compatibility impact, and validation. Only a named,
authorized RouteDeck change may proceed, and its purpose must be recorded.

## Step 5: Implement The Smallest Complete Vertical Slice

Carry the behavior through every required layer:

```text
persistence
  -> domain/service
  -> supervised operation and policy
  -> frontend authoritative state
  -> rendered surface
  -> chat interaction where permitted
  -> failure/recovery
  -> both neighboring handoffs
```

Reuse working modules through their real public contracts. Do not reconstruct
a working module inside a surface, adapter, neighboring feature, or recorder.
Never use fixtures, canned responses, heuristic stand-ins, cached success,
automatic retry, or silent fallback in a product path.

Prioritize the usable behavior over broad test expansion and non-blocking
polish. Fix an observed regression immediately only when it blocks the active
behavior, violates ownership, safety, or lineage, corrupts data, or makes
evidence untruthful. Record lesser regressions in the evidence-backed task.

## Step 6: Validate The Feature In Isolation

Exercise the real product before broad testing:

1. real persistence and integrations;
2. owner-visible desktop interaction;
3. maximized split layout for work-heavy surfaces;
4. representative mobile interaction;
5. material failure, waiting, review, retry, and recovery states; and
6. focused tests for contracts actually at risk.

Every material non-sensitive behavior requires independent evidence for:

- **Chat-only:** the configured real model receives ordinary owner language and
  completes the behavior through legal operations. Expected operation IDs may
  be assertions but never prompt instructions.
- **Surface-only:** direct declared controls complete the behavior without chat
  assistance.
- **Hybrid:** chat and surfaces alternate while retaining the same task,
  identities, authoritative state, and operation chronology without replaying
  completed work.

Passwords, credentials, and similarly sensitive values remain surface-only.

An isolated feature campaign has a short, declared wall-clock limit. Capture
normal-speed evidence with the working surface maximized where appropriate,
plus exact identities, safe diagnostics, and the relevant desktop/mobile
states. A failed run remains failed. Diagnose it offline and return to the
owning feature instead of replaying the complete product.

## Step 7: Retest Through The Behavior Ledger

Use the task and its linked record as the retest contract:

- preserve the original expected and observed behavior;
- retain the exact feature, prerequisite graph, mode, and evidence lineage;
- change task workflow state without changing prior evidence truth;
- rerun only through capabilities supported by the canonical recorder;
- require a fresh visible product observation before recording `passed`;
- retain ordered screenshots, hashes, classified diagnostics, and attempt
  history; and
- keep every failed, blocked, or pending result linked to a task.

The ledger result semantics remain owned by
`docs/corpus-behavior-evidence-ledger.md`. This process must not introduce a
second ledger schema, dashboard, runner, or status vocabulary.

## Step 8: Run Horizontal Acceptance Only At The Gate

Do not use a complete product journey to debug an isolated feature. A
release-level horizontal run is permitted only after every blocking behavior
record for that slice has fresh accepted evidence.

At that gate:

1. run broad backend, frontend, Studio, generated-contract, manifest parity,
   architecture, documentation, migration, and runtime-health gates once;
2. run one current ordinary-chat-only journey, one surface-only journey, and
   one hybrid journey;
3. retain normal-speed uncut evidence and exact lineage for each independent
   run; and
4. if a journey fails, preserve it as failed and return only to the owning
   behavior/task—never loop the complete journey as a debugger.

## Step 9: Close And Reconcile Truth Owners

After acceptance, update only the owners whose meaning changed:

- accepted Studio state;
- Studio-to-implementation manifest;
- Corpus implementation and generated contract;
- authorized RouteDeck change report;
- code map and component documents;
- system-flow and test indexes;
- behavior ledger/task/dashboard through the canonical audit workflow;
- validation log and evidence hashes; and
- checkpoint and concise `context.md` restart state.

Keep detailed contracts in their primary owners. `context.md` links to current
truth; it does not become the process, architecture, or evidence ledger.

## Completion Standard

A behavior is complete only when its current product path works, required
interaction modes are freshly observed, handoffs and lineage are preserved,
failure semantics are truthful, the canonical ledger record is current, and
all authority owners agree.

A compiled surface, CRUD endpoint, passing test count, edited task, isolated
mock, or historical horizontal journey is not completion by itself.

## Anti-Drift Rules

- Behavior Notes remain the owner authority and are never rewritten by an
  implementation agent.
- Studio is corrected before materially different product behavior is coded.
- RouteDeck is inspected before a framework gap is claimed.
- Audit collection and product mutation never occur in the same campaign.
- Product semantics are not moved into recorder prompts or tests.
- Natural chat is not spoonfed with internal names or microscopic steps.
- A working feature is not reconstructed inside an integration layer.
- Isolated feature evidence precedes horizontal evidence.
- Failures remain failed; no assertion weakening or fallback makes them pass.
- The canonical behavior ledger is observed truth, not a mutable progress
  narrative or implementation plan.
