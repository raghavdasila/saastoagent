# Operator Workbench Baseline Validation

Date: 2026-05-09

## Scope

Validation for the user operating model introduced by ADR-006.

## What To Validate

- First-run flow shows the intent spine, operator status strip, capability rail, next action dock, and collapsed evidence drawer.
- Anonymous landing can still use backend-owned Sign In, Create Account, Learn, and Setup actions.
- Workspace mode shows readiness from workspace stats: missing connection, connected API, generated tools.
- Capability rail states render as Ready, Needs setup, Locked, Running, Needs approval, or Has findings.
- Selecting a capability opens the context lens without replacing the central conversation.
- Context lens uses registry empty/failure/evidence copy for Learn, Setup, Connections, Knowledge, Sessions, Entities, Actions, and QA.
- Evidence drawer expands to show mode, graph stage, run id, session id, graph version, readiness, and autonomy ladder.
- Autonomy ladder is visible but advisory until REST execution approval gates are wired.
- Unknown and future artifact widget types fail closed; new readiness/tool/plan/approval/trace/learning widgets render when emitted.
- Mobile keeps chat primary and treats context/evidence as drawer-style secondary surfaces.
- Product chrome renders `SaaStoAgent`; the operator persona renders exactly as `Corpus`.
- Legacy persisted workspace names such as `SaaStoAgent Operator - It Will Talk To My Saas` render through display cleanup and do not appear in the header.

## Current Evidence

- `python -m compileall backend`: passed.
- `npm run type-check`: passed.
- `npm run build`: passed.

## How To Run Current Checks

```powershell
python -m compileall backend
cd frontend
npm run type-check
npm run build
```

Add repo-native browser tests before treating the workbench behavior as automated coverage.
