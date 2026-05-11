# Packaging Roadmap

RouteDeck is repo-local today. The folder structure is designed for later extraction.

## PyPI

Candidate package: `routedeck-core`

Initial public API:

- `RouteDeckManifest`
- `RouteDeckNodeSpec`
- `RouteDeckEdgeSpec`
- `RouteDeckActionSpec`
- `RouteDeckFieldSpec`
- `RouteDeckSensitivePolicy`
- `RouteDeckRuntimeSnapshot`
- `validate_manifest()`
- `build_runtime_snapshot()`
- `reachable_nodes()`

Before publishing:

- Add isolated package tests under `routedeck_framework/tests`.
- Add semantic versioning and changelog.
- Replace repo-relative imports with normal package imports.
- Add examples to the package README.

## npm

Candidate package: `@routedeck/react`

Initial public API:

- `RouteDeckDebugger`
- RouteDeck TypeScript manifest and snapshot types.

Before publishing:

- Add build config that outputs ESM and declaration files.
- Keep React and `@xyflow/react` as peer dependencies.
- Add visual tests or story examples.
- Remove SaaStoAgent styling assumptions or document required CSS classes.

## Contract Compatibility

RouteDeck should preserve a stable JSON shape for manifests and runtime snapshots. Product-specific adapters may add fields, but the core packages should remain framework-level and domain-neutral.
