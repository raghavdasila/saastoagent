# Corpus Product Definition

Status: locked layout, proposed feature contracts

Updated: 2026-07-25

## Vision

Corpus is a chat-first agentic app for assembling and operating deployed agents.
An owner works through a permanent Corpus conversation and typed surfaces.
RouteDeck supplies the legal topology and scopes the Corpus agent to the prompt,
context, tools, operations, and surfaces available at the active node.

Corpus deploys **agents**. In this product vocabulary, an **agentic app** is a
separate application category and is not a synonym for a deployed agent.

## Primary Interaction Contract

The Corpus agent is part of Corpus itself, not an optional assistant feature.
RouteDeck lets one primary agent move across product features without carrying
unbounded scope:

```text
active RouteDeck node
  -> node-scoped prompt and context
  -> node-scoped tools and legal operations
  -> node-scoped surfaces
  -> typed operation outcome
  -> next legal node
```

Features own product meaning. RouteDeck owns generic interaction state.

## Feature Set

The layout contains **15 features**. This is an ownership grouping, not the
Navgraph.

| # | Feature | Purpose | Principal connections and surfaces |
| ---: | --- | --- | --- |
| 1 | Workspace | Owner, organization, tenancy and current working context | Workspace frame, selector, activity and Corpus-memory entry points |
| 2 | Agents | Create, inspect, version and configure deployed agents | Agent list, overview, revision and Agent Configuration surfaces |
| 3 | Source Hub | Unified source inventory, health, manifests and agent bindings | Source list, readiness, binding and failure surfaces |
| 4 | API Source | Connect APIs/OpenAPI and curate discovered operations | Connection, inspection, operation selection and readiness |
| 5 | Database Source | Connect databases and define safe resource/action boundaries | Connection, schema inspection, resource selection and mutation policy |
| 6 | Knowledge Source | Configure Agentic-GRAG ingestion, retrieval and evidence | Source ingestion, indexing, readiness and evidence preview |
| 7 | MCP Source | Connect Smithery MCP servers and curate tools/resources/prompts | Discovery, authorization, primitive inspection and readiness |
| 8 | Agent Designer | Propose the agent design, Navgraph, node capabilities, policies and surfaces | Brief, design conversation, topology/policy review and proposal |
| 9 | Agent Builder | Materialize an accepted design as a versioned runnable agent artifact | Build status, generated inventory, diagnostics and artifact review |
| 10 | Sandbox | Interactively run the actual draft agent in isolated RouteDeck state with controlled bindings | Conversation, state inspector, surface preview, trace and run evidence |
| 11 | Evaluation | Define evalsets, execute repeatable checks, compare revisions and decide readiness | Evalset library/editor, run matrix, case trace, evidence, diff and gate summary |
| 12 | Channels | Configure where and how an agent interacts | Channel catalog, credentials, identity mapping, surface compatibility, test and health |
| 13 | Deployment | Release a validated agent revision to environments and channel targets | Revision selection, dependency review, rollout, active status and rollback |
| 14 | Operations | Observe and intervene in live deployed-agent behavior | Health, sessions, traces, reviews, source calls, failures and recovery |
| 15 | Learning | Turn evidence into governed improvement candidates | Inbox, evidence review, change proposal and owner decision |

## First Launch Feature Subset

The v0.1 first launch uses **11 of the 15 features**. It proves a basic
RouteDeck-powered agent path with one real source family: API collections.

| Launch # | Feature | Relationship to the 15-feature map |
| ---: | --- | --- |
| 1 | Workspace | Included |
| 2 | Agents | Included |
| 3 | Source Hub | Included |
| 4 | API Source / API Collection | Included as the first source connector |
| 5 | Agent Designer | Included; planner/executor behavior remains to be formalized |
| 6 | Agent Builder | Included |
| 7 | Sandbox | Included |
| 8 | Evaluation | Included |
| 9 | Channels | Included with Web as the first channel |
| 10 | Deployment | Included |
| 11 | Operations | Included as the minimum behavior/logging surface |

Deferred from first launch: Database Source, Knowledge Source, MCP Source, and
Learning. Authentication is required host infrastructure, not a separate product
feature in this feature map.

## Evaluation And Evalsets

Sandbox answers whether an owner can explore a draft safely. Evaluation answers
whether an exact revision repeatedly satisfies explicit requirements.

An evalset is a versioned collection of cases, inputs, binding profiles,
expected outcomes, assertions and readiness rules. The Evaluation UI must make
the evidence legible rather than reducing it to one score:

- evalset library and editor;
- case authoring and capture from Sandbox;
- source and channel test profiles;
- batch run matrix;
- case-level RouteDeck trace and projected surfaces;
- expected-versus-actual evidence;
- revision comparison;
- deployment gate summary.

Evaluation results are immutable evidence pinned to the tested Agent
Configuration revision. They may block deployment and may create Learning
candidates; they never rewrite the revision they tested.

## Channels

Channels are a first-class owner journey because every channel has its own
credentials, user identity, interaction constraints, supported surfaces,
delivery semantics, rollout status and health. Initial candidates include web,
embedded widget, API, Slack and WhatsApp, but concrete channel support remains
an implementation decision.

A channel binding points to an exact agent revision and declares its compatible
surface and interaction contract. Deployment activates a revision against one
or more validated channel targets.

## Agent Configuration

The contracts previously described as governance, reproducibility, model
configuration, memory and delivery are parts of the versioned Agent
Configuration, not separate features:

```text
Agent Configuration
├── identity and instructions
├── RouteDeck Navgraph and node scopes
├── source bindings
├── operations and review policies
├── standard and custom surfaces
├── model-role bindings
├── memory configuration
├── access, safety, budgets and retention
├── channel bindings
└── revision lineage
```

Sandbox runs, evaluation results, deployments, sessions, traces and learning
candidates must pin the exact relevant revision.

## Memory

Memory belongs to an agent:

- Corpus has memory about its owner and their work.
- Each deployed agent has its own configured memory scopes and retention rules.
- Knowledge is sourced evidence; memory is retained context; learning is a
  governed proposal to change future behavior.

Detailed memory design is intentionally deferred until the remaining feature
and Agent Configuration contracts are refined.

## Product Lifecycle Relationship

The following is a product relationship, **not a Navgraph**:

```text
Connect sources -> Design -> Build -> Sandbox -> Evaluate -> Configure channels
      -> Deploy -> Operate -> Learn -> create a new design revision
```

The Navgraph separately defines the exact legal nodes and transitions through
which Corpus supports those journeys.
