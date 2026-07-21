# Corpus Code Map

Status: planned ownership map for an empty scaffold

| Subsystem | Purpose | Source globs | Interfaces | Documentation | Validation |
| --- | --- | --- | --- | --- | --- |
| Backend host | Transport, auth, tenancy and application composition | `backend/src/corpus/app/**` | Not implemented | `architecture/components/corpus-routedeck-boundary.md` | No runtime yet |
| Corpus agent runtime | Primary chat loop and node-scoped model execution | `backend/src/corpus/runtime/**` | Not implemented | `docs/corpus-product-definition.md` | No runtime yet |
| RouteDeck integration | Product definitions, state dispatch and projections without framework duplication | `backend/src/corpus/routedeck/**`, `frontend/src/routedeck/**` | Not implemented | `architecture/components/corpus-routedeck-boundary.md` | No runtime yet |
| Frontend app shell | Permanent Corpus chat surface and application composition | `frontend/src/app/**` | Not implemented | `docs/corpus-product-definition.md` | No runtime yet |
| Surface rendering | Standard and registered custom surface render boundary | `frontend/src/surfaces/**` | Not implemented | `docs/corpus-product-definition.md` | No runtime yet |
| Shared contracts | Agent Configuration, evalset/result, channel and projection schemas | `contracts/**` | Not implemented | `contracts/README.md` | No schema checks yet |
| Feature implementations | Future feature-owned backend/frontend packages | Not created | Not defined | `docs/corpus-product-definition.md` | Must be defined with each feature |
| Benchmark | Preserved legacy behavior and visual baseline | `benchmark/saastoagent-v0.1/**` | Read-only reference | `docs/corpus-behavior-reference.md` | Use benchmark's own commands |

Update this map when an actual runtime, public interface, feature package, test
suite, or ownership boundary is introduced.
