# Legacy Path Reference Inventory

Date: 2026-07-15 (Asia/Calcutta)

Current operator paths were updated for the standalone repository:

- `README.md`
- `docs/medusa-api-agent-test-guide.md`
- `CORPUS_HOSTINGER_DEPLOYMENT.md`
- `docs/medusa-vps-deployment.md`

The following search now finds 46 files outside dependencies, generated builds,
recordings, and the ignored Codex archive:

```powershell
rg -l "D:\\Dev\\AI Projects\\agent-core|agent-lab-powered-projects/saastoagent-v0\.1|agent-lab-powered-projects\\saastoagent-v0\.1" . \
  -g '!codex_chats_and_memories/**' \
  -g '!frontend/node_modules/**' \
  -g '!frontend/dist/**' \
  -g '!frontend/recordings/**'
```

Those remaining references are retained as chronological evidence rather than
runtime configuration:

- dated `context_history/`, `context_checkpoints/`, and `logs/` records;
- completed design and implementation plans under `docs/superpowers/plans/`;
- historical validation and test-index records;
- the preserved OpenAPI ToolRouter integration snapshot and its reports;
- `docs/migration/source-baseline.md`, which intentionally records the source
  subtree from which this repository was extracted.

Do not mechanically rewrite those records: their old paths are part of the
evidence they preserve. New commands, configuration, tests, Docker build
contexts, and package dependencies must use standalone-relative paths or the
explicit sibling RouteDeck Medusa fixture path.
