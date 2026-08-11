# Corpus final-integration current-state audit

Date: 2026-08-10

Updated: 2026-08-11

Authority:

- `docs/corpus-agent-design/final-integration-tasks-and-process.md`
- `docs/corpus-agent-design/feature-behavior-notes.md`
- accepted Design Studio state
- `contracts/corpus-agent-design-routedeck-manifest.json`

This is a current-state integration audit, not a completion claim. It separates
working implementation, integrated product behavior, surface quality, and
evidence. The owner-authored Behavior Notes remain unchanged.

## Current product evidence inspected

The local Corpus runtime was healthy at `http://127.0.0.1:5199`, with backend
readiness at `http://127.0.0.1:8099/readyz` and local Medusa health at
`http://127.0.0.1:9100/health`.

Current screenshots are retained under
`.runtime/audits/20260810-final-integration-current-ui/`:

1. `01-lounge-shell.png` — docked chat and surface shell;
2. `02-maximized-chat-surface.png` — wide-screen split chat/surface layout;
3. `03-live-navgraph.png` — docked RouteDeck NavGraph inspector;
4. `04-fullscreen-navgraph.png` — fullscreen RouteDeck NavGraph inspector.

The screenshots prove that the shared shell, maximized split, and real generic
RouteDeck inspector exist. They also expose the current graph-density and
presentation problems. They do not prove authenticated feature flows.

## Cross-cutting integration findings

### Working and worth preserving

- Corpus has one coherent application shell with conversation history,
  feature navigation, surface dock, composer, and a resizable NavGraph panel.
- The surface dock already supports a useful wide-screen split with chat on
  the left and the active surface on the right.
- RouteDeck already exports a real React Flow `NavGraphInspector` with focused
  node detail, surfaces, legal operations, transitions, current/reachable
  state, zoom, fit, and fullscreen support.
- Builder persists both the immutable compiled NavGraph and the exact generated
  RouteDeck frontend contract. The information needed for a real renderer is
  already present.
- Designer, Builder, and Sandbox now share one real RouteDeck React Flow
  presentation over the same immutable topology identity. A current accepted
  three-node Designer topology compiled into a three-node/six-transition build
  and drove the Sandbox runtime onto its exact `Product types` capability node.
- Designer, Builder, Sandbox, Evaluation, Channels/Deployment, public
  delivery, and Operations have independent backend/frontend modules and exact
  lineage contracts. Integration should reuse them rather than replace them.

### Material integration failures

- The generic docked NavGraph is real but too narrow to be legible at its
  default width. Fullscreen fits the entire 20-node sitemap into a small center
  cluster with large unused space, weakening labels and node inspection.
- The public deployed Agent is a separate minimal form/list page. It does not
  reuse Corpus's proven conversation hierarchy, composer, status treatment,
  responsive shell, or message presentation. RouteDeck powers its runtime but
  the product does not communicate that quality.
- Feature surfaces use inconsistent information hierarchy and CSS maturity.
  Strong shared shell and Source graph work coexist with textarea-heavy or raw
  list/card screens in later features.
- The manifest still marks every feature after Lounge as partial even where a
  baseline runtime is implemented. Current gaps mix missing behavior, missing
  integration, missing UX, and missing external evidence; these categories
  must be tracked independently.

## Feature-by-feature status

| Feature | Existing working truth | Integration or behavior gap | Current judgment |
| --- | --- | --- | --- |
| 0. Lounge | Public help and account surfaces exist in the shared Corpus shell. Manifest mapping is complete. | Retain current shell quality and verify chat/surface continuity after shared changes. | Integrated baseline; preserve. |
| 1. Workspace | Authenticated home, overview, and feature-entry operations exist. | Manifest leaves signed-in product help, arbitrary task continuation, and sign-out-to-Lounge unmapped. Cross-feature continuation must be proven without spoonfed navigation language. | Partial integration. |
| 2. Agents | Agent identity/version, exact Source attachments, archive/delete review services, build lineage, and selected-Agent navigation exist. | Edit behavior is incomplete; manifest still leaves archive/delete, selected-Agent operations, and historical build references unmapped or unproven. The selected-Agent hub must guide the complete downstream lifecycle. | Strong module, incomplete product behavior. |
| 2.5. Selected-Agent operations | Navigation to Designer, Builds, Sandbox, Evaluation, Channels, and Operations exists with private Agent binding. | The hub must explain prerequisites and current lineage rather than acting as a menu of disconnected destinations. Context must survive every return/handoff. | Present, needs integrated guidance. |
| 3. Source Hub | Source inventory, staged API attachment, processing state, Markdown description lifecycle, dependency-aware reviewed delete, semantic evidence, connection profiles, curation, and Agent handoff code exist. | Existing-source selection for an Agent remains Agents-owned. Same-named Sources are difficult to distinguish in the inventory, and the newly implemented description/delete behavior still needs replacement per-behavior chat-only, surface-only, and hybrid proof. | Integrated runtime path; hierarchy and evidence incomplete. |
| 4. API Source / Collection | Real ToolRouter processing, complete persisted semantic graph, exact 534-event construction replay, protected profile, explicit curation, planning, and routed execution exist. Attachment/acceptance remains separate from explicit analysis. | The combined compiled Sources feature spans the separately authored Source Hub and API Source design boundaries, so the strict feature-level manifest mapping remains partial. Standard API-definition language and same-task Agent handoff must remain consistent in every state. | Architecturally strong and visibly integrated; strict mapping/evidence boundary remains partial. |
| 5. Agent Designer | Immutable proposals/customizations, required approval, exact Source/curation snapshot, shared topology hash, build request, and a real proposed RouteDeck topology are visible. The current accepted design has `Agent home`, `Product tags`, and `Product types` areas with exact policies, surfaces, navigation, and curated tools. | Goals/responsibilities and behavior editing still need a more guided miniature-Studio interaction; raw identifiers remain available as owner diagnostics but must not dominate the task. | Topology integration proven; design-authoring UX depth remains. |
| 6. Agent Builder | Exact accepted-design assembly, immutable build, model/runtime/source/profile/curation bindings, persisted compiled NavGraph/frontend contract, running/stopped/delete controls, and explicit pause-unavailable truth exist. The current build renders the real three-node/six-transition RouteDeck application. | Durable pause, background lifecycle depth, explicit retry, deletion usability among historical builds, and automatic ToolRouter evalset generation remain gaps. | Topology/presentation integrated; lifecycle depth incomplete. |
| 7. Sandbox | Exact build execution, isolated sessions/runs, visible ToolRouter clarification/evidence, and real capability-node traversal now work for the current multi-area build. Maximized desktop and mobile layouts preserve chat plus the active surface. | Owner diagnostics need stronger hierarchy, build selection needs human-readable lineage, and chat/surface/hybrid evidence must still retain one run and clarification lineage. | Real multi-area runtime path proven; lifecycle/UX depth remains. |
| 8. Evaluation | Immutable interaction-derived cases, run evidence, reviewer, metrics, and deployment eligibility exist. | ToolRouter evalset generation and case edit/remove are missing or pending. Surface is list-oriented and needs clearer set/case/run/eligibility hierarchy plus durable async status and explicit retry. | Baseline works; Behavior Note CRUD/generation incomplete. |
| 9. Channels | Hosted Web channel identity, enable/disable state, and exact active deployment binding exist. | Custom-domain linkage remains explicitly exploratory. Channel availability must be clearly separated from deployment and public session state. | Launch channel present; management depth incomplete. |
| 10. Deployment | Reviewed eligible-build deployment, active version, public URL, restart-safe binding, and public sessions exist. | Rollback, availability changes, durable async progress/failure, and explicit retry require completion and proof. Public Agent UI is materially below Corpus's existing shell quality. | Runtime baseline works; public experience and lifecycle incomplete. |
| 11. Operations | Owner-only deployed interactions, redacted RouteDeck/ToolRouter/API evidence, exact build NavGraph, and promotion operation exist. | Current UI is a raw stacked evidence dump and reuses the weak Builder graph. Promotion, filtering/selection, readable decision chronology, and linkage back to Evaluation need product-level proof. | Data and operations exist; usability and evidence depth incomplete. |

## 2026-08-11 Source and Workspace handoff checkpoint

The rebuilt local product was exercised through the in-app Browser at
`http://127.0.0.1:5199/`:

1. authenticated Workspace Home rendered the real overview as `2` Agents and
   `3` API Sources, all `3` ready;
2. the direct `Open Sources` action rendered the same three-source inventory
   and one explicit next step;
3. opening that exact next Source retained its selected immutable API version
   in a six-stage guided workspace;
4. the Graph stage rendered the complete persisted ToolRouter graph (`860`
   nodes, `1363` edges) and all `534` recorded construction events; and
5. maximizing retained chat on the left and the active Source workspace on the
   right. Browser error and warning logs were empty.

Accepted current-run screenshots are outside the repository at:

- `C:/Users/ragha/.codex/visualizations/2026/08/11/corpus-final-integration-audit/01-workspace-home.jpg`
- `C:/Users/ragha/.codex/visualizations/2026/08/11/corpus-final-integration-audit/02-source-guided-workspace.jpg`

This is a real rendered integration checkpoint, not final per-behavior
chat-only/surface-only/hybrid evidence. It also exposed two UX risks: the three
same-named Source records rely on file/date metadata for distinction, and an
older Lounge assistant message remains visible beside the surface-only Source
task until the next chat turn.

## 2026-08-11 Designer, Builder, and Sandbox handoff checkpoint

The same authenticated local product was exercised through the in-app Browser
without a fixture or recorder-owned runtime path:

1. Designer revision `4` rendered and accepted a three-area topology with hash
   `aba678482db68af3…`: `Agent home`, `Product tags`, and `Product types`;
2. Builder assembled immutable build
   `6ab6f8d3-778a-40ed-8b87-29eb6f72a1e3` with runtime hash
   `e361c774b3986611…`, preserving the same topology as three nodes and six
   transitions;
3. the build entered `Running`, and Builder retained `Continue to Sandbox`
   even while another historical build was also running;
4. Sandbox selected that exact build and executed the safe owner request
   `List all product types.` through one real `GetProductTypes` API call;
5. run `ad3c9830-cee2-454a-bff8-bc0ba321f75b` finished `succeeded`, and its
   RouteDeck session `6ae35904-b41c-4150-a555-895ba80a958b` ended on exact
   capability node `agent_runtime.area.64dbb3a2206d1c26e040`, projecting the
   `Product types` surface and `Return to agent home` action; and
6. the visible ToolRouter trace retained the ranked candidates, selected
   `GetProductTypes`, supervised HTTP `200`, and final run completion.

Rendered audit exposed and fixed a shared-shell mobile defect: programmatic
focus could retain hidden horizontal surface scroll, and long immutable IDs
could enlarge Sandbox grid children. The shell now resets both scroll axes on
node/layout changes, clips horizontal overflow, and Sandbox runtime identities
wrap inside the available width. Fresh 390x844 inspection shows complete left
edges, independently scrollable chat and surface panes, and zero browser
warnings or errors.

Accepted current-run evidence is retained at:

- `audits/2026-08-11-final-integration-runtime/05-designer-navgraph-corrected.png`
- `audits/2026-08-11-final-integration-runtime/09-builder-multi-area-navgraph-map.png`
- `audits/2026-08-11-final-integration-runtime/10-sandbox-multi-area-runtime.jpg`
- `audits/2026-08-11-final-integration-runtime/11-sandbox-maximized-runtime.jpg`
- `audits/2026-08-11-final-integration-runtime/12-sandbox-mobile-maximized.jpg`
- `audits/2026-08-11-final-integration-runtime/13-sandbox-mobile-runtime.jpg`

Focused evidence is green: 14 Designer/Builder/Sandbox backend tests, the
Designer/Build/deployed presentation set, the four Builder lifecycle tests, the
new shared-shell horizontal-scroll regression, and strict frontend typecheck.
This closes the current topology/runtime handoff only; it does not claim the
remaining Builder lifecycle, Evaluation, delivery, Operations, or per-mode
evidence tasks.

## First horizontal implementation boundary

The highest-leverage first slice is the shared immutable Agent NavGraph and
deployed UI presentation boundary:

1. reuse RouteDeck's public `NavGraphInspector` for exact persisted build
   frontend contracts;
2. make one product-owned immutable-Agent graph shell reusable by Builder,
   Sandbox/Evaluation where appropriate, and owner-only Operations evidence;
3. preserve exact hash, lineage, capability/tool/safety/review detail around the
   real graph rather than hiding it;
4. improve graph sizing/focus so fullscreen uses available space and docked
   views remain legible;
5. separately bring the public Agent onto Corpus's proven chat presentation and
   responsive primitives without exposing owner-only NavGraph or execution
   diagnostics.

No RouteDeck primitive gap is currently proven for the immutable build graph:
RouteDeck already exports the required inspector and Builder already persists
its exact frontend contract. This slice is Corpus-owned unless live
implementation proves a narrower upstream styling or sizing contract is
required.

## Evidence boundary

Existing horizontal recordings prove that a baseline path can complete. They
do not close the current final-integration tasks because presence in a video
does not establish intuitive surfaces, complete Behavior Note operations, or
reuse of the strongest existing UI. New evidence will be recorded only after
the affected product slices work end to end.
