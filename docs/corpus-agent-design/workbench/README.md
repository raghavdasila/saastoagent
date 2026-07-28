# Corpus Agent Design Workbench

This is a local prototype workspace for iterating on the Corpus feature design
before implementation. Slice 1 currently contains the **Workspace** and
**Agents** features. Its ordinary content is a labeled design seed, not product
data or an implementation claim; only stories explicitly described as an
implementation-backed baseline carry that narrower meaning.

Workspace also contains seven approved owner-authentication stories copied
from the currently implemented and tested Corpus behavior: registration and
guest-session adoption, sign-in and resume, sign-out, reset request, password
change, verification resend, and verification confirmation. Authentication is
Workspace-owned infrastructure rather than another launch feature, and users
of deployed agents remain outside this owner identity boundary. These approved
stories lock the current-product baseline only; **Reopen draft** remains the
explicit way to reconsider one.

Each story keeps the review unit deliberately small:

- an editable title and one user-story narrative;
- editable mock conversation between Corpus and the owner;
- a static mock surface rendered in a no-permissions iframe; and
- explicit approve or reasoned reject controls.

Use **Add story** in the selected feature's story list to create and immediately
select a blank story. Desktop keeps the story editor and surface preview in
separate scroll regions inside one viewport; mobile keeps page chrome fixed and
scrolls the working content region.

The workbench defaults to the operating-system color preference and provides a
header toggle between light and slate dark themes. The explicit choice is saved
under `corpus.feature-design-workbench.theme`. Static mock surfaces follow the
same choice through their own `prefers-color-scheme` styles; this does not add
permissions to the iframe sandbox.

Approval and rejection apply to one story. Reviewed stories are locked until
they are reopened. Edits and review state are saved to versioned browser local
storage. Version 3 adds the locked authentication baseline. Existing version 2
stories are retained and only missing seed stories are appended; version 1
five-field stories are first migrated into the single narrative field without
discarding content. Invalid saved data stops on a visible reset screen instead
of silently falling back to the seed.

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
`public/mock-surfaces`. Each document contains only the surface under review,
not the Corpus shell; skeleton elements can provide lightweight surface context.
The authentication stories reuse one script-free static document whose URL
fragment selects the relevant registration, sign-in, sign-out, reset, or
verification surface.
They render through `<iframe sandbox="">`, which grants no script, same-origin,
form, popup, download, or navigation permission. If a future mock genuinely
needs interaction, add only the specific sandbox token needed and document that
decision; do not add `allow-same-origin` to these local surface mocks.
