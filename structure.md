# Corpus Repository Structure

Status: initial feature-free scaffold

```text
saastoagent-v0.1/
├── backend/
│   ├── src/corpus/
│   │   ├── app/                 # host composition and transport boundary
│   │   ├── routedeck/           # RouteDeck product integration boundary
│   │   ├── runtime/             # node-scoped primary Corpus agent runtime
│   │   └── shared/              # backend primitives without feature ownership
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/                 # permanent Corpus chat shell
│   │   ├── routedeck/           # state and projection bridge
│   │   ├── surfaces/            # standard surface render boundary
│   │   └── shared/              # frontend primitives without feature ownership
│   └── tests/
├── contracts/                   # language-neutral agent/runtime contracts
├── docs/                        # product definition, behavior, notebook
├── architecture/                # ownership map and subsystem contracts
├── decisions/                   # durable architecture decisions
├── plans/                       # active plans only
├── test_index/                  # validation commands and meanings
├── context_checkpoints/         # restart checkpoints
├── context_history/             # superseded context snapshots
├── logs/                        # session evidence
└── benchmark/
    └── saastoagent-v0.1/        # preserved legacy application; no new imports
```

Feature directories are deliberately absent. They will be introduced only
after their contracts are refined. This tree does not prescribe a backend or
frontend framework yet.
