# Corpus Repository Structure

Status: feature-free scaffold with active context architecture

```text
saastoagent-v0.1/
|-- AGENTIC_CODING_GUIDE.md          # Corpus-specific operating sequence
|-- backend/
|   |-- src/corpus/
|   |   |-- app/                     # future host and transport boundary
|   |   |-- routedeck/               # future RouteDeck integration boundary
|   |   |-- runtime/                 # future node-scoped Corpus agent runtime
|   |   `-- shared/                  # future backend shared primitives
|   `-- tests/
|-- frontend/
|   |-- src/
|   |   |-- app/                     # future permanent Corpus chat shell
|   |   |-- routedeck/               # future state and projection bridge
|   |   |-- surfaces/                # future surface render boundary
|   |   `-- shared/                  # future frontend shared primitives
|   `-- tests/
|-- contracts/                       # future language-neutral contracts
|-- docs/                            # product, behavior, design notebook
|-- architecture/
|   |-- code-map.md                  # subsystem source/doc/test ownership
|   |-- components/                  # subsystem contracts
|   |-- diagrams/                    # maintained architecture visuals
|   `-- dev_validated_docs/          # generated/tool-validated references
|-- decisions/                       # durable ADRs
|-- plans/                           # active plans only
|-- test_index/                      # executable validation commands/meaning
|-- scripts/                         # repository-local validation tools
|-- tests/                           # tests for repository-local tooling
|-- logs/                            # dated session evidence
|-- context_checkpoints/             # restart handoffs
|-- context_history/                 # archived prior live contexts
|-- knowledgebase/                   # verified reusable findings
|-- audits/                          # read-only audit reports
|-- errors/                          # reusable debugging evidence
|-- skills/                          # stable repeatable repo-local workflows
`-- benchmark/
    `-- saastoagent-v0.1/            # ignored local legacy baseline
```

Feature directories and framework manifests are deliberately absent. They will
be introduced only after their contracts are refined and dependencies are
researched and approved. The ignored benchmark remains local comparison
evidence and cannot be imported by new code.
