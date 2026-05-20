# Source Snapshot

Date: 2026-05-20
Source path: `D:\Dev\AI Projects\agent-core\research\openapi_toolrouter_benchmark`
Destination path: `agent-lab-powered-projects/saastoagent-v0.1/integration_prep/openapi_toolrouter/vendor/openapi_toolrouter_benchmark`
Repo branch at copy time: `saastoagent`
Repo HEAD at copy time: `0a0370fa732b69f329139b33536371f68983afe2`

## Copy Policy

The snapshot was copied as a runnable integration-prep fork. It includes source, tests, OpenAPI data, generated artifacts, benchmark results, reports, and notebooks.

Excluded transient files:

- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `*.pyc`

## Divergence Rule

Changes under this prep folder are allowed to diverge from the research benchmark because this slice prepares a SaaStoAgent-facing adapter and sandbox. Research benchmark optimization remains out of scope.

When promoting this router into production SaaStoAgent, compare this snapshot against the current research folder and decide whether to promote the integration package, refresh the vendor snapshot, or extract a shared package.
