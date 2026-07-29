# Corpus Agent Design Workbench

This is a local prototype workspace for iterating on Corpus feature design
before implementation. The current seed covers behavior-note sections 0–4:
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
- editable actions kept separate from surfaces;
- an optional static surface rendered separately from the chat path in a tightly sandboxed iframe; and
- explicit approve or reasoned reject controls.

Each `AgentPolicy` entry contains an editable scope type, a human-readable
"applies to" name, and plain-language guidance. Designers can add, edit, or
remove policies at feature, behavior, node, capability, surface, action,
operation, or another explicitly named design scope. The studio neither seeds
nor displays RouteDeck declaration IDs, and it does not claim to compute an
effective runtime policy. Declaration references and policy resolution belong
to later RouteDeck extraction. Feature-scoped policy has one dedicated sidebar
destination. A behavior contains and displays only policies owned by that
behavior or its contained scopes.

Use **Add behavior** in the selected feature's behavior list to create and immediately
select a blank behavior. Draft behaviors can be deleted through an inline confirmation;
reviewed behaviors must be reopened before they can be deleted. Desktop keeps the
behavior editor and product preview in separate scroll regions inside one viewport;
mobile keeps page chrome fixed and scrolls the working content region.
The studio uses a flat, compact editing treatment: structural dividers replace
nested cards, controls use square geometry, and the mock product preview
retains its own product-specific visual language.

This workbench covers feature behavior design only. Navgraph and other
RouteDeck-candidate mapping belongs to the later extraction phase after the
relevant behavior has been accepted and extraction has been explicitly
authorized.

The workbench defaults to the operating-system color preference and provides a
header toggle between light and slate dark themes. The explicit choice is saved
under `corpus.feature-design-workbench.theme`. Static mock surfaces follow the
same choice through their own `prefers-color-scheme` styles; this does not add
permissions to the iframe sandbox.

Approval and rejection apply to one behavior. Reviewed behaviors are locked until
they are reopened. The complete version 13 design state is automatically saved
to `design-state.json` in this directory after each edit; the Vite development
server owns the local read/write endpoint and uses an atomic file replacement.
Browser local storage is used only for the theme preference. Invalid file data
stops on a visible replacement screen instead of silently using another source.
User intent records the meaning
Corpus should recognize; agent intent records the outcome Corpus is responsible
for producing. These are design guidance, not RouteDeck declarations or runtime
intent state.
## Run locally

From the repository root:

```powershell
pnpm --dir docs/corpus-agent-design/workbench install
pnpm --dir docs/corpus-agent-design/workbench dev --host 127.0.0.1 --port 8782 --strictPort
```

Open `http://127.0.0.1:8782/`.

Validation commands:

```powershell
pnpm --dir docs/corpus-agent-design/workbench test
pnpm --dir docs/corpus-agent-design/workbench typecheck
pnpm --dir docs/corpus-agent-design/workbench build
```

## UI and surface boundary

The workbench pins the repository's existing shadcn/Radix-Nova stack at
`shadcn@4.13.1` (MIT) with React, Vite, Tailwind CSS, and Radix UI. The copied
shadcn primitives remain local under `src/components/ui`; workbench behavior is
kept under `src/workbench`.

Before integration, the official shadcn Vite flow was run in a temporary local
app with the same pinned version, Button, Textarea, Separator, and Tooltip; its
production build passed and the reference page was exercised at
`http://127.0.0.1:4180/`.

Mock surfaces are separate static HTML documents under
`public/mock-surfaces`. Each document contains only the inline surface under
review, not the Corpus shell, a modal, a dialog, or the surrounding chat. The
workbench places the iframe immediately above the action row and composer so the
surface is reviewed in its intended chat position. An action-only behavior has
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
