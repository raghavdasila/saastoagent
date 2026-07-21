# Corpus Validation Index

The new Corpus scaffold has no runtime or dependency manifest yet. The current
executable gates protect the context architecture and proposed design artifact;
they do not claim backend, frontend, RouteDeck, persistence, or deployment
readiness.

## Executable Suite Index

| Suite | Command | Protects | Source owner |
| --- | --- | --- | --- |
| Design notebook structure | `python scripts/validate_design_notebook.py` | Exactly 15 feature groups, 53 unique nodes, 146 parsed edges, zero undeclared edge targets, matching summary chips, and Node.js syntax validity for every inline script | Product and behavior documentation |
| Context tooling unit suite | `python -m unittest discover -v` | Code-map parsing, Git rename parsing, glob matching, unmatched-file warnings, and current Navgraph structural counts | Validation tooling |
| Coverage checker CLI | `python scripts/check_doc_coverage.py --help` | The advisory ownership-mapping command remains invocable | Validation tooling |
| Changed-file ownership advisory | `python scripts/check_doc_coverage.py` | Changed supported files are mapped to code-map rows and their architecture/test anchors for review; warnings are advisory and exit 0 | Context architecture lifecycle, Validation tooling |
| Targeted ownership advisory | `python scripts/check_doc_coverage.py --files docs/corpus-routedeck-design-notebook.html scripts/validate_design_notebook.py` | Explicit notebook/tooling files resolve to documented owners without depending on working-tree state | Product and behavior documentation, Validation tooling |

## Prerequisites

- Python 3.10 or newer for repository-local scripts and tests.
- Node.js on `PATH` for inline JavaScript syntax checking. Missing Node.js is a
  validation failure, not a skipped check.

## What Is Not Yet Proven

- no new Corpus runtime starts;
- no backend or frontend behavior exists;
- no RouteDeck integration is installed;
- no persistence, source, model, memory, sandbox, evaluation, channel,
  deployment, operations, or learning path exists.

Add exact end-to-end commands to this index with the first real implementation
of each path. Tests must use the actual integration or source of truth for the
behavior they claim to prove.

## Architecture Coverage Link

`architecture/code-map.md` owns source-to-test mapping. When adding, moving, or
removing tests or validators, update its owning row and any affected component
document.
