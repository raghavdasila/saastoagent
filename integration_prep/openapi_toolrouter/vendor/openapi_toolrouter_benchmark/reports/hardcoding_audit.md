# Hardcoding Audit

Scope: `toolrouter/*.py`

## Result

Reusable routing code no longer embeds Medusa business-domain coverage terms or a custom stopword list.

## Fixed

- Removed the resource denylist from `openapi_loader.clean_resource()`. The previous list included generic path/source terms such as `admin`, `store`, `api`, version labels, and `id`; that was effectively a stopword list.
- Removed hardcoded Medusa coverage domains from `tasks.py`.
- Removed the hardcoded `medusa_` task id prefix from the reusable task generator.
- Replaced business-policy wording about issuing credits with provider-neutral policy-abstention task text.
- Moved Medusa target coverage terms to `data/medusa_task_coverage.json`.
- Added `--coverage` and `--task-prefix` task CLI options so target-specific benchmark requirements are provided as data/config.

## Remaining Target-Specific Code

These are intentional target commands/scripts, not reusable routing rules:

- `__main__.py` contains `fetch-medusa-specs`, which downloads the two official Medusa OpenAPI specs.
- `medusa_smoke.py` contains the required Medusa local smoke flow: admin email/password auth, `GET /admin/products`, and `GET /store/products`.

## Remaining Generic Constants

These are generic benchmark semantics rather than Medusa/business rules:

- HTTP methods.
- Operation classes: `list`, `get`, `create`, `update`, `delete`, `search`, `custom`.
- Graph edge/node kind names.
- Evaluation metric names.
- Report filenames.

## Notes

The current Medusa task run still covers products, orders, customers, carts, inventory, payments, fulfillment, returns, and promotions. The coverage list is now an external benchmark target config, not a reusable package constant.
