# Horizontal Studio Behavior Mapping Audit

Date: 2026-08-09

Authority: `docs/corpus-agent-design/feature-behavior-notes.md` (read only)

## RouteDeck inspection result

The current sibling RouteDeck contracts already provide the required generic
primitives: `Feature`, `Node`, `Capability`, `AgentPolicy`, stable/detail/review
`Surface` slots, `Operation` source and safety declarations, durable review,
accept-time recheck, transitions, entity providers, and session projection.
The later Corpus modules use those contracts directly.

No RouteDeck source file was changed for this reconciliation.

## Studio to RouteDeck to Corpus map

| Behavior-note area | Explicit Studio behaviors | Existing RouteDeck contract | Corpus owner | Current truth |
| --- | --- | --- | --- | --- |
| Agent Designer | propose; customize; inspect the proposed topology/NavGraph; review and accept; request build | `designer.home`, `designer.authoring`, `designer.home`, `designer.review`, `designer.propose`, `designer.customize`, `designer.approve`, `designer.request_build` | `backend/src/corpus/features/designer/**`, `frontend/src/features/designer/**`, shared `features/builder/navgraph.py` | Implemented; external chat/surface/hybrid proof pending |
| Agent Builder | assemble immutable build; observe durable status and lineage; control run/stop/delete; generate evaluation set | `builder.home`, `builder.assembly`, `builder.home`, `builder.assemble` | `backend/src/corpus/features/builder/**`, `frontend/src/features/builder/**` | Assemble/status/NavGraph implemented; lifecycle controls and generated evalset explicitly unmapped |
| Sandbox | start isolated run; continue same-run clarification; inspect RouteDeck diagnostics; inspect safe operation trace | `sandbox.home`, `sandbox.execution`, `sandbox.home`, `sandbox.start`, `sandbox.resume` | `backend/src/corpus/features/sandbox/**`, `frontend/src/features/builder/Sandbox*` | Implemented; external chat/surface/hybrid proof pending |
| Evaluation | generate ToolRouter evalset; create categorized case; edit/delete case; run exact build; observe durable status/eligibility | `evaluation.home`, `evaluation.manage`, `evaluation.home`, `evaluation.create_case`, `evaluation.run_case` | `backend/src/corpus/features/evaluation/**`, `frontend/src/features/evaluation/**` | Create/run/status implemented; generator and edit/delete explicitly unmapped |
| Channels | create hosted Web channel; view URL/active build; explore custom domain; set availability; use hosted Agent | `channels.home`, `channels.manage`, `channels.home`, `channels.availability_review`, `channels.create`, `channels.set_enabled`; public hosted route remains Corpus delivery UI | `backend/src/corpus/features/channels/**`, `frontend/src/features/delivery/**` | Hosted URL/availability/public Agent implemented; custom domain remains draft exploration |
| Deployment | deploy exact eligible build; observe durable status; roll back | `channels.home`, `channels.manage`, `deployment.deploy_review`, `deployment.rollback_review`, `deployment.deploy`, `deployment.rollback` | `backend/src/corpus/features/deployment/**`, `frontend/src/features/delivery/**` | Implemented; external chat/surface/hybrid proof pending |
| Operations | view deployed interactions; inspect result/API/RouteDeck/NavGraph/ToolRouter evidence; promote to Evaluation | `operations.home`, `operations.inspect`, `operations.home`, `operations.promote_evaluation_case` | `backend/src/corpus/features/operations/**`, `frontend/src/features/operations/**` | Implemented; external chat/surface/hybrid proof pending |

## Corpus correction made by this mapping

Builder/Sandbox and Channels already declared the correct feature-scoped
`AgentPolicy` values but did not activate them through `Feature.policy_refs`.
Corpus now activates those existing policies. This is a Corpus composition
correction, not a new RouteDeck primitive or framework workaround.

## Explicit remaining gaps

- Builder run, stop, and delete controls are not compiled or implemented.
- Build-time ToolRouter evaluation-set generation is not implemented.
- Evaluation case edit/delete and ToolRouter evalset generation are not
  compiled or implemented.
- Custom-domain linking remains a draft exploration item, not a launch claim.
- Dependency-aware Source deletion and ordered graph-construction replay remain
  incomplete and explicitly unmapped.
- Final normal-speed uncut chat-only, surface-only, and hybrid evidence remains
  pending. Credentials stay surface-only.

These gaps remain visible in the Studio and manifest. No fixture, fallback, or
test-only product behavior is used to make them appear complete.
