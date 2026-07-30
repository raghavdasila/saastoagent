# RouteDeck Agent Design Studio

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
account entry or recovery. Its six implementation-backed authentication stories
are approved. **Workspace** is the authenticated owner home; its sign-out story
is also implementation-backed and approved. **Agents** owns agent identity,
configuration overview, source handoffs, and lifecycle actions without a
product-level draft-agent concept. **Source Hub** owns source inventory and the
only launch entry into **API Source**, which owns OpenAPI intake, connection
configuration, ToolRouter processing, graph inspection and replay, operation
curation, and explicit recovery. These approved stories lock current-product
behavior only; **Reopen draft** remains the explicit way to reconsider one.

Each behavior keeps the review unit deliberately small:

- editable user intent and agent intent guidance;
- an editable expected-behavior statement containing the observable response,
  material constraints, and completion state without repeating either intent;
- a read-only chat-path example for the same task;
- a provisional Node design for the behavior;
- editable Capabilities, Surfaces, and Operations with scoped AgentPolicies;
- optional SuggestedActions kept separate from Operations and bound to one of them;
- an optional static surface rendered separately from the chat path in a tightly sandboxed iframe; and
- explicit approve or reasoned reject controls.

The dedicated **Feature policies** destination contains feature-scoped
`AgentPolicy` instructions only. Every behavior is the human-readable design
unit for one provisional feature Node and owns its Node, Capability, Surface,
and Operation AgentPolicies. The studio neither asks for nor displays RouteDeck
declaration IDs, and it does not claim to compute effective runtime policy.
Declaration references and resolution belong to complete RouteDeck extraction.

Operations are first-class design objects with a name and intended effect. The
effect states the product result, state transition, navigation outcome, or
observed response produced by the Operation; it does not restate the
SuggestedAction that exposes it. Inputs, outcomes, safety/review, and recovery are expandable details. A
SuggestedAction is a separate optional chat invitation and must reference a
defined Operation. Surface affordances and complete runtime contracts remain
part of later extraction.

Use **Add behavior** in the selected feature's behavior list to create and immediately
select a blank behavior. Draft behaviors can be deleted through an inline confirmation;
reviewed behaviors must be reopened before they can be deleted. Desktop uses a
three-region studio shell: project navigation, the Node editor, and the behavior
preview. The preview keeps Surface path above Chat path. Mobile collapses the
project navigator into an overlay rail and keeps the working region free of
document-level horizontal overflow.

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
they are reopened. The complete version 15 design state is automatically saved
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
