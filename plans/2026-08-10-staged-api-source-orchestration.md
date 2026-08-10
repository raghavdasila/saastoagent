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
| API Source workflow | Existing child Node and stable Surface contracts | New `sources.api` Node and `sources.api` Surface own intake, analysis, graph, curation, connection, and attachment controls |
| Maximize while retaining chat | No RouteDeck state change; presentation is outside the NavGraph | Corpus Agent shell switches the same mounted surface into a chat-left/surface-right layout |
| Complete semantic graph | RouteDeck only legalizes selection actions; graph rendering is product data and UI | Corpus serves the complete persisted ToolRouter graph and renders it with the pinned Sigma/Graphology stack |
| Recorded graph construction replay | Existing state-selection Operation remains sufficient for product state; local playback is read-only presentation | Corpus exposes exact persisted `graph_trace.jsonl` events and replays them without sampling or live-stream claims |

No RouteDeck repository change is required. Product text, graph projection, next-step guidance, and maximized layout are Corpus-owned; RouteDeck continues to own node legality, transition state, operation supervision, projection, and session persistence.

### Graph renderer dependency decision

- Selected: the already-proven ToolRouter stack, pinned exactly to `sigma@3.0.3`, `graphology@0.26.0`, `graphology-components@1.5.4`, and `graphology-layout-forceatlas2@0.10.1`. It is WebGL-oriented for thousands of nodes, MIT-licensed, and already used by both the ToolRouter visualizer and Source Hub Runtime.
- Considered: Source Hub Runtime's Sigma plus Cytoscape dual renderer. It is proven but adds a second rendering lifecycle and dependency without a required interaction that Sigma cannot provide here.
- Considered: existing `@xyflow/react@12.11.2`. It avoids a dependency change but is a node-editor abstraction rather than the proven large semantic-network renderer and would not satisfy the requested ToolRouter visualizer reuse.

## Public language

Use `API definition`, `API version`, `analyze operations`, and `review API changes`. Internal implementation may retain legacy contract-revision class and operation identifiers until a separate migration is justified, but those terms must not appear as owner-facing product copy.
