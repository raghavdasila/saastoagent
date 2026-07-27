# Architecture

This directory owns current subsystem boundaries and source ownership.

- `code-map.md` maps source globs to interfaces, architecture anchors, tests,
  and update triggers.
- `components/` owns focused component contracts and invariants.
- `components/toolrouter-source-integration.md` documents the implemented
  generic Sources boundary, every API/ToolRouter file owner, artifact flow,
  failure semantics, and future connector extension point.
- `diagrams/` is reserved for maintained architecture diagrams.
- `dev_validated_docs/` is reserved for generated or tool-validated technical
  references whose provenance is recorded.

Product meaning belongs in `docs/`; current restart state belongs in
`context.md`; durable choices belong in `decisions/`.
