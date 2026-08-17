# Fresh GitHub Setup Validation - 2026-08-17

## Result

The four-repository Windows workspace was cloned from GitHub into
`D:\Dev\AI Projects\saastoagent`, configured for OpenAI, and exercised without
copying old source, build outputs, configuration, or generated secrets. Corpus,
its source worker, the RouteDeck Agent Design Studio, and a newly provisioned
Medusa 2.13.6 target were healthy. The live Corpus bearer/reconnect smoke and an
authenticated Medusa Store API request passed.

The final validation used the isolated Compose project `corpus-fresh`, host
ports 5299 and 8199, and its own newly created runtime volume so the existing
development environment could remain available. These temporary ports are not
the documented defaults.

## Repository provenance

| Repository | Origin | Verified commit |
| --- | --- | --- |
| Corpus | `https://github.com/saastoagent/saastoagent.git` | `b40a896a3a85b08fdd8d4d2ed64868bed599ec73` before this record |
| RouteDeck | `https://github.com/saastoagent/routedeck.git` | `0f777587f015bb99e69d537dcba427798ca4175f` |
| Agent Execution Runtime | `https://github.com/saastoagent/agent-execution-runtime.git` | `f0b4033562708090dff8d9a072423ddf20bc9274` |
| Agent Delivery Runtime | `https://github.com/saastoagent/agent-delivery-runtime.git` | `2fdeab9b35f0997123ecdc4b6ab670dc6795fd1b` |

RouteDeck and both runtime dependencies were clean detached checkouts at the
immutable commits recorded in
`contracts/dependency-provenance/development-source-checkouts.json`.

## Tool and runtime versions

- Git 2.50.0.windows.1
- Node.js 24.3.0
- pnpm 11.9.0
- Python 3.11.9
- Docker client/server 29.5.3
- Docker Compose 5.1.4
- Medusa 2.13.6 from RouteDeck's locked source

## Sanitized execution evidence

The following commands were run from the fresh checkouts. Secret values were
neither printed nor written to this log.

```powershell
.\scripts\clone-development-dependencies.ps1
docker compose --env-file .env.local config --quiet
docker compose --project-name corpus-fresh --env-file .env.local -f compose.yaml -f .runtime\compose.fresh-ports.yaml up --build -d backend source-worker frontend
pnpm --dir docs/corpus-agent-design/workbench install --frozen-lockfile
powershell -NoProfile -ExecutionPolicy Bypass -File .\examples\medusa-agent\scripts\demo-stack.ps1 -Action Provision
powershell -NoProfile -ExecutionPolicy Bypass -File .\examples\medusa-agent\scripts\demo-stack.ps1 -Action Up -Services medusa
```

Fresh smoke results:

- Corpus frontend `http://127.0.0.1:5299/`: HTTP 200
- Corpus backend `http://127.0.0.1:8199/healthz`: HTTP 200
- Corpus backend `http://127.0.0.1:8199/readyz`: HTTP 200
- Design Studio `http://127.0.0.1:8882/`: HTTP 200 with the expected title
- Medusa `http://127.0.0.1:9100/health`: HTTP 200
- backend container to `http://host.docker.internal:9100/health`: HTTP 200
- source worker: Huey consumer running with all five Corpus task commands
- authenticated Store API product request: HTTP 200 with four seeded products
- provider identity: OpenAI for Corpus, ToolRouter, and Evaluation; configured
  model `gpt-5.6-luna`; no Ollama provider fallback

The live command below completed successfully inside the fresh backend
container:

```powershell
python scripts/smoke_live.py --base-url http://127.0.0.1:8099 --origin http://127.0.0.1:5299
```

It proved a real OpenAI-backed anonymous conversation, a durable run,
disconnect/reconnect by cursor, and recovered conversation history.

Medusa provisioning produced the protected seed fingerprint
`routedeck-medusa-demo-v1|1|5bda6e5cfc873107f535e573b626739bc127a741e60ec482062245e1f3ec47ba`.
No publishable key, secret, user identifier, conversation identifier, product
identifier, or other private identifier is retained here.

## Hiccups and required corrections

### Canonical RouteDeck pin omitted already-tested work

- Expected: the pinned RouteDeck commit contained the contracts used by Corpus.
- Actual: Corpus startup rejected `Operation.public_outcome_schemas` because the
  required RouteDeck work existed only in the old checkout's tracked changes.
- Cause: earlier E2E validation ran against a dirty RouteDeck checkout while the
  manifest still named its unchanged commit.
- Workaround: publish the already-tested 32-file RouteDeck change set as
  `0f777587f015bb99e69d537dcba427798ca4175f` and update the Corpus pin.
- Permanent correction: fresh-clone and dependency checks must require clean
  dependency trees and verify that built source equals every recorded SHA.

### Protected Medusa reset omitted profile-owned resources

- Expected: `docker compose down --volumes` removed the exact protected demo.
- Actual: application-profile containers and six associated volumes remained.
- Cause: Compose only included resources in the active profile.
- Workaround: rerun the protected teardown with `--profile application` after
  verifying every remaining container and volume protection label.
- Permanent correction: the RouteDeck reset procedure must enumerate and handle
  every protected profile-owned resource.

### Protected volumes produce Compose ownership warnings

- Expected: first-time provisioning started without ownership warnings.
- Actual: Compose warned that the pre-created protected Postgres and Redis
  volumes were not created by Compose. Provisioning and health still passed.
- Cause: the protection script creates the labeled volumes before Compose.
- Workaround: none required for this validation.
- Permanent correction: declare the protected volumes consistently as external
  or align provisioning ownership with Compose.

### Temporary Compose project collision during parallel validation

- Expected: the fresh runtime never mounted existing Corpus state.
- Actual: an initial fresh start reused the default Compose project and briefly
  mounted the old named database volume with the fresh clone's encryption key.
- Cause: source-path separation does not change Compose project identity.
- Workaround: isolate the fresh run as `corpus-fresh` with new ports, network,
  and volume. One collision-created session was removed from the old database
  after recoverable backups were made; all retained encrypted records validated.
- Permanent correction: the fresh-setup procedure must assign an explicit
  unique Compose project whenever another checkout or retained default volume
  exists.

### Full horizontal ecommerce replay has an external source dependency

- Expected: the four documented repositories were sufficient for a full
  horizontal ecommerce replay.
- Actual: the runner defaults to a Medusa OpenAPI document under an undocumented
  `agent-core` checkout, and a related connection runner contains an old local
  RouteDeck environment path.
- Cause: benchmark input provenance and paths are not owned by the four-repo
  bootstrap contract.
- Workaround: this setup validation used the live Corpus smoke and authenticated
  Store API smoke; it did not claim a four-repository horizontal E2E replay.
- Permanent correction: move the approved OpenAPI artifact into a canonical
  documented owner and make both paths explicit configuration or CLI inputs.

## Validation boundary

This record proves reproducible source acquisition, isolated local startup,
OpenAI-backed Corpus conversation continuity, and the real Medusa Store API
path. It does not claim the blocked four-repository horizontal ecommerce replay,
deployment, multi-host operation, exhaustive E2E coverage, or production SLA.
