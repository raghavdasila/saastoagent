# Standalone Source Hub and API Source suite

Status: proven independently; not imported into Corpus

Standalone authority: `D:\Dev\AI Projects\source-hub-runtime`

This document records how the standalone suite relates to the owner-authored Corpus launch baseline. It is a consumption map, not authorization to modify RouteDeck or to replace Corpus's existing generic Sources ownership.

## Launch-feature coverage

The standalone suite does not complete the 11-feature Corpus launch path. It strongly covers API Source, substantially covers Source Hub, and contributes bounded foundations to Evaluation and Operations. Numerically, the 11-feature launch subset has one strong feature, three partial/foundation features and seven absent features. Against all 15 proposed ownership features, it is one strong, three partial/foundation and eleven absent. The number of fully proven Corpus end-to-end launch paths remains zero.

| Corpus launch feature | Standalone coverage | Remaining Corpus responsibility |
| --- | --- | --- |
| Workspace | None | Corpus owner context, navigation and Workspace activity. |
| Agents | None | Agent lifecycle and source attachments. |
| Source Hub | Substantial | Reconcile with Corpus's existing generic source inventory; add real agent-attachment usage and separate Markdown-file upload if that owner behaviour remains required. |
| API Source | Strong | Integrate accepted use cases into Corpus surfaces/operations and Corpus authentication; reconcile the duplicate ToolRouter snapshot. |
| Agent Designer | None | RouteDeck-powered accepted agent design. |
| Agent Builder | None | Versioned runnable Agent Build and isolated execution runtime. |
| Sandbox | None | Run the actual draft agent. Direct standalone API calls are executor evidence, not Sandbox. |
| Evaluation | Partial | ToolRouter source-routing cases exist; Corpus still needs case CRUD, exact Agent Build execution, metrics and eligible/ineligible deployment evidence. |
| Channels | None | Hosted Web channel and binding. |
| Deployment | None | Publish an eligible agent revision. |
| Operations | Primitive only | Execution/processing evidence exists; deployed-agent sessions, public interactions, review and interaction-to-evaluation capture do not. |

The minimum Corpus journey remains incomplete here:

```text
create agent -> upload API -> attach -> design -> build -> Sandbox
             -> evaluate -> deploy Web -> public interaction -> Operations
```

The standalone proof covers only this bounded subpath:

```text
upload OpenAPI schema -> durable ToolRouter processing -> graph/grouping
-> operation ranking/evalset evidence -> configure real API
-> explicit API execution -> response-schema review
-> corrected OpenAPI schema -> ToolRouter reprocessing
```

## Proven standalone capabilities

- owner-isolated source lifecycle and immutable OpenAPI schema revisions;
- durable Huey/SQLite processing with visible failure, explicit retry, recovery and logs;
- pinned ToolRouter ingestion, semantic grouping, complete graph, focused operation neighbourhood, routing evidence and reviewed evalsets;
- encrypted write-only API-key credentials and immutable connection configuration;
- explicitly selected real API connection tests and execution through `api-execution-runtime`;
- response-schema mismatch review and user-approved corrected OpenAPI schema lineage;
- exact `openapi_schema_hash` recorded for routing, evalsets, connection tests and executions;
- real Ory and Medusa evidence, parallel isolated owners, restart persistence and rendered frontend proof.

Exact evidence and commands are owned by the standalone repository:

- `D:\Dev\AI Projects\source-hub-runtime\RUNBOOK.md`
- `D:\Dev\AI Projects\source-hub-runtime\docs\CAPABILITY_COVERAGE.md`
- `D:\Dev\AI Projects\source-hub-runtime\docs\VALIDATION_INDEX.md`
- `D:\Dev\AI Projects\source-hub-runtime\docs\PUBLIC_HTTP_API.md`

## Corpus integration points

| Standalone boundary | Corpus destination | Constraint |
| --- | --- | --- |
| Source lifecycle use cases | `backend/src/corpus/features/sources` | Do not create a second Corpus source inventory. Reconcile behaviours with `SourceService`. |
| `ToolRouterPort` | Existing Corpus API Source `ApiSourceEngine` bridge | Choose one authoritative vendored snapshot and preserve provenance. Never run two ToolRouter engines for one schema revision. |
| `ExecutionPort` | New adapter owned by Corpus API Source/runtime composition | Keep `api-execution-runtime` types inside the adapter. ToolRouter ranks; executor calls HTTP. |
| `CredentialPort` | Corpus-owned credential infrastructure | Credentials stay out of chat, RouteDeck state/history and public DTOs. |
| `JobQueuePort` | Corpus durable-work infrastructure | Huey is an adapter choice, not a domain requirement. |
| `SourceUsagePort` | Corpus Agents/source-binding lookup | Purge must use real agent attachments; do not reuse the standalone no-attachments adapter. |
| Standalone test-user resolver | No destination | Never integrate; Corpus bearer identity already owns authentication. |
| Standalone FastAPI and React host | Corpus HTTP/RouteDeck surfaces | Use as behaviour evidence only, not a second application shell. |

## Required integration flow

```text
Corpus bearer owner
-> Corpus Source Hub/API Source use case
-> exact active OpenAPI schema revision
-> ToolRouter ranking and evidence
-> Agent Build allowed-operation and RouteDeck policy checks
-> Corpus execution adapter
-> api-execution-runtime
-> real API
-> response-schema mismatch/execution evidence
-> Sandbox, Evaluation or Operations consumer
```

The exact source revision and `openapi_schema_hash` must be pinned into every future Agent Build, Sandbox run, evaluation result and deployment that depends on it.

## Adoption gates

Before Corpus source changes:

1. inspect current Corpus Sources/API Source and current RouteDeck contracts read-only;
2. produce the mandatory `isolated use case -> Corpus adapter -> RouteDeck Operation/Node/Surface` mapping;
3. identify duplicate persistence and ToolRouter ownership;
4. decide package import versus hash-pinned copy;
5. define Corpus credential, queue, source-usage and execution adapters;
6. prove the real Corpus owner path through ToolRouter and API execution;
7. prove an actual Agent Build path before claiming Sandbox, Evaluation eligibility, Deployment or Operations coverage.

No RouteDeck change is implied by this document. If a required RouteDeck contract is missing, stop and report the exact upstream gap.
