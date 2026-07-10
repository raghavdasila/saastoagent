# SaaStoAgent v0.1 Standalone Extraction Report

Date: 2026-07-15 (Asia/Calcutta)

History note: source-derived commits retain their exact original timestamps;
extraction-only commits use evidence-derived reconstructed dates and do not
assert that the extraction itself occurred on those dates.

## Boundary

- Standalone repository: `D:\Dev\AI Projects\saastoagent-v0.1`
- Extracted source subtree:
  `agent-lab-powered-projects/saastoagent-v0.1`
- Branch: `main`
- Remotes: none
- GitHub push: not performed
- Original `agent-core` checkout: read-only throughout the extraction

SaaStoAgent now builds from its own repository. Its mature v0 product contract
depends on a pinned compatibility snapshot at
`vendor/routedeck-v0-compat`, sourced from RouteDeck commit
`4b4acff9ff21b674f9d2ab354d8419eba999bad2`. The snapshot is an explicit
dependency, not an error-selected fallback. Its provenance is recorded in
`vendor/routedeck-v0-compat/PROVENANCE.md`.

The sibling standalone RouteDeck repository is required only for the optional
real Medusa acceptance target.

## Preservation and history

- Preserved source snapshot: 10,206 files, 2,018,323,674 bytes
- Source working-state snapshot commit:
  `f1f6665f41324db28099498ac95ff5bcbc15d26d`
- Standalone-boundary commit:
  `18916275b23c0773227fbac1df76fe48d2a2352a`
- Standalone runtime compatibility commit:
  `cfa2755b3e844d96aa2b84ec7b4c16d3cdfd7f20`
- Audited source path commits: 49
- Filtered history commits: 50
- Source-to-standalone commit map: `source-commit-map.tsv`
- Source-ignored artifacts preserved: 9,661 files
- Ignore-parity audit: all 9,661 source-ignored files remain ignored; private
  probes were ignored and `.env.example` remained trackable

`codex_chats_and_memories` is intentionally ignored by Git. Its manifest has
327 items, including 165 raw Codex sessions, totalling 2,674,181,784 bytes. A
fresh full-hash verification found no missing, modified, or unmanifested items.

## Recreated environments

- Python 3.13.5 virtual environment: `.venv`
- Python dependencies: `backend/requirements.txt`
- Node.js 24.3.0
- npm 11.4.2 on the host
- Frontend install: `npm ci` from `package-lock.json` (319 installed
  packages)
- Playwright Chromium 147

Neither `.venv` nor `node_modules` was copied from the source tree. Both are
ignored.

## Standalone compatibility work

- Replaced sibling editable Python and `file:` Node dependencies with the
  pinned in-repository RouteDeck v0 compatibility snapshot.
- Made both Docker images build from this repository alone and added a strict
  `.dockerignore`.
- Removed the runtime `npm install --no-package-lock`; the image installs with
  `npm ci`, then the container builds and previews that locked install.
- Preserved Corpus product lens fields across both Pydantic serialization and
  RouteDeck React normalization.
- Corrected recovery ranking so a POST that recreates a known resource
  collection cannot outrank the intended continuation.
- Updated the real-Medusa browser harness for the extracted RouteDeck credential
  file, current direct deployment-save contract, and semantic live-model copy.
- Updated current README/operator paths. Historical paths remain untouched and
  are classified in `legacy-path-references.md`.
- Applied available patch-level frontend dependency security updates. Final
  `npm audit --audit-level=low` reports zero vulnerabilities.

## Verification

Fresh verification from this repository:

- Backend suite: 273 passed
- Vendored RouteDeck React suite: 24 passed
- Frontend TypeScript check: passed
- Frontend production build: passed, 2,254 modules transformed
- npm audit: zero vulnerabilities
- Docker API health: HTTP 200
- Docker frontend: HTTP 200
- Docker UI contract E2E: passed
- Real Medusa owner/public browser flow: passed

The real flow used the isolated RouteDeck Medusa service, activated one API
connection with 64 tools and 674 router documents, listed and filtered actual
Medusa products, required and recorded explicit owner learning approvals,
added the selected variant to a real cart, selected Standard Shipping, and
placed a Medusa order on checkout turn 10. Public output leak assertions also
passed.

The ignored evidence set is:

```text
frontend/recordings/extraction-real-medusa-rerun7/
```

Its final screenshot is `public-medusa-checkout-done.png`.

## Local runtime smoke

Runtime location: local Windows machine.

```powershell
cd "D:\Dev\AI Projects\saastoagent-v0.1"
docker compose --project-name saastoagent-v01-extracted up --detach --build
```

Smoke-test URLs:

- API health: `http://127.0.0.1:8085/api/health` - HTTP 200
- Owner frontend: `http://127.0.0.1:3007` - HTTP 200
- Real isolated Medusa target: `http://127.0.0.1:9110/health` - HTTP 200
- Host-served OpenAPI schema during E2E: port 9111

The SaaStoAgent Compose project uses its own named Postgres and upload volumes.
The RouteDeck Medusa fixture runs under the separate
`routedeck-medusa-extracted` Compose project. No source-workspace service or
volume was reused.
