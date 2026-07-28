# Corpus Agent Design Workbench

This is a local prototype workspace for iterating on the Corpus feature design
before implementation. Slice 1 currently contains the **Workspace** and
**Agents** features. Its ordinary content is a labeled design seed, not product
data or an implementation claim; only stories explicitly described as an
implementation-backed baseline carry that narrower meaning.

Codex drives the behavior inventory, drafts one atomic story and its supporting
artifacts at a time, and advances after review. The user reviews, text-edits,
corrects, and explicitly approves or rejects each story.

Workspace also contains seven approved owner-authentication stories copied
from the currently implemented and tested Corpus behavior: registration and
guest-session adoption, sign-in and resume, sign-out, reset request, password
change, verification resend, and verification confirmation. Authentication is
Workspace-owned infrastructure rather than another launch feature, and users
of deployed agents remain outside this owner identity boundary. These approved
stories lock the current-product baseline only; **Reopen draft** remains the
explicit way to reconsider one.

Each story keeps the review unit deliberately small:

- editable user intent and agent intent guidance kept distinct from the user story;
- an editable title and one user-story narrative;
- editable mock conversation between Corpus and the owner;
- editable actions kept separate from surfaces;
- an optional static surface rendered inline above the chat composer in a tightly sandboxed iframe; and
- explicit approve or reasoned reject controls.

Use **Add story** in the selected feature's story list to create and immediately
select a blank story. Draft stories can be deleted through an inline confirmation;
reviewed stories must be reopened before they can be deleted. Desktop keeps the
story editor and product preview in separate scroll regions inside one viewport;
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

Approval and rejection apply to one story. Reviewed stories are locked until
they are reopened. Edits and review state are saved to versioned browser local
storage. Version 6 adds lightweight user and agent intent guidance to every
seeded story while preserving version 4 edits. The skipped version 5 key was a
temporary, reverted local experiment and is neither loaded nor treated as a
valid migration source. User intent records the meaning
Corpus should recognize; agent intent records the outcome Corpus is responsible
for producing. These are design guidance, not RouteDeck declarations or runtime
intent state. Version 4 introduced explicit actions and corrected seeded surface
placement without discarding version 3 review text. Version 3 added the locked
authentication baseline; version 2 stories retain their edits and receive only
missing seed stories; version 1 five-field stories are first migrated into the
single narrative field. Invalid saved data stops on a visible reset screen
instead of silently falling back to the seed.

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
