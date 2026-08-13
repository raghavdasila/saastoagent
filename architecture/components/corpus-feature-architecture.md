# Corpus Feature Architecture

Corpus is a modular monolith. Each RouteDeck feature owns one vertical product
slice, while application composition, authentication, persistence primitives,
and truly generic contracts remain outside feature packages.

![Corpus architecture boundaries](../../docs/assets/corpus-architecture-boundaries.png)

## Feature boundary

A backend feature may contain these roles as its behavior requires:

- `contracts.py`: deliberately public cross-feature references;
- `models.py`: feature-owned persisted or domain truth;
- `schemas.py`: validated request and response serialization;
- `ports.py`: protocols required from another subsystem or external service;
- `service.py`: domain and application rules independent of HTTP and RouteDeck;
- `declarations.py`: RouteDeck Operations and stable identifiers;
- `operations.py`: RouteDeck handlers that call feature services or ports;
- `feature.py`: Nodes, Capabilities, Surfaces, policies, and transitions;
- `bindings.py`: the feature's handler/provider/guard binding factory;
- `http.py`: feature-owned HTTP endpoints when structured data is not a
  RouteDeck projection.

The matching frontend slice uses `models.ts`, `client.ts`, and `store.ts` for
feature domain/query state and actions, plus feature-owned surface components.
RouteDeck store state is never copied into a feature store. RouteDeck continues
to own legal interaction, navigation, pending review, session/projection
versions, and operation recovery.

## Global and shared ownership

- `corpus.composition`, `corpus.bindings`, and `corpus.app` are the composition
  boundary. They may connect concrete subsystems to feature ports.
- `corpus.auth` and `frontend/src/auth` own global identity and owner-session
  state. Lounge uses them but does not own them.
- `corpus.persistence` owns database lifecycle and generic persistence
  primitives. Feature tables and repository behavior remain feature-owned.
- `corpus.jobs` owns the product-neutral durable-job contract, SQLAlchemy job
  truth/lifecycle events, and Huey adapter. A consuming feature owns its task.
- `corpus.credentials` owns opaque owner-scoped references and authenticated
  encrypted payloads. Feature code never owns vault key material.
- `corpus.shared` and `frontend/src/shared` contain only stable, product-neutral
  primitives. They do not import features.
- Cross-feature navigation is injected by the application composition root.
  A direct cross-feature import is allowed only from the target feature's
  `contracts` module.
- Concrete auth, provider, mail, or persistence adapters never enter a feature
  operation handler through an implicit global. They implement an explicit
  feature port and are wired centrally.

## MVC-style relationship

The model is feature-owned server truth. Schemas serialize its public shape.
Services apply domain rules. RouteDeck Operations and feature HTTP endpoints
are controller boundaries. The frontend feature store consumes the endpoint,
owns loading/error/data state, and exposes actions to surfaces. This mirrors
the useful Django/DRF/MobX relationship without duplicating RouteDeck's state
machine in the browser.

## Mechanical enforcement

Run:

```powershell
.\.venv\Scripts\python.exe scripts\check_architecture_boundaries.py
```

The checker currently governs Lounge, Workspace, and Agents. It rejects
feature-to-application imports, concrete auth imports, cross-feature internal
imports, frontend feature-store coupling, and shared-layer dependencies on
product subsystems. Sources remains outside this enforcement set until its
separate implementation lane is reconciled.

## Agent Source attachment boundary

Agents owns `AgentSourceAttachment`, including organization scope, exact
`source_id` plus immutable `source_revision_id`, uniqueness and conflict
semantics. Its persisted row contains identities and attachment time only; it
does not copy the Source display name. The application adapter reads the one
owner-scoped Source inventory and revision chain through `SourceService` and
enriches the attachment display name at read time. If that exact Source
revision is unavailable, the attachment read fails truthfully rather than
returning stale copied data. Agents does not copy Source, job, ToolRouter or
session state. RouteDeck owns the selected-Agent private entity binding and
rotates its legal operation allowlist with each `agents.home` / `sources.home`
transition. Corpus revalidates owner, READY/current revision and the persisted
exact attachment before every attach or open behavior.

The cross-feature seam is explicit: backend Agents imports only the public
`sources.contracts` values used by the handoff, and frontend Agents depends on
the public `SourceInventoryClient` / `SourceView` contract rather than the
Sources client implementation. The compiled Agents Node, attachment
Capability, picker Surface and lifecycle Operations activate the exact
accepted Studio policies. Internal selection and return Operations remain
current RouteDeck contracts without being presented as Studio-authored
product Operations.

## Accepted ecommerce lineage

The current horizontal product path preserves one exact owner-scoped lineage:

```text
Source revision + profile + curation
  -> Agent configuration version + exact Source attachment
  -> accepted Designer revision + topology hash
  -> immutable Builder artifact + compiled RouteDeck Application
  -> Sandbox run + exact-build Evaluation coverage/results
  -> Channel + immutable Deployment releases
  -> public session + redacted interaction evidence
  -> owner-only Operations promotion back into Evaluation
```

No feature resolves “latest” as a substitute for an unavailable historical
identity. Builder and Evaluation surfaces poll their authoritative feature
services while mounted so queued/worker-completed state is visible after
leaving and returning. Source Hub likewise refreshes while mounted, including
when chat creates the first Source after an initially empty inventory.

The assembled Sandbox and deployed Agent retain only bounded response-derived
references needed by the current session: a product variant from the validated
search response and a cart ID from the reviewed cart response. They do not
retain or expose response bodies, credentials, headers, cookies, or private
router evidence. Each public write remains a separate RouteDeck review; the
second operation cannot inherit approval from the first.

Operations inspection is read-only. Promotion requires an explicit owner
request and selects one exact matching deployed interaction/build lineage;
viewing or explaining an interaction cannot promote it implicitly.
