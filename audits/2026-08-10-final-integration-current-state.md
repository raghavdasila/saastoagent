# Corpus final-integration current-state audit

Date: 2026-08-10

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
- Designer, Builder, Sandbox, Evaluation, Channels/Deployment, public
  delivery, and Operations have independent backend/frontend modules and exact
  lineage contracts. Integration should reuse them rather than replace them.

### Material integration failures

- Designer and Builder do not reuse RouteDeck's proven NavGraph renderer.
  Designer uses a handmade one-node SVG and Builder uses a separate horizontal
  SVG. Operations embeds that Builder SVG again for deployed evidence. The
  exact persisted RouteDeck frontend contract is therefore discarded at the
  UI boundary.
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
| 3. Source Hub | Source inventory, staged API attachment, processing state, semantic evidence, connection profiles, curation, and Agent handoff code exist. | Source delete and Markdown description behavior are missing. Existing-source selection for an Agent is split across Agents. Current workflow remains dense and terminology still exposes `contract` language. | Major functionality present; UX and CRUD incomplete. |
| 4. API Source / Collection | Real ToolRouter processing, semantic artifacts, protected profile, explicit curation, planning, and routed execution exist. `SemanticGraphVisualizer` uses real persisted graph data. | The manifest still treats API Source as design-only/unimplemented. The product must consistently separate attachment from processing, replace non-standard contract language, and use the proven ToolRouter/source-runtime construction/playback visual language instead of a weaker duplicate. | Architecturally strong, mapping and experience incomplete. |
| 5. Agent Designer | Immutable proposals/customizations, required approval, exact Source/curation snapshot, shared topology hash, and build request exist. | Surface is primarily raw textareas and a handmade one-node SVG. It is not yet the Behavior Notes' intuitive miniature Design Studio connecting semantic groups to features, behaviors, policies, capabilities, surfaces, tools, and the real proposed NavGraph. | Runtime baseline works; core surface underdesigned. |
| 6. Agent Builder | Exact accepted-design assembly, immutable build, model/runtime/source/profile/curation bindings, persisted compiled NavGraph/frontend contract, and isolated runtime exist. | Build renderer discards the persisted frontend contract for a handmade SVG. Start/stop/pause/delete controls, durable background lifecycle, explicit retry, and automatic ToolRouter evalset generation remain gaps. | Runtime foundation strong; lifecycle and presentation incomplete. |
| 7. Sandbox | Exact build execution, isolated sessions/runs, ToolRouter clarification, safe event evidence, and one real operation path exist. | Owner diagnostics need stronger separation and hierarchy. Runtime start/stop/pause semantics inherited from Builder remain incomplete. Chat, surface, and hybrid evidence must retain one run and clarification lineage. | Functional baseline; lifecycle/UX depth incomplete. |
| 8. Evaluation | Immutable interaction-derived cases, run evidence, reviewer, metrics, and deployment eligibility exist. | ToolRouter evalset generation and case edit/remove are missing or pending. Surface is list-oriented and needs clearer set/case/run/eligibility hierarchy plus durable async status and explicit retry. | Baseline works; Behavior Note CRUD/generation incomplete. |
| 9. Channels | Hosted Web channel identity, enable/disable state, and exact active deployment binding exist. | Custom-domain linkage remains explicitly exploratory. Channel availability must be clearly separated from deployment and public session state. | Launch channel present; management depth incomplete. |
| 10. Deployment | Reviewed eligible-build deployment, active version, public URL, restart-safe binding, and public sessions exist. | Rollback, availability changes, durable async progress/failure, and explicit retry require completion and proof. Public Agent UI is materially below Corpus's existing shell quality. | Runtime baseline works; public experience and lifecycle incomplete. |
| 11. Operations | Owner-only deployed interactions, redacted RouteDeck/ToolRouter/API evidence, exact build NavGraph, and promotion operation exist. | Current UI is a raw stacked evidence dump and reuses the weak Builder graph. Promotion, filtering/selection, readable decision chronology, and linkage back to Evaluation need product-level proof. | Data and operations exist; usability and evidence depth incomplete. |

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

