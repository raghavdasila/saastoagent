# Corpus Code Map

Last updated: 2026-07-21

This is the canonical subsystem-to-code ownership map. The implementation rows
describe the planned empty scaffold honestly; the context/tooling rows describe
the executable project-memory infrastructure now present.

## How To Use This Map

- Identify the owning row before changing source, tests, contracts, or current
  behavior documentation.
- Update a row when ownership, interfaces, architecture anchors, tests, or
  update triggers move.
- During closeout, name each changed source file's row and state which anchors
  changed or remained unchanged.
- Run `python scripts/check_doc_coverage.py` before closeout.

The `Source globs` column is parsed by the coverage checker. Keep globs
comma-separated, backtick-delimited, and relative to the repository root.

| Subsystem | Purpose | Source globs | Interfaces | Architecture anchors | Test anchors | Update triggers |
| --- | --- | --- | --- | --- | --- | --- |
| Backend host | Transport, auth, tenancy, and application composition | `backend/src/corpus/app/**` | Not implemented | `architecture/components/corpus-routedeck-boundary.md`, `SYSTEM_FLOW_INDEX.md` | No runtime gate yet; add command to `test_index/README.md` with implementation | Transport, host composition, auth, tenancy, or public endpoint changes |
| Corpus agent runtime | Primary chat loop and node-scoped model execution | `backend/src/corpus/runtime/**` | Not implemented | `docs/corpus-product-definition.md`, `architecture/components/corpus-routedeck-boundary.md`, `SYSTEM_FLOW_INDEX.md` | No runtime gate yet; add real chat-path validation with implementation | Agent loop, node scope, prompt/context/tool exposure, model execution, or failure-semantic changes |
| RouteDeck integration | Corpus definitions, state dispatch, and projections without framework duplication | `backend/src/corpus/routedeck/**`, `frontend/src/routedeck/**` | Not implemented | `architecture/components/corpus-routedeck-boundary.md`, `SYSTEM_FLOW_INDEX.md` | No runtime gate yet; validate against approved standalone RouteDeck contracts | RouteDeck version, state ownership, operation legality, transition, projection, or diagnostics changes |
| Frontend app shell | Permanent Corpus chat surface and application composition | `frontend/src/app/**` | Not implemented | `docs/corpus-product-definition.md`, `SYSTEM_FLOW_INDEX.md` | No runtime/browser gate yet; add rendered interaction checks with implementation | Shell composition, navigation, chat interaction, accessibility, or responsive-layout changes |
| Surface rendering | Standard and registered custom surface boundary | `frontend/src/surfaces/**` | Not implemented | `docs/corpus-product-definition.md`, `architecture/components/corpus-routedeck-boundary.md` | No surface gate yet; add rendered typed-operation checks with implementation | Surface registry, schema dispatch, operation emission, compatibility, or rendering changes |
| Shared contracts | Language-neutral agent, runtime, evalset/result, channel, and projection schemas | `contracts/**` | Not implemented | `contracts/README.md`, `docs/corpus-product-definition.md` | No schema gate yet; add compatibility checks with first contract | Schema, versioning, compatibility, required agent configuration, or serialization changes |
| Shared implementation primitives | Backend/frontend primitives without feature ownership | `backend/src/corpus/shared/**`, `frontend/src/shared/**` | Not implemented | `architecture/code-map.md` | Add focused tests with first primitive | Shared primitive ownership, public export, cross-subsystem dependency, or failure-semantic changes |
| Feature implementations | Future feature-owned backend/frontend packages | Not created | Not defined | `docs/corpus-product-definition.md` | Must be defined with each approved feature slice | Create a row and component/test anchors before introducing a feature package |
| Product and behavior documentation | Current Corpus product meaning, verified benchmark behavior, and design notebook | `docs/**/*.md`, `docs/**/*.html` | Design notebook and documented product contracts | `docs/README.md`, `critical_prompt.md`, `SYSTEM_FLOW_INDEX.md` | `python scripts/validate_design_notebook.py` | Product boundary, feature layout, proven behavior, Navgraph adjacency/count, or notebook script changes |
| Context architecture lifecycle | Restart state, handoffs, ownership docs, decisions, plans, audits, and evidence | `*.md`, `architecture/**/*.md`, `plans/**/*.md`, `decisions/**/*.md`, `logs/**/*.md`, `context_checkpoints/**/*.md`, `context_history/**/*.md`, `knowledgebase/**/*.md`, `audits/**/*.md`, `errors/**/*.md` | Session start/end workflow, code map, checkpoints, ADRs, folder ownership docs | `AGENTIC_CODING_GUIDE.md`, `context_pipeline.md`, `work_prompt.md`, `architecture/README.md` | `python scripts/check_doc_coverage.py --help`, documentation self-review | Context lifecycle, folder inventory, closeout rules, authority, or ownership policy changes |
| Repo-local skills | Stable repeatable Corpus workflows | `skills/**/*.md`, `skills/**/*.py`, `skills/**/*.json` | Skill `SKILL.md` files and declared resources | `skills/README.md`, `architecture/code-map.md` | Skill self-review; `python scripts/check_doc_coverage.py --files skills/README.md` | Skill trigger, input/output/check, stop condition, or bundled resource changes |
| Validation tooling | Structural validators and their tests | `scripts/**/*.py`, `tests/**/*.py`, `test_index/**/*.md` | Python command-line validators and unittest discovery | `architecture/code-map.md`, `test_index/README.md` | `python -m unittest discover -v`, `python scripts/validate_design_notebook.py` | Validator behavior, acceptance claim, test movement, command, or failure-semantic changes |
| Benchmark | Preserved local legacy behavior and visual baseline | `benchmark/saastoagent-v0.1/**` | Read-only, ignored reference; never a new-runtime interface | `docs/corpus-behavior-reference.md`, `critical_prompt.md` | Use only the benchmark's own commands when explicitly in scope | User explicitly authorizes benchmark analysis or maintenance; never update as a side effect of Corpus implementation |

## Closeout Rule

For each changed source file matched by a row, record the row and the updated
architecture/test anchors—or explicitly state why the documented contract and
validation meaning remain unchanged.
