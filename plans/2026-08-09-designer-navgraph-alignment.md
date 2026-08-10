# Designer to RouteDeck NavGraph Alignment

Date: 2026-08-09

Status: implemented; focused proof green; full regression and browser evidence pending

## Authority

- `critical_prompt.md`: RouteDeck is first-class in Corpus and in every built Agent.
- `docs/corpus-agent-design/feature-behavior-notes.md`: Agent Designer is a
  prepopulated miniature design studio, presents the NavGraph, and produces a
  runnable RouteDeck Agent configuration.
- `docs/corpus-agent-design/workbench/design-state.json`: the approved
  `agent-designer-propose-review-build` behavior.
- `contracts/corpus-agent-design-routedeck-manifest.json`: the existing
  Designer review/build mapping and its Corpus/RouteDeck ownership boundary.

The owner-authored behavior notes remain read only.

## Mapping gate

| Studio concept | Existing RouteDeck contract | Corpus implementation owner |
| --- | --- | --- |
| Prepopulated Agent design | Product-owned immutable design revision | `features/designer` schemas, topology, service and repository |
| Visible proposed NavGraph | RouteDeck `Application`, `Feature`, `Node`, `Capability`, `Surface`, `Operation`, `AgentPolicy` vocabulary | Designer topology projection and frontend blueprint |
| Customize design | `designer.customize` DRAFT operation | Designer service/repository and surface |
| Approve exact design | `designer.approve` with REQUIRED review and accept-time current-design provider | Existing Designer declarations, provider, handler and review surface |
| Build approved design | `designer.request_build`, then `builder.assemble` | Builder input gateway, compiler, runtime gateway and immutable build record |
| Runnable Agent | Compiled RouteDeck `Application` reopened through the SQL-backed RouteDeck runtime | `features/builder/navgraph.py` and `app/agent_routedeck_runtime.py` |

No missing RouteDeck primitive is proven. RouteDeck already owns every generic
contract required here. The correction is Corpus-owned: the Designer preview
and Builder compiler must consume one topology definition instead of presenting
one structure and compiling another.

## Locked implementation boundary

1. Add one pure Designer-owned topology compiler. It validates that every
   accepted tool belongs to exactly one declared capability and emits stable
   capability identities, the exact runtime node/surface layout, and a topology
   hash.
   A single named capability explicitly owns the complete exact tool set;
   multiple capabilities use `Title: operation_id, operation_id` and must form
   an exhaustive, non-overlapping partition. This is the persisted contract,
   not a compatibility fallback.
2. Add the topology projection to every immutable design revision view. No
   secret, profile, credential, base URL, or private RouteDeck session identity
   enters it.
3. Make Builder construct RouteDeck capabilities and accepted-design metadata
   from that exact topology. The runtime remains one executable Agent node; the
   topology truth is its real capability/tool organization, not a decorative
   multi-node lifecycle diagram.
4. Render the exact topology hash, node, capabilities, operations, policies and
   surfaces in Designer. Render the same topology identity in the built
   NavGraph.
5. Fail closed on unknown, duplicate, missing, or multiply assigned tools. Do
   not infer a fallback capability or silently broaden the curation.

## Corpus file plan

- Add `backend/src/corpus/features/designer/topology.py`.
- Modify Designer `schemas.py` and `service.py`.
- Modify Builder `navgraph.py` only to consume the shared topology.
- Modify Designer frontend models/blueprint and Builder NavGraph rendering.
- Add focused backend and frontend correspondence tests.
- Refresh the manifest, architecture component, flow index, test index and
  current context only after the product contract is green.

## Proof

- A proposed revision exposes one stable topology with an exhaustive,
  non-overlapping tool-to-capability mapping.
- The compiled RouteDeck node contains the same capability IDs, titles and
  exact tool membership and records the same topology hash.
- Invalid customized capability membership fails before approval/build.
- Designer and Builder visibly render the same topology identity.
- Existing review, immutable lineage, Source/profile/credential binding,
  runtime isolation, ToolRouter and execution behavior remain unchanged.
