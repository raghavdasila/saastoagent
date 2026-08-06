# Corpus Documentation

This directory owns product meaning, verified behavior references, and design
artifacts. It does not own current source boundaries or session state.

- `corpus-product-definition.md` — locked product layout, not locked features.
- `corpus-behavior-reference.md` — verified legacy benchmark behavior.
- `corpus-routedeck-design-notebook.html` — mobile design discussion artifact
  and proposed RouteDeck Navgraph.

- `corpus-feature-behavior-notebook.html` combines the focused authoring
  interface for the approved 11-feature basic-agent slice with an interactive
  launch-structure explorer. The explorer documents the responsibility,
  separation rationale, and exclusions for every proposed folder and file.
- `feature-behavior-notes.md` contains owner-authored working notes saved from
  that interface; they remain discussion input until formally reconciled.
- `toolrouter-integration-requirements.md` owns the implemented launch-scope
  requirements, connector/adapter boundaries, persistence/failure contracts,
  and exact local completion evidence for the Sources API connector.
- `local-runtime-runbook.md` is the authoritative procedure for host Ollama,
  Corpus Docker backend/frontend, and the RouteDeck Agent Design Studio at
  `http://127.0.0.1:8782/`. Its isolated-capability section also gives the exact
  optional commands and claim boundary for the standalone Agent Execution
  Runtime.
- `standalone-source-hub-integration.md` measures the independently proven
  Source Hub/API Source suite against the 11-feature launch baseline and owns
  the future Corpus adapter/integration map. The suite is not currently
  imported into Corpus.

## Stale Design Artifacts

`corpus-feature-behavior-notebook.html` and its server on port `8771` are stale
legacy design artifacts. They are retained as historical reference, not as the
current Design Studio or startup path. The isolated R1 prototype under
`mockruns/corpus-r1` on port `8783` is also stale and reference-only.

The authoritative Studio is `docs/corpus-agent-design/workbench/`; run it with:

```powershell
pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort
```

Open `http://127.0.0.1:8782/`.

## Historical Notebook Instructions

Run the behavior notebook only when intentionally reviewing that stale
historical artifact:

```powershell
python scripts/feature_behavior_notebook.py
```

Open `http://127.0.0.1:8771/`. Its global save action atomically replaces
`docs/feature-behavior-notes.md`; browser-local drafts protect unsaved typing.
Use the `Structure explorer` tab to review the connector-based Sources and
Channels layout without changing the notes file.

Run `python scripts/validate_design_notebook.py` after changing the notebook's
Navgraph adjacency or inline JavaScript.
