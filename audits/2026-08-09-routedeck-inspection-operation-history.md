# RouteDeck Change Report: Authenticated Recent Operation Inspection

Date: 2026-08-09

Authorization: the user explicitly authorized RouteDeck sibling changes when
every changed file and its purpose are recorded. The change was required only
after proving that Corpus could not verify genuine multi-operation chat turns
through an existing finite public contract.

## Proven framework gap

`GET /events` correctly owns durable event replay as an authenticated SSE
stream, but it intentionally remains open. `GET /inspect` is the finite,
authenticated, private/no-store diagnostic snapshot used by developer and
owner inspection, but it exposed no durable operation history. Reading the
RouteDeck SQLite store from Corpus would couple the product to framework-owned
persistence and produced transient cross-process WAL errors. Corpus therefore
could not correctly solve this with a product adapter.

## Exact RouteDeck changes and purpose

Source:

- `routedeck_fastapi/inspection.py`: adds the bounded, public-safe
  `recent_operations` projection to the finite inspection payload. Each item
  contains only event ID, cursor, operation ID, public status, and
  session/projection versions.
- `routedeck_fastapi/routes/inspection.py`: reads at most the most recent 256
  durable events through the existing `RouteDeckSessionStore.events_after`
  contract and passes them into inspection. It does not read a database
  directly or alter event/SSE behavior.
- `scripts/export_contracts.py`: declares the typed
  `InspectionOperationEvent` transport contract and makes
  `InspectionPayload.recent_operations` required.
- `packages/core/src/contracts/inspection.ts`: decodes and exposes the typed
  recent-operation collection to authenticated headless clients.

Generated contract outputs:

- `packages/core/schema/routedeck.schema.json`
- `packages/core/src/contracts/generatedRuntime.ts`
- `packages/core/src/contracts/generated.ts`

Focused proof:

- `tests/fastapi/test_transport_smoke.py`: proves a staged and accepted
  operation are returned in order and the inspection response still omits the
  private session ID.

Canonical documentation:

- `docs/route-deck-reference.md`: records bounded recent-operation history on
  `GET /inspect`.
- `architecture/components/fastapi-conversation-transport.md`: records the
  exact safe fields and forbidden private fields.

## Security and ownership boundary

The inspection endpoint remains authenticated and `private, no-store`. The
new collection never contains the private session ID, operation arguments,
request payloads, private-form values, entity values, credentials, or model
messages. RouteDeck owns durable operation identity/status; Corpus owns the
post-hoc evidence rubric. No model prompt, legal-operation selection,
supervision, review, navigation, or product behavior changed.

## Validation

```powershell
D:\Dev\AI Projects\routedeck\.venv\Scripts\python.exe -m pytest tests\fastapi -q
```

Result: `68 passed` (one existing Starlette/httpx deprecation warning).

```powershell
pnpm contracts:generate
pnpm contracts:check
pnpm --filter @routedeck/core test
pnpm --filter @routedeck/core build
```

Results: generated contracts current; core `89 passed`; core build passed.

