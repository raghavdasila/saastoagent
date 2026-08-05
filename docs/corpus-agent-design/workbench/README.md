# RouteDeck Agent Design Studio

The implementation destinations for feature prompts and every AgentPolicy
scope are defined in
[`../routedeck-design-mapping.md`](../routedeck-design-mapping.md).

This is the local **RouteDeck Agent Design Studio**, with **Corpus** as the
active project. It is a prototype workspace for iterating on Corpus feature
design before implementation. The current seed covers behavior-note sections 0–4:
**Lounge**, **Workspace**, **Agents**, **Source Hub**, and **API Source**. Its
ordinary content is a labeled design seed, not product data or an implementation
claim; only stories explicitly described as an implementation-backed baseline
carry that narrower meaning.

Codex drives the behavior inventory, drafts one atomic behavior and its supporting
artifacts at a time, and advances after review. The user reviews, text-edits,
corrects, and explicitly approves or rejects each behavior. The preview presents
the same task as two separate interaction paths: structured surface and chat.

**Lounge** is the unauthenticated product home for general product help and
account entry or recovery. Its eight behaviors now carry complete, explicit
operation contracts and are drafts awaiting renewed review after that design
change. **Workspace** is the authenticated owner home; its sign-out story
is also implementation-backed and approved. **Agents** owns agent identity,
configuration overview, source handoffs, and lifecycle actions without a
product-level draft-agent concept. **Source Hub** owns source inventory and the
only launch entry into **API Source**, which owns OpenAPI intake, connection
configuration, ToolRouter processing, graph inspection and replay, operation
curation, and explicit recovery. Approved stories lock current-product behavior
only; **Reopen draft** remains the explicit way to reconsider one.

Each behavior keeps the review unit deliberately small:

- editable user intent and agent intent guidance;
- an editable expected-behavior statement containing the observable response,
  material constraints, and completion state without repeating either intent;
- a read-only chat-path example for the same task;
- a provisional Node design for the behavior;
- editable Capabilities, Surfaces, and Operations with scoped AgentPolicies;
- optional SuggestedActions kept separate from Operations and bound to one of them;
- behavior-level single-turn eval definitions with semantic criteria, optional
  reference responses, coverage categories, and product-state expectations;
- an optional static surface rendered separately from the chat path in a tightly sandboxed iframe; and
- deterministic completeness diagnostics and explicit approve or reasoned reject controls.

The dedicated **Feature guidance** and **Feature rules** destinations separate
product framing from feature-scoped `AgentPolicy` instructions. Every behavior is the human-readable design
unit for one provisional feature Node and owns its Node, Capability, Surface,
and Operation AgentPolicies. The studio neither asks for nor displays RouteDeck
declaration IDs, and it does not claim to compute effective runtime policy.
Declaration references and resolution belong to complete RouteDeck extraction.

Operations are first-class design objects with a name and intended effect. A
compact inventory exposes contract status and opens one focused editor at a time. The
effect states the product result, state transition, navigation outcome, or
observed response produced by the Operation; it does not restate the
SuggestedAction that exposes it. Inputs and prerequisites, observable outcomes,
safety/review, and failure/recovery are required before approval. A
SuggestedAction is a separate optional chat invitation and must reference a
defined Operation. Surface affordances remain part of the product design;
technical runtime bindings remain part of later extraction.

Each feature also has a **Conversation evals** destination. It authors adaptive
tester contracts through a compact scenario inventory and one focused editor at
a time. Scenarios define an opening message, hidden goal, bounded facts,
disclosure rules, bypass tactics, semantic criteria, product-state checkpoints,
and stop conditions; they do not script Corpus's clarification order. Lounge
contains eight behavior-eval sets and eight feature conversation scenarios
covering product help, task redirection, authentication routing, account
enumeration, credentials, Workspace privacy, indirect bypasses, and unsupported
product claims.

Evaluation definitions are design inputs, not passing evidence. Run the Lounge
conversation pack against the live local Corpus backend with:

```powershell
.\.venv\Scripts\python.exe scripts\run_lounge_evaluations.py
```

The Corpus-owned runner uses real HTTP conversations, a separately invoked
adaptive tester and structured judge, and deterministic product-state checks.
It writes immutable artifacts below `.runtime/evaluations/`. The Studio reads
the external latest-result index and shows **Passed**, **Failed**, **Stale**, or
**Not run** without copying evidence into `design-state.json`. Level-3
backend-state product benchmarks remain explicitly deferred.

Use **Add behavior** in the selected feature's behavior list to create and immediately
select a blank behavior. Draft behaviors can be deleted through an inline confirmation;
reviewed behaviors must be reopened before they can be deleted. Desktop uses a
review-first studio shell: project navigation, a structured behavior document,
and a tabbed review pane for Surface, Chat, Completeness, and scoped Rules.
Narrow layouts switch between **Design** and **Preview & review** instead of
compressing both panes. Mobile also collapses the project navigator into an
overlay rail and keeps the working region free of document-level horizontal overflow.

The shell, navigation, editor sections, controls, and state presentation are
modular. Product/project copy lives in `src/workbench/studioConfig.ts`; the
feature list is derived directly from design-state data and needs no
per-feature presentation configuration. Shared light/dark colors,
geometry, spacing, motion, and semantic aliases live in
`src/styles/tokens.css`; shell and responsive layout rules live in
`src/styles/studio.css`. Repeated editor regions use the shared
`StudioSection` primitive instead of duplicating layout markup.

This workbench covers feature behavior and provisional Node design. Complete
Navgraph mapping—including routes, transitions, providers, guards, bindings,
and declaration identifiers—belongs to the later extraction phase after the
relevant behavior has been accepted and extraction has been explicitly
authorized.

The studio defaults to the operating-system color preference and provides a
header toggle between light and graphite-dark themes. The explicit choice is saved
under `routedeck.agent-design-studio.theme`. Static mock surfaces follow the
same choice through their own `prefers-color-scheme` styles; this does not add
permissions to the iframe sandbox.

Approval and rejection apply to one behavior. Reviewed behaviors are locked until
they are reopened. Approval is unavailable while deterministic blocking issues
remain. The diagnostics validate required design text, operation contracts,
evaluation coverage, product-design references, and scoped rules; they do not
guess semantic contradictions or treat **Not run** as a design blocker. The
complete design state is automatically saved
to `design-state.json` in this directory after each edit; the Vite development
server owns the local read/write endpoint and uses an atomic file replacement.
**Export JSON** downloads a formatted snapshot of the current in-memory design
as `corpus-agent-design.json`; it does not replace or bypass autosave. Browser
local storage is used only for the theme preference. Invalid file data
stops on a visible replacement screen instead of silently using another source.
User intent records the meaning
Corpus should recognize; agent intent records the outcome Corpus is responsible
for producing. These are design guidance, not RouteDeck declarations or runtime
intent state.
## Run locally

From the repository root:

```powershell
pnpm --dir docs/corpus-agent-design/workbench install
pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort
```

Open `http://127.0.0.1:8782/` locally, or use the host machine's LAN address on
port `8782` from another device on the same WLAN.

Validation commands:

```powershell
pnpm --dir docs/corpus-agent-design/workbench test
pnpm --dir docs/corpus-agent-design/workbench typecheck
pnpm --dir docs/corpus-agent-design/workbench build
```

## UI and surface boundary

The workbench pins the repository's existing shadcn/Radix-Nova stack at
`shadcn@4.13.1` (MIT) with React, Vite, Tailwind CSS, and Radix UI. The copied
shadcn primitives remain local under `src/components/ui`; studio behavior is
kept under `src/workbench`, and the centralized visual system is under
`src/styles`.

Before integration, the official shadcn Vite flow was run in a temporary local
app with the same pinned version, Button, Textarea, Separator, and Tooltip; its
production build passed and the reference page was exercised at
`http://127.0.0.1:4180/`.

Mock surfaces are separate static HTML documents under
`public/mock-surfaces`. Each document contains only the inline surface under
review, not the Corpus shell, a modal, a dialog, or the surrounding chat. The
workbench places the iframe immediately above the SuggestedAction row and composer so the
surface is reviewed in its intended chat position. An Operation-only behavior has
no surface document.
The authentication stories reuse one static document whose URL
fragment selects the relevant registration, sign-in, sign-out, reset, or
verification surface.
Surfaces grow to their reported content height until they reach half the height
of the chat preview; taller content scrolls inside the surface. They render
through `<iframe sandbox="allow-scripts">`. The only script reports intrinsic
height to the parent, whose listener verifies the sending frame. The sandbox
still grants no same-origin, form, popup, download, or navigation permission.
If a future mock genuinely needs interaction, add only the specific sandbox
token needed and document that decision; do not add `allow-same-origin` to
these local surface mocks.
