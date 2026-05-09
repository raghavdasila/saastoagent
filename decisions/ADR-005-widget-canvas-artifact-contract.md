# ADR-005 — Widget And Canvas Artifact Contract

Date: 2026-05-09
Status: Accepted

## Context

The entry assistant needs to do more than produce text. It should answer platform questions, summarize setup drafts, preview API connection details, show citations, and later support richer operator workflows. At the same time, canvas UI should not be permanently mounted or become a second primary product surface.

The frontend should stay thin: backend graph/runtime decisions produce artifacts, and the frontend renders them through stable contracts.

## Decision

Use backend-emitted UI artifacts for non-text assistant output.

Supported artifact categories:

- typed React-rendered widgets
- sanitized display-only markup
- canvas-capable artifacts that can be promoted from chat into a larger panel/canvas surface

Rendering rules:

- mobile and narrow screens render artifacts inline in chat
- desktop can show a side canvas when the user opens a canvas-capable artifact
- canvas/panels are closed by default and mount only when useful
- unknown widget types fail closed with a compact unsupported artifact state
- markup is display-only and sanitized with a strict allowlist

Initial widget types include:

- platform overview
- onboarding checklist
- setup draft summary
- API connection preview
- knowledge citations

## Consequences

- The backend can progressively enrich the conversation without hardcoding product logic into React.
- Chat remains primary; canvas is an optional focus surface, not a permanent split layout.
- Unsafe markup features such as scripts, handlers, forms, iframes, external loading elements, and unsafe links are rejected.
- Future widgets must be added through the artifact registry and typed payloads.
- This contract is the extension point for richer operator workflows, generated inspections, and setup previews.
