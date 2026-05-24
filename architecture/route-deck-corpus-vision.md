# RouteDeck + Corpus Vision

Date: 2026-05-19
Status: Canonical anti-drift vision for the RouteDeck refactor
Scope: RouteDeck foundation + Corpus foundation only

Related RouteDeck framework anchor: `../../routedeck/docs/agentic-ui-state-runtime.md`.

Read that document as the framework-level clarification of this vision: RouteDeck is graph-backed state management for agentic UI, not just a projection DTO or debugger package.

## Current Implementation Checkpoint - 2026-05-24

The RouteDeck direction has been tightened further:

```text
RouteDeck is the runtime/store layer for agentic UI.
Corpus is the SaaStoAgent product agent that consumes RouteDeck.
```

This means SaaStoAgent mounts a configured `RouteDeckStore` and reads RouteDeck
state through hooks. Corpus may choose legal operations and allowed surface
variants, but RouteDeck owns the generic state-management contract and
`CorpusRouteDeckRuntime` mediates commits/guard enforcement over
`CorpusGraphRuntime`.

The active backend boundary is:

- `/api/corpus/state` -> `route_deck_runtime.snapshot(...)`
- `/api/corpus/action` -> `route_deck_runtime.dispatch(...)`
- `/api/corpus/stream` -> RouteDeck projection events when subscribing to state,
  Corpus turn streaming when natural-language input is present

The active frontend boundary is:

- RouteDeck owns graph state, projection, operations, active surfaces, active
  SaaSAgent identity, and location.
- Zustand owns only local UI state such as active tabs, drafts, selected rows,
  and a mirrored active id for old shell ergonomics.

The current reset plan is captured in `../plans/routedeck_runtime_store_reset_plan.md`.

## Purpose

This document is the anti-drift reference for RouteDeck and Corpus.

Use it before:

- changing RouteDeck contracts
- adding RouteDeck UI/runtime behavior
- wiring Corpus turn behavior
- exposing diagnostics or graph visibility
- adding product-specific logic to reusable framework code

If implementation disagrees with this document, the implementation is wrong unless this document is intentionally updated first.

## Exact Grill QA Session

Extracted from the Codex chat dump. The key “grill QA” decisions are below. Source dump:

## Grill QA: RouteDeck + Corpus Vision

|  # | Grill question                                                                                                         | Your answer                                                                                                                                                           | Final decision                                                                                                                                              |
| -: | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
|  1 | Should the graph be runtime truth only, product metaphor, or hybrid?                                                   | Runtime truth with selective reveal. The app should remain cohesive, not disjoint.                                                                                    | **Everything is graph-owned, but not everything is graph-visible.** RouteDeck projects graph state into UI surfaces, diagnostics, and allowed interactions. |
|  2 | Should the LLM choose graph transitions directly, or only propose backend-validated capabilities?                      | LLM has full control over navigation intent. Graph state, conditions, and transition requirements should be visible to the LLM. Mandatory guards still apply.         | **LLM owns navigation intent. Graph kernel owns invariant enforcement.**                                                                                    |
|  3 | Should the LLM write graph state directly?                                                                             | “Legal operation set.”                                                                                                                                                | **No direct graph mutation.** LLM selects/fills typed legal operations. Runtime validates before commit.                                                    |
|  4 | Should operations execute immediately in `/turn`, or should `/turn` only propose and `/action` execute after approval? | Safe operations should execute directly. Side-effect actions should go through action/approval. Users should define what is safe/reviewable, with a full-access mode. | **Safe graph/navigation ops can auto-run during `/turn`. Side effects use proposal + `/action`.**                                                           |
|  5 | Should autonomy policy be global, per API/connection, or per operation/tool?                                           | Asked for pros/cons, then accepted hierarchy.                                                                                                                         | **Hierarchical autonomy policy:** SaaSAgent default → connection override → operation override.                                                             |
|  6 | Should the LLM see blocked operations by default?                                                                      | Hidden unless the LLM asks. Add meta tools for graph inspection.                                                                                                      | **Blocked operations are hidden from normal context.** The LLM can inspect them through read-only meta tools when needed.                                   |
|  7 | Should meta graph tools be internal-only or exposed in diagnostics too?                                                | Diagnostics too.                                                                                                                                                      | **The same introspection should power both LLM meta tools and developer/user diagnostics.**                                                                 |
|  8 | Should the LLM choose surface variants?                                                                                | Yes, but no direct mutation. LLM can choose surface variant.                                                                                                          | **Graph owns location. LLM can influence presentation only within allowed surface variants.**                                                               |
|  9 | Should surface variants be chosen every turn or persist?                                                               | Persist.                                                                                                                                                              | **Surface choices are sticky** until graph transition, explicit user request, or component event.                                                           |
| 10 | Should `presentation_state` be persisted backend graph state or ephemeral browser/session state?                       | Ephemeral. Start from home.                                                                                                                                           | **Product graph state is persistent. Presentation state is ephemeral.**                                                                                     |
| 11 | Should authenticated users always start at home, or should home resolve to dashboard?                                  | Home resolves to personalized dashboard. Before home, unauthenticated users have a lounge.                                                                            | **`home` is a resolver node, not a page.** Pre-auth users enter Lounge; authenticated users resolve to Dashboard.                                           |
| 12 | Should unauthenticated Lounge allow draft SaaSAgent/setup plans?                                                       | Only Q&A/exploration.                                                                                                                                                 | **Lounge is read-only platform exploration.** No SaaSAgent creation, credentials, uploads, or persisted setup.                                              |
| 13 | After login, should Corpus proactively start first SaaSAgent creation?                                                 | Wait for user intent. Suggest “Create my SaaS Agent,” then guide if selected.                                                                                         | **Dashboard shows suggestion actions, but onboarding does not auto-start.**                                                                                 |
| 14 | Is “Create SaaS Agent” a single node or a mini subgraph?                                                               | Mini subgraph.                                                                                                                                                        | **SaaSAgent creation is a bounded workflow graph**, not one form.                                                                                           |
| 15 | Should API connection setup happen during SaaSAgent creation or after?                                                 | Deferred. Build RouteDeck and Corpus first.                                                                                                                           | **Stop before SaaSToAgent-specific ops.** Current scope is RouteDeck + Corpus foundation.                                                                   |
| 16 | Should RouteDeck be product-specific or reusable?                                                                      | RouteDeck reusable; Corpus SaaSToAgent-specific.                                                                                                                      | **RouteDeck is the reusable app-state/navigation/surface runtime. Corpus is the SaaSToAgent agent runtime.**                                                |

## Condensed Decisions

**RouteDeck**

* Reusable graph-backed application runtime.
* Owns projection, legal operations, surfaces, presentation state, navigation commits, provider/hooks, diagnostics, and introspection.
* Must not contain hardcoded SaaSToAgent/SaaSAgent literals except fixtures/examples.
* Recomputed from graph state every turn; not a static navigation config.

**Corpus**

* SaaSToAgent-specific agent identity and runtime.
* Handles platform agent behavior, prompts, policy, personality, conversation, and platform-specific proposals.
* Chooses legal operations and allowed surface variants.
* Does not directly mutate graph state.

**Graph kernel**

* Owns persistent app truth.
* Enforces guards, invariants, permissions, required IDs, schemas, approval rules, and recovery.
* Returns recovery context when Corpus tries an invalid operation.

**Autonomy**

* Every operation has `safety_class`.
* Runtime resolves `execution_mode`: `auto`, `review`, or `blocked`.
* Policy hierarchy: SaaSAgent → connection → operation.
* Hard guards override full access.

**Diagnostics**

* Must show more than raw JSON.
* Should expose graph topology, current node, allowed operations, blocked reasons, guards, route reachability, surfaces, and traces.
* Meta tools and diagnostics should share the same read-only introspection layer.

**UI/surfaces**

* Surfaces are graph-declared and RouteDeck-projected.
* Corpus may choose among allowed surface variants.
* Surface choice persists until transition/user/component event.
* Presentation state is ephemeral.

**Platform flow**

```text
lounge -> auth -> home resolver -> personalized_dashboard
```

**Creation flow**

```text
dashboard
 -> saas_agent_create_start
 -> saas_agent_identity
 -> saas_agent_target_type
 -> api_source_choice
 -> api_connection_setup
 -> catalog_preview
 -> review_create
 -> agent_created
 -> dashboard | open_agent_interface
```

## Cohesive Vision

The application is graph-centric, agentic, and LLM-powered, but the graph is not the product metaphor.

The graph owns runtime truth:

- persistent state
- current node
- legal operations
- transition guards
- recovery rules
- allowed surface variants

Corpus is the primary product interface. The user talks to Corpus. Corpus sees graph state, legal operations, guards, and diagnostics context. Corpus chooses legal operations and presentation variants. Corpus does not directly patch graph state.

RouteDeck is the projection/runtime bridge between graph truth and application rendering. RouteDeck is not a second product layer, not a workflow-builder UI, and not a SaaSToAgent-specific shell.

The core relationship is:

```text
Corpus decides intent.
Graph commits state.
RouteDeck projects state into surfaces and diagnostics.
React renders the projected result around Corpus.
```

## Architecture Boundaries

### RouteDeck owns

- projection contracts
- legal operation contracts
- surface contracts
- presentation state contracts
- diagnostics contracts
- introspection/meta-tool contracts
- navigation commit interfaces
- reusable frontend provider/hooks/widgets

### RouteDeck must not own

- SaaSToAgent prompts
- Corpus personality
- product copy
- SaaSAgent-specific hardcoded literals
- business-specific flow assumptions
- direct LLM provider logic

### Corpus owns

- SaaSToAgent platform-agent behavior
- turn prompts and policies
- user-facing conversation
- operation selection from legal operations
- allowed surface variant selection
- platform-specific proposals

### Corpus must not own

- graph truth
- invariant enforcement
- direct raw state mutation
- bypass of graph guards
- reusable RouteDeck framework concerns

### Graph kernel owns

- persistent application truth
- eligibility
- transition validation
- guard enforcement
- approval gates
- recovery context

### Diagnostics/introspection own

- graph topology
- current node
- legal operations
- blocked reasons
- guard explanations
- route reachability
- surface projection state
- trace/recovery context

Diagnostics must be read-only.

## Dos

- Do treat the graph as the source of truth.
- Do let Corpus control navigation intent through typed legal operations.
- Do validate every selected operation against guards before commit.
- Do keep blocked operations hidden from normal LLM context.
- Do expose blocked reasoning through read-only meta tools and diagnostics.
- Do let Corpus choose only from allowed surface variants.
- Do persist presentation choices only ephemerally.
- Do reset unauthenticated entry to Lounge.
- Do resolve authenticated `home` into Dashboard.
- Do treat suggestions as proposals, not auto-transitions.
- Do keep RouteDeck reusable and product-agnostic.
- Do make diagnostics richer than raw JSON.
- Do use this document as the anti-drift review gate.

## Don'ts

- Do not let RouteDeck contain SaaSToAgent or SaaSAgent literals in framework code.
- Do not let Corpus directly mutate graph state.
- Do not expose raw legal operations as the default product UI just because they are eligible.
- Do not open forms or work surfaces merely because they are eligible.
- Do not make the graph the default user-facing metaphor.
- Do not let the frontend invent navigation truth outside the graph.
- Do not treat `home` as a static page.
- Do not let Lounge create drafts, collect credentials, or persist setup state.
- Do not auto-start onboarding after login.
- Do not turn RouteDeck into a second product shell.
- Do not couple RouteDeck contracts to SaaSToAgent copy, prompts, or domain models.
- Do not continue implementation when it conflicts with this vision without first updating this document.

## Anti-Drift Review Checklist

Before accepting any RouteDeck or Corpus change, check:

1. Is this logic graph truth, Corpus behavior, or RouteDeck projection?
2. Did any SaaSToAgent-specific literal leak into reusable RouteDeck code?
3. Is the UI rendering an eligible capability directly instead of an agent-authored proposal or initiated surface?
4. Is Corpus selecting a typed legal operation rather than patching raw state?
5. Are blocked operations hidden from default context and available only through introspection?
6. Does diagnostics expose meaningful graph/runtime understanding beyond JSON dumps?
7. Is presentation state ephemeral rather than persistent product truth?
8. Does the change preserve Corpus as the central interface?

If any answer is wrong, stop and refactor before continuing.

## Immediate Implications For The Current Refactor

- RouteDeck must be audited for hardcoded `saas_agent` and similar product literals.
- Current UI work must be judged against the proposal/surface contract, not just technical rendering.
- Existing ADRs or docs that say the frontend should render eligible actions directly are now stale and must be treated as superseded by this vision.
- Current scope remains RouteDeck + Corpus foundation, not deeper SaaSToAgent setup workflows.
