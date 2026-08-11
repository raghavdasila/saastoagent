# Staged API source orchestration

## Authority correction

The accepted Studio behavior now makes the file boundary explicit:

- attaching an OpenAPI file stages owner input for the current authenticated conversation;
- staging does not create a Source, start ToolRouter, or attach a Source to an Agent;
- a normal owner request may authorize Corpus to add and analyze the staged definition;
- missing Agent identity, goal/responsibility, or operation-selection intent is clarified naturally;
- attachment occurs only after the exact Source revision is ready.

## RouteDeck mapping gate

| Studio concept | Existing RouteDeck contract | Corpus owner |
| --- | --- | --- |
| Stage binary file | Not a RouteDeck operation. Authenticated same-origin HTTP is the binary transport; the record is bound to owner, public conversation, and RouteDeck session. | `features/sources/connectors/api/staged_attachments.py`, connector HTTP, Source client |
| Add staged API definition | Draft operation, Agent + Surface, strict empty input, public typed result, normal guard/handler failure semantics. | `sources.accept_staged_api`, Sources declarations/handler/binding |
| Analyze accepted API version | Draft operation, Agent + Surface, explicit queue outcome, durable worker remains Corpus-owned. | `sources.process_api`, Sources declarations/handler/binding/service |
| Preserve selected Agent while adding Source | Existing private Agent entity binding and existing `agents.open_source_creation` navigation. | Agents feature plus Sources surface projection |
| Attach ready Source | Existing `agents.attach_created_source`; server may resolve the sole eligible unattached ready Source when no Source ID is supplied. | Agents handler/service |
| Continue after navigation | Existing RouteDeck multi-operation chat semantics; no Corpus prompt choreography or frontend dispatch chain. | RouteDeck agent driver/runtime |

No new RouteDeck primitive is required. Binary upload remains outside RouteDeck because RouteDeck operations accept typed JSON, while every product state transition after staging remains a legal compiled operation.

## Corpus file plan

- Backend: staged attachment repository/service, upload HTTP, accepted Source state, explicit processing operation and bindings.
- Frontend: stage-only Source client and Composer path, Source Hub staged-file confirmation, explicit add/analyze controls.
- Studio/manifest: synchronize the accepted staged-file behavior and compiled mappings.
- Evidence: focused persistence/concurrency/HTTP/RouteDeck tests, then real chat-only, surface-only, and hybrid product runs with uncut normal-speed video.

## Guided Source Hub and API Source mapping

| Studio concept | Existing RouteDeck contract | Corpus implementation |
| --- | --- | --- |
| Source Hub inventory and next step | Existing stable Surface on the existing `sources.home` Node | `SourceHubSurface` lists sources and setup progress only; it dispatches navigation into API Source |
| Add or open an API Source | Existing navigation Operation, Transition, public surface effects, and session-bound route | `sources.open_api_creation` and `sources.open_api_source` navigate to `sources.api` and project intake or exact selected-source identity |
| New API intake | Existing child Node, Transition, and stable Surface contracts | `sources.api_intake` owns only staged-file acceptance and explicit return actions; it cannot analyze, curate, configure, or attach |
| Selected API Source workflow | Existing child Node and stable Surface contracts | `sources.api` owns the exact accepted/selected Source, explicit analysis, graph, curation, connection, and attachment controls; it cannot accept another staged definition |
| Accept and continue | Existing supervised Operation outcome transition plus public surface effects | `sources.accept_staged_api` moves `sources.api_intake -> sources.api` and projects the exact accepted Source identity |
| Maximize while retaining chat | No RouteDeck state change; presentation is outside the NavGraph | Corpus Agent shell switches the same mounted surface into a chat-left/surface-right layout |
| Complete semantic graph | RouteDeck only legalizes selection actions; graph rendering is product data and UI | Corpus serves the complete persisted ToolRouter graph and reuses Source Hub Runtime's pinned Sigma accumulated-graph plus Cytoscape operation-neighborhood renderers |
| Recorded graph construction replay | Existing state-selection Operation remains sufficient for product state; local playback is read-only presentation | Corpus exposes exact persisted `graph_trace.jsonl` events and replays them without sampling or live-stream claims |

No RouteDeck repository change is required. Product text, intake/detail legality, graph projection, next-step guidance, and maximized layout are Corpus-owned; RouteDeck continues to own node legality, transition state, operation supervision, projection, and session persistence.

### Graph renderer dependency decision

- Selected by the owner: the already-proven Source Hub Runtime dual renderer. Corpus pins `sigma@3.0.3`, `graphology@0.26.0`, `graphology-components@1.5.4`, `graphology-layout-forceatlas2@0.10.1`, and `cytoscape@3.33.1`. All are MIT-licensed. Sigma owns the complete accumulated WebGL graph; Cytoscape owns one exact operation neighborhood; Corpus layers the persisted ToolRouter construction replay over both without changing graph truth.
- Considered: Sigma-only visibility filtering. It preserved every node in memory but did not reuse the proven Source Hub neighborhood renderer and therefore did not meet the accepted behavior.
- Considered: existing `@xyflow/react@12.11.2`. It is a node-editor abstraction rather than the proven semantic-network renderer and would not satisfy the requested ToolRouter/Source Hub visualizer reuse.
- Verified reference: `D:\Dev\AI Projects\source-hub-runtime\frontend`, command `npm run build`, completed successfully on 2026-08-10 with Cytoscape 3.33.1 and Sigma 3.0.3. Corpus keeps the integration behind `SemanticGraphVisualizer.tsx`; Source Hub Runtime and ToolRouter remain unchanged.

## Public language

Use `API definition`, `API version`, `analyze operations`, and `review API changes`. Internal implementation may retain legacy contract-revision class and operation identifiers until a separate migration is justified, but those terms must not appear as owner-facing product copy.

## Guided selected-Agent continuation mapping

The accepted horizontal lifecycle already exists, but the owner must not have to
reverse-navigate through the Agent hub after every completed prerequisite. The
continuation remains explicit navigation: it does not build, run, evaluate,
deploy, or inspect merely because the next surface opens.

| Studio intent | Existing RouteDeck contract | Corpus implementation |
| --- | --- | --- |
| Continue an accepted Designer build request into Builds | Existing `agents.open_builds` Navigation Operation, exact selected-Agent entity binding, and `designer.home -> builder.home` Transition | Designer exposes `Continue to Builds` only after the durable build request exists |
| Continue a ready immutable build into Sandbox | Existing `agents.open_sandbox` Navigation Operation and `builder.home -> sandbox.home` Transition | Builder exposes `Continue to Sandbox` only when a ready build exists |
| Continue a successful private trial into Evaluation | Existing `agents.open_evaluation` Navigation Operation and `sandbox.home -> evaluation.home` Transition | Sandbox exposes `Continue to Evaluation` only when a successful run exists |
| Continue eligible evaluation evidence into hosted delivery | Existing `agents.open_channels` Navigation Operation and `evaluation.home -> channels.home` Transition | Evaluation exposes `Continue to Channels` only when the exact build is eligible |
| Continue an active hosted deployment into owner Operations | Existing `agents.open_operations` Navigation Operation and `channels.home -> operations.home` Transition | Channels exposes `View Operations` only after an active deployment exists |

No RouteDeck repository change is required. The existing Agent-area navigation
handlers already project the exact selected Agent into the target surface. Corpus
only makes those already-compiled operations legal and visible at the preceding
stage, while RouteDeck continues to own legality, entity binding, transition,
projection, and session persistence.

## File-first Workspace task routing mapping

The approved `Set up an agent from an attached API definition` Studio story
requires the staged definition to become an identifiable Source and begin
analysis before Corpus asks which Agent to use or create. At `workspace.home`,
both destination operations are legal, so generic destination descriptions did
not express that prerequisite strongly enough to the model.

| Studio intent | Existing RouteDeck contract | Corpus implementation |
| --- | --- | --- |
| Start an authorized file-first Agent setup | Existing `workspace.open_sources` Navigation operation and `workspace.home -> sources.home` transition | Workspace feature policy and operation description make Sources the first destination while the attached definition is still staged |
| Manage Agents directly | Existing `workspace.open_agents` Navigation operation and `workspace.home -> agents.home` transition | Operation description keeps direct Agent inventory/configuration available for explicit Agent work and after the file prerequisite has begun |
| Continue the same owner request | Existing conversation state, legal-operation projection, and serial multi-operation agent loop | Corpus preserves the staged attachment and current request; Sources owns acceptance/analysis and Agents owns later choice/creation/attachment |

No new guard, automatic dispatch, prompt-specific branch, or RouteDeck primitive
was added. The model still chooses among current legal operations from ordinary
owner language; the semantic distinction comes from the accepted Studio story,
the synchronized Workspace feature policy, and the compiled operation
descriptions.
