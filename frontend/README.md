# Corpus Frontend

The frontend is the generic permanent chat shell plus Workspace owner surfaces
and the authenticated Sources debug surface.

```text
frontend/
|-- package.json
|-- pnpm-lock.yaml
|-- src/
|   |-- app/                  # generic shell, chat, bootstrap, Navgraph slot
|   |-- features/workspace/   # product surfaces and navigation content
|   |-- features/sources/     # API upload, graph, retrieval, evalset debug UI
|   |-- routedeck/            # client and surface registry
|   |-- main.tsx              # product composition
|   `-- styles.css
`-- src/tests/                # framework and Workspace component contracts
```

The primary chat is not an optional assistant feature. RouteDeck changes the
scope available to the same Corpus agent as the active node changes.

`sources.debug` is intentionally an owner-only experimental workbench. It uses
the neutral `/api/sources/**` response contract to upload a collection, inspect
persisted graph counts, run bounded/full retrieval, and inspect real
generator/reviewer evidence. It does not implement Agent Designer, Sandbox, or
a public deployed channel, and it labels reviewed evalset candidates as not
human gold.

Run from the repository root:

```powershell
.\scripts\run-frontend.ps1
pnpm --dir frontend typecheck
pnpm --dir frontend test
pnpm --dir frontend build
```

Vite proxies `/api`, `/healthz`, and `/readyz` to the local backend at port
8099. The application is served at `http://127.0.0.1:5199/`.
