# 2026-05-25 Agent Orchestration And RouteDeck v2 Validation

## Scope

Validation for the current SaaStoAgent worktree after:

- agent-owned API orchestration
- execution-frame variable state
- policy-gap learning
- RouteDeck v2 navigation
- Learning detail surfaces
- graph-owned instructions save
- RouteDeck/Corpus boundary hardening
- RouteDeck usage documentation

## Commands

```powershell
cd D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1
python -m pytest backend/tests -q
```

Result: `171 passed`.

```powershell
cd D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\frontend
npm run type-check
```

Result: passed.

```powershell
cd D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\routedeck\react
npm test
```

Result: `13 passed`.

```powershell
cd D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\routedeck
python -m pytest tests -q
```

Result: `17 passed`.

```powershell
cd D:\Dev\AI Projects\agent-core
git diff --check
```

Result: passed.

## Boundary Scans

Checked current worktree for:

- direct Learning approve/reject REST mutation from Corpus UI
- direct instructions save REST mutation from Corpus UI
- public `/api/routedeck/*` route declarations
- product-visible "RouteDeck node" wording
- SaaStoAgent/Corpus/Medusa product literals in RouteDeck production source

Result: no active production matches for the targeted leaks.

## Browser Validation Status

Browser/Medusa E2E was not rerun after the latest changes.

Previous browser screenshots existed for:

- open deployed chat
- list products
- ask to buy Medusa T-Shirt
- add L size to cart

Those screenshots showed the owner-policy-needed state, not a completed checkout.

## Risk Notes

- Current validation is strong at unit/contract/type level.
- Full checkout remains unvalidated and incomplete.
- The next meaningful validation is `npm run e2e:medusa:docker`.
- Do not claim product E2E is green until browser validation passes on the current worktree.
