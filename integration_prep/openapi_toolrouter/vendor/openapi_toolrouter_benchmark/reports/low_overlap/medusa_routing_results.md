# OpenAPI Routing Results

## Graph-Enriched RAG Baselines

| Split | Baseline | k | Complete | Routing@1 | Routing@10 | Ambiguous Abstain | Policy Abstain | Macro Track | Required Params | Validation | Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | GRAG_EXPAND | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_EXPAND | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_EXPAND | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_EXPAND | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_RERANK | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_RERANK | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_RERANK | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_RERANK | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_CONSTRAINED | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_CONSTRAINED | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_CONSTRAINED | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAG_CONSTRAINED | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| dev | GRAG_EXPAND | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_EXPAND | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_EXPAND | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_EXPAND | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_RERANK | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_RERANK | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_RERANK | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_RERANK | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_CONSTRAINED | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_CONSTRAINED | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_CONSTRAINED | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAG_CONSTRAINED | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_EXPAND | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_EXPAND | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_EXPAND | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_EXPAND | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_RERANK | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_RERANK | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_RERANK | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_RERANK | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_CONSTRAINED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_CONSTRAINED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_CONSTRAINED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAG_CONSTRAINED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_EXPAND | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_EXPAND | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_EXPAND | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_EXPAND | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_RERANK | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_RERANK | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_RERANK | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_RERANK | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_CONSTRAINED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_CONSTRAINED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_CONSTRAINED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAG_CONSTRAINED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:carts | GRAG_EXPAND | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_EXPAND | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_EXPAND | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_EXPAND | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_RERANK | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_RERANK | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_RERANK | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_RERANK | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_CONSTRAINED | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_CONSTRAINED | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_CONSTRAINED | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAG_CONSTRAINED | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:claims | GRAG_EXPAND | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_EXPAND | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_EXPAND | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_EXPAND | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_RERANK | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_RERANK | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_RERANK | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_RERANK | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_CONSTRAINED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_CONSTRAINED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_CONSTRAINED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAG_CONSTRAINED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_EXPAND | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_EXPAND | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_EXPAND | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_EXPAND | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_RERANK | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_RERANK | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_RERANK | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_RERANK | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_CONSTRAINED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_CONSTRAINED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_CONSTRAINED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAG_CONSTRAINED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_EXPAND | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_EXPAND | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_EXPAND | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_EXPAND | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_RERANK | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_RERANK | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_RERANK | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_RERANK | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_CONSTRAINED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_CONSTRAINED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_CONSTRAINED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAG_CONSTRAINED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:customers | GRAG_EXPAND | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_EXPAND | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_EXPAND | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_EXPAND | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_RERANK | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_RERANK | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_RERANK | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_RERANK | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_CONSTRAINED | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_CONSTRAINED | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_CONSTRAINED | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAG_CONSTRAINED | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:fulfillment | GRAG_EXPAND | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_EXPAND | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_EXPAND | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_EXPAND | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_RERANK | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_RERANK | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_RERANK | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_RERANK | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_CONSTRAINED | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_CONSTRAINED | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_CONSTRAINED | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAG_CONSTRAINED | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:inventory | GRAG_EXPAND | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_EXPAND | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_EXPAND | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_EXPAND | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_RERANK | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_RERANK | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_RERANK | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_RERANK | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_CONSTRAINED | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_CONSTRAINED | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_CONSTRAINED | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAG_CONSTRAINED | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:orders | GRAG_EXPAND | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_EXPAND | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_EXPAND | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_EXPAND | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_RERANK | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_RERANK | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_RERANK | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_RERANK | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_CONSTRAINED | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_CONSTRAINED | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_CONSTRAINED | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAG_CONSTRAINED | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:payments | GRAG_EXPAND | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_EXPAND | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_EXPAND | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_EXPAND | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_RERANK | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_RERANK | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_RERANK | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_RERANK | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_CONSTRAINED | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_CONSTRAINED | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_CONSTRAINED | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAG_CONSTRAINED | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_EXPAND | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_EXPAND | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_EXPAND | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_EXPAND | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_RERANK | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_RERANK | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_RERANK | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_RERANK | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_CONSTRAINED | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_CONSTRAINED | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_CONSTRAINED | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAG_CONSTRAINED | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_EXPAND | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_EXPAND | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_EXPAND | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_EXPAND | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_RERANK | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_RERANK | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_RERANK | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_RERANK | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_CONSTRAINED | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_CONSTRAINED | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_CONSTRAINED | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAG_CONSTRAINED | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_EXPAND | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_EXPAND | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_EXPAND | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_EXPAND | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_RERANK | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_RERANK | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_RERANK | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_RERANK | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_CONSTRAINED | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_CONSTRAINED | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_CONSTRAINED | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAG_CONSTRAINED | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| test | GRAG_EXPAND | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_EXPAND | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_EXPAND | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_EXPAND | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_RERANK | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_RERANK | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_RERANK | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_RERANK | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_CONSTRAINED | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_CONSTRAINED | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_CONSTRAINED | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAG_CONSTRAINED | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| train | GRAG_EXPAND | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_EXPAND | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_EXPAND | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_EXPAND | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_RERANK | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_RERANK | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_RERANK | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_RERANK | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_CONSTRAINED | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_CONSTRAINED | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_CONSTRAINED | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAG_CONSTRAINED | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |

## Required Ablations

| Split | Baseline | k | Complete | Routing@1 | Routing@10 | Ambiguous Abstain | Policy Abstain | Macro Track | Required Params | Validation | Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | RAG_ALL_MAX | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_MAX | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_MAX | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_MAX | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_MAX | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_MAX | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_MAX | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_MAX | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAPH_SPARSE | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAPH_SPARSE | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAPH_SPARSE | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAPH_SPARSE | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| dev | RAG_ALL_MAX | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_MAX | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_MAX | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_MAX | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_MAX | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_MAX | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_MAX | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_MAX | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAPH_SPARSE | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAPH_SPARSE | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAPH_SPARSE | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAPH_SPARSE | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAPH_SPARSE | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAPH_SPARSE | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAPH_SPARSE | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAPH_SPARSE | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAPH_SPARSE | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAPH_SPARSE | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAPH_SPARSE | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAPH_SPARSE | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:carts | RAG_ALL_MAX | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_MAX | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_MAX | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_MAX | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_MAX | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_MAX | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_MAX | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_MAX | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAPH_SPARSE | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAPH_SPARSE | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAPH_SPARSE | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAPH_SPARSE | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:claims | RAG_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAPH_SPARSE | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAPH_SPARSE | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAPH_SPARSE | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAPH_SPARSE | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAPH_SPARSE | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAPH_SPARSE | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAPH_SPARSE | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAPH_SPARSE | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAPH_SPARSE | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAPH_SPARSE | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAPH_SPARSE | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAPH_SPARSE | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:customers | RAG_ALL_MAX | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_MAX | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_MAX | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_MAX | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_MAX | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_MAX | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_MAX | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_MAX | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAPH_SPARSE | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAPH_SPARSE | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAPH_SPARSE | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAPH_SPARSE | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_MAX | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_MAX | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_MAX | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_MAX | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_MAX | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_MAX | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_MAX | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_MAX | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAPH_SPARSE | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAPH_SPARSE | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAPH_SPARSE | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAPH_SPARSE | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_MAX | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_MAX | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_MAX | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_MAX | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_MAX | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_MAX | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_MAX | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_MAX | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAPH_SPARSE | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAPH_SPARSE | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAPH_SPARSE | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAPH_SPARSE | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:orders | RAG_ALL_MAX | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_MAX | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_MAX | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_MAX | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_MAX | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_MAX | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_MAX | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_MAX | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAPH_SPARSE | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAPH_SPARSE | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAPH_SPARSE | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAPH_SPARSE | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:payments | RAG_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAPH_SPARSE | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAPH_SPARSE | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAPH_SPARSE | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAPH_SPARSE | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAPH_SPARSE | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAPH_SPARSE | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAPH_SPARSE | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAPH_SPARSE | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAPH_SPARSE | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAPH_SPARSE | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAPH_SPARSE | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAPH_SPARSE | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_MAX | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_MAX | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_MAX | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_MAX | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAPH_SPARSE | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAPH_SPARSE | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAPH_SPARSE | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAPH_SPARSE | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| test | RAG_ALL_MAX | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_MAX | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_MAX | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_MAX | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_MAX | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_MAX | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_MAX | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_MAX | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAPH_SPARSE | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAPH_SPARSE | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAPH_SPARSE | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAPH_SPARSE | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| train | RAG_ALL_MAX | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_MAX | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_MAX | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_MAX | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_MAX | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_MAX | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_MAX | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_MAX | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAPH_SPARSE | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAPH_SPARSE | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAPH_SPARSE | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAPH_SPARSE | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |

## Other Baselines

| Split | Baseline | k | Complete | Routing@1 | Routing@10 | Ambiguous Abstain | Policy Abstain | Macro Track | Required Params | Validation | Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | BM25_ALL_MEAN | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_MEAN | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_MEAN | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_MEAN | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_TOP3 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_TOP3 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_TOP3 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | BM25_ALL_TOP3 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAPH_TEXT | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAPH_TEXT | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAPH_TEXT | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | GRAPH_TEXT | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | HYBRID | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | HYBRID | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | HYBRID | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | HYBRID | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_ALL | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_ALL | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_ALL | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_ALL | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_BM25 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_BM25 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_BM25 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_BM25 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_GRAPH | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_GRAPH | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_GRAPH | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_GRAPH | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_LEXICAL | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_LEXICAL | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_LEXICAL | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_LEXICAL | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_LEXICAL_GRAPH | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_LEXICAL_GRAPH | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_LEXICAL_GRAPH | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_LEXICAL_GRAPH | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_SCHEMA_PARAM | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_SCHEMA_PARAM | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_SCHEMA_PARAM | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | LEARNED_SCHEMA_PARAM | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_MEAN | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_MEAN | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_MEAN | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_MEAN | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_TOP3 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_TOP3 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_TOP3 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ALL_TOP3 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ENDPOINT | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ENDPOINT | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ENDPOINT | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| all | RAG_ENDPOINT | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% | 0.00 |
| dev | BM25_ALL_MEAN | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_MEAN | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_MEAN | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_MEAN | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_TOP3 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_TOP3 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_TOP3 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | BM25_ALL_TOP3 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAPH_TEXT | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAPH_TEXT | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAPH_TEXT | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | GRAPH_TEXT | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | HYBRID | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | HYBRID | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | HYBRID | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | HYBRID | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_ALL | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_ALL | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_ALL | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_ALL | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_BM25 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_BM25 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_BM25 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_BM25 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_GRAPH | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_GRAPH | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_GRAPH | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_GRAPH | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_LEXICAL | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_LEXICAL | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_LEXICAL | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_LEXICAL | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_LEXICAL_GRAPH | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_LEXICAL_GRAPH | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_LEXICAL_GRAPH | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_LEXICAL_GRAPH | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_SCHEMA_PARAM | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_SCHEMA_PARAM | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_SCHEMA_PARAM | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | LEARNED_SCHEMA_PARAM | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_MEAN | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_MEAN | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_MEAN | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_MEAN | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_TOP3 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_TOP3 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_TOP3 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ALL_TOP3 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ENDPOINT | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ENDPOINT | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ENDPOINT | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| dev | RAG_ENDPOINT | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | BM25_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAPH_TEXT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAPH_TEXT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAPH_TEXT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | GRAPH_TEXT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | HYBRID | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | HYBRID | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | HYBRID | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | HYBRID | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_ALL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_ALL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_ALL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_ALL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_BM25 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_BM25 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_BM25 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_BM25 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_LEXICAL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_LEXICAL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_LEXICAL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_LEXICAL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_LEXICAL_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_LEXICAL_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_LEXICAL_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_LEXICAL_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_SCHEMA_PARAM | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_SCHEMA_PARAM | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_SCHEMA_PARAM | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | LEARNED_SCHEMA_PARAM | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ENDPOINT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ENDPOINT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ENDPOINT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:api_keys | RAG_ENDPOINT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | BM25_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAPH_TEXT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAPH_TEXT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAPH_TEXT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | GRAPH_TEXT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | HYBRID | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | HYBRID | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | HYBRID | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | HYBRID | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_ALL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_ALL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_ALL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_ALL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_BM25 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_BM25 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_BM25 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_BM25 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_LEXICAL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_LEXICAL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_LEXICAL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_LEXICAL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_LEXICAL_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_LEXICAL_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_LEXICAL_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_LEXICAL_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_SCHEMA_PARAM | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_SCHEMA_PARAM | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_SCHEMA_PARAM | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | LEARNED_SCHEMA_PARAM | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ENDPOINT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ENDPOINT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ENDPOINT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:auth | RAG_ENDPOINT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:carts | BM25_ALL_MEAN | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_MEAN | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_MEAN | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_MEAN | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_TOP3 | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_TOP3 | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_TOP3 | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | BM25_ALL_TOP3 | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAPH_TEXT | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAPH_TEXT | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAPH_TEXT | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | GRAPH_TEXT | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | HYBRID | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | HYBRID | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | HYBRID | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | HYBRID | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_ALL | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_ALL | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_ALL | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_ALL | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_BM25 | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_BM25 | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_BM25 | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_BM25 | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_GRAPH | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_GRAPH | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_GRAPH | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_GRAPH | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_LEXICAL | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_LEXICAL | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_LEXICAL | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_LEXICAL | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_LEXICAL_GRAPH | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_LEXICAL_GRAPH | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_LEXICAL_GRAPH | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_LEXICAL_GRAPH | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_SCHEMA_PARAM | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_SCHEMA_PARAM | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_SCHEMA_PARAM | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | LEARNED_SCHEMA_PARAM | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_MEAN | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_MEAN | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_MEAN | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_MEAN | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_TOP3 | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_TOP3 | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_TOP3 | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ALL_TOP3 | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ENDPOINT | 1 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ENDPOINT | 3 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ENDPOINT | 5 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:carts | RAG_ENDPOINT | 10 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% | 0.00 |
| leave_domain_out:claims | BM25_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | BM25_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAPH_TEXT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAPH_TEXT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAPH_TEXT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | GRAPH_TEXT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | HYBRID | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | HYBRID | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | HYBRID | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | HYBRID | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_ALL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_ALL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_ALL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_ALL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_BM25 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_BM25 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_BM25 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_BM25 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_LEXICAL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_LEXICAL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_LEXICAL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_LEXICAL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_LEXICAL_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_LEXICAL_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_LEXICAL_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_LEXICAL_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_SCHEMA_PARAM | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_SCHEMA_PARAM | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_SCHEMA_PARAM | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | LEARNED_SCHEMA_PARAM | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ENDPOINT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ENDPOINT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ENDPOINT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:claims | RAG_ENDPOINT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | BM25_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAPH_TEXT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAPH_TEXT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAPH_TEXT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | GRAPH_TEXT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | HYBRID | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | HYBRID | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | HYBRID | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | HYBRID | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_ALL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_ALL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_ALL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_ALL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_BM25 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_BM25 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_BM25 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_BM25 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_LEXICAL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_LEXICAL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_LEXICAL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_LEXICAL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_LEXICAL_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_LEXICAL_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_LEXICAL_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_LEXICAL_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_SCHEMA_PARAM | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_SCHEMA_PARAM | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_SCHEMA_PARAM | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | LEARNED_SCHEMA_PARAM | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ENDPOINT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ENDPOINT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ENDPOINT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:collections | RAG_ENDPOINT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | BM25_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAPH_TEXT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAPH_TEXT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAPH_TEXT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | GRAPH_TEXT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | HYBRID | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | HYBRID | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | HYBRID | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | HYBRID | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_ALL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_ALL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_ALL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_ALL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_BM25 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_BM25 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_BM25 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_BM25 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_LEXICAL | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_LEXICAL | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_LEXICAL | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_LEXICAL | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_LEXICAL_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_LEXICAL_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_LEXICAL_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_LEXICAL_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_SCHEMA_PARAM | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_SCHEMA_PARAM | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_SCHEMA_PARAM | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | LEARNED_SCHEMA_PARAM | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ENDPOINT | 1 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ENDPOINT | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ENDPOINT | 5 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:currencies | RAG_ENDPOINT | 10 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:customers | BM25_ALL_MEAN | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_MEAN | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_MEAN | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_MEAN | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_TOP3 | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_TOP3 | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_TOP3 | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | BM25_ALL_TOP3 | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAPH_TEXT | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAPH_TEXT | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAPH_TEXT | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | GRAPH_TEXT | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | HYBRID | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | HYBRID | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | HYBRID | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | HYBRID | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_ALL | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_ALL | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_ALL | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_ALL | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_BM25 | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_BM25 | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_BM25 | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_BM25 | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_GRAPH | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_GRAPH | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_GRAPH | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_GRAPH | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_LEXICAL | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_LEXICAL | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_LEXICAL | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_LEXICAL | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_LEXICAL_GRAPH | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_LEXICAL_GRAPH | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_LEXICAL_GRAPH | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_LEXICAL_GRAPH | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_SCHEMA_PARAM | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_SCHEMA_PARAM | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_SCHEMA_PARAM | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | LEARNED_SCHEMA_PARAM | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_MEAN | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_MEAN | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_MEAN | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_MEAN | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_TOP3 | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_TOP3 | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_TOP3 | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ALL_TOP3 | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ENDPOINT | 1 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ENDPOINT | 3 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ENDPOINT | 5 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:customers | RAG_ENDPOINT | 10 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_MEAN | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_MEAN | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_MEAN | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_MEAN | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_TOP3 | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_TOP3 | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_TOP3 | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | BM25_ALL_TOP3 | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAPH_TEXT | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAPH_TEXT | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAPH_TEXT | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | GRAPH_TEXT | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | HYBRID | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | HYBRID | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | HYBRID | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | HYBRID | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_ALL | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_ALL | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_ALL | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_ALL | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_BM25 | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_BM25 | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_BM25 | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_BM25 | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_GRAPH | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_GRAPH | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_GRAPH | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_GRAPH | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_LEXICAL | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_LEXICAL | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_LEXICAL | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_LEXICAL | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_LEXICAL_GRAPH | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_LEXICAL_GRAPH | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_LEXICAL_GRAPH | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_LEXICAL_GRAPH | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_SCHEMA_PARAM | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_SCHEMA_PARAM | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_SCHEMA_PARAM | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | LEARNED_SCHEMA_PARAM | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_MEAN | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_MEAN | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_MEAN | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_MEAN | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_TOP3 | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_TOP3 | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_TOP3 | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ALL_TOP3 | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ENDPOINT | 1 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ENDPOINT | 3 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ENDPOINT | 5 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:fulfillment | RAG_ENDPOINT | 10 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_MEAN | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_MEAN | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_MEAN | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_MEAN | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_TOP3 | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_TOP3 | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_TOP3 | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | BM25_ALL_TOP3 | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAPH_TEXT | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAPH_TEXT | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAPH_TEXT | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | GRAPH_TEXT | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | HYBRID | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | HYBRID | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | HYBRID | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | HYBRID | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_ALL | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_ALL | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_ALL | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_ALL | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_BM25 | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_BM25 | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_BM25 | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_BM25 | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_GRAPH | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_GRAPH | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_GRAPH | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_GRAPH | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_LEXICAL | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_LEXICAL | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_LEXICAL | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_LEXICAL | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_LEXICAL_GRAPH | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_LEXICAL_GRAPH | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_LEXICAL_GRAPH | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_LEXICAL_GRAPH | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_SCHEMA_PARAM | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_SCHEMA_PARAM | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_SCHEMA_PARAM | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | LEARNED_SCHEMA_PARAM | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_MEAN | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_MEAN | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_MEAN | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_MEAN | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_TOP3 | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_TOP3 | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_TOP3 | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ALL_TOP3 | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ENDPOINT | 1 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ENDPOINT | 3 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ENDPOINT | 5 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:inventory | RAG_ENDPOINT | 10 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% | 0.00 |
| leave_domain_out:orders | BM25_ALL_MEAN | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_MEAN | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_MEAN | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_MEAN | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_TOP3 | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_TOP3 | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_TOP3 | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | BM25_ALL_TOP3 | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAPH_TEXT | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAPH_TEXT | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAPH_TEXT | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | GRAPH_TEXT | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | HYBRID | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | HYBRID | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | HYBRID | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | HYBRID | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_ALL | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_ALL | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_ALL | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_ALL | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_BM25 | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_BM25 | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_BM25 | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_BM25 | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_GRAPH | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_GRAPH | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_GRAPH | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_GRAPH | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_LEXICAL | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_LEXICAL | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_LEXICAL | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_LEXICAL | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_LEXICAL_GRAPH | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_LEXICAL_GRAPH | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_LEXICAL_GRAPH | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_LEXICAL_GRAPH | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_SCHEMA_PARAM | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_SCHEMA_PARAM | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_SCHEMA_PARAM | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | LEARNED_SCHEMA_PARAM | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_MEAN | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_MEAN | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_MEAN | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_MEAN | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_TOP3 | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_TOP3 | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_TOP3 | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ALL_TOP3 | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ENDPOINT | 1 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ENDPOINT | 3 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ENDPOINT | 5 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:orders | RAG_ENDPOINT | 10 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% | 0.00 |
| leave_domain_out:payments | BM25_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | BM25_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAPH_TEXT | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAPH_TEXT | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAPH_TEXT | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | GRAPH_TEXT | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | HYBRID | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | HYBRID | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | HYBRID | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | HYBRID | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_ALL | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_ALL | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_ALL | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_ALL | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_BM25 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_BM25 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_BM25 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_BM25 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_LEXICAL | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_LEXICAL | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_LEXICAL | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_LEXICAL | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_LEXICAL_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_LEXICAL_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_LEXICAL_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_LEXICAL_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_SCHEMA_PARAM | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_SCHEMA_PARAM | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_SCHEMA_PARAM | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | LEARNED_SCHEMA_PARAM | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ENDPOINT | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ENDPOINT | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ENDPOINT | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:payments | RAG_ENDPOINT | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | BM25_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAPH_TEXT | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAPH_TEXT | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAPH_TEXT | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | GRAPH_TEXT | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | HYBRID | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | HYBRID | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | HYBRID | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | HYBRID | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_ALL | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_ALL | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_ALL | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_ALL | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_BM25 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_BM25 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_BM25 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_BM25 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_LEXICAL | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_LEXICAL | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_LEXICAL | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_LEXICAL | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_LEXICAL_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_LEXICAL_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_LEXICAL_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_LEXICAL_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_SCHEMA_PARAM | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_SCHEMA_PARAM | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_SCHEMA_PARAM | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | LEARNED_SCHEMA_PARAM | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ENDPOINT | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ENDPOINT | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ENDPOINT | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:products | RAG_ENDPOINT | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | BM25_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAPH_TEXT | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAPH_TEXT | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAPH_TEXT | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | GRAPH_TEXT | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | HYBRID | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | HYBRID | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | HYBRID | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | HYBRID | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_ALL | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_ALL | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_ALL | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_ALL | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_BM25 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_BM25 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_BM25 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_BM25 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_LEXICAL | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_LEXICAL | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_LEXICAL | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_LEXICAL | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_LEXICAL_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_LEXICAL_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_LEXICAL_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_LEXICAL_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_SCHEMA_PARAM | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_SCHEMA_PARAM | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_SCHEMA_PARAM | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | LEARNED_SCHEMA_PARAM | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ENDPOINT | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ENDPOINT | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ENDPOINT | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:promotions | RAG_ENDPOINT | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | BM25_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAPH_TEXT | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAPH_TEXT | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAPH_TEXT | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | GRAPH_TEXT | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | HYBRID | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | HYBRID | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | HYBRID | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | HYBRID | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_ALL | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_ALL | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_ALL | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_ALL | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_BM25 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_BM25 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_BM25 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_BM25 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_LEXICAL | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_LEXICAL | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_LEXICAL | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_LEXICAL | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_LEXICAL_GRAPH | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_LEXICAL_GRAPH | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_LEXICAL_GRAPH | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_LEXICAL_GRAPH | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_SCHEMA_PARAM | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_SCHEMA_PARAM | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_SCHEMA_PARAM | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | LEARNED_SCHEMA_PARAM | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_MEAN | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_MEAN | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_MEAN | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_MEAN | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_TOP3 | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_TOP3 | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_TOP3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ALL_TOP3 | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ENDPOINT | 1 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ENDPOINT | 3 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ENDPOINT | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| leave_domain_out:returns | RAG_ENDPOINT | 10 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% | 0.00 |
| test | BM25_ALL_MEAN | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_MEAN | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_MEAN | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_MEAN | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_TOP3 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_TOP3 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_TOP3 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | BM25_ALL_TOP3 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAPH_TEXT | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAPH_TEXT | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAPH_TEXT | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | GRAPH_TEXT | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | HYBRID | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | HYBRID | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | HYBRID | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | HYBRID | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_ALL | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_ALL | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_ALL | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_ALL | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_BM25 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_BM25 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_BM25 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_BM25 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_GRAPH | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_GRAPH | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_GRAPH | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_GRAPH | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_LEXICAL | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_LEXICAL | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_LEXICAL | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_LEXICAL | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_LEXICAL_GRAPH | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_LEXICAL_GRAPH | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_LEXICAL_GRAPH | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_LEXICAL_GRAPH | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_SCHEMA_PARAM | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_SCHEMA_PARAM | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_SCHEMA_PARAM | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | LEARNED_SCHEMA_PARAM | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_MEAN | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_MEAN | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_MEAN | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_MEAN | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_TOP3 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_TOP3 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_TOP3 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ALL_TOP3 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ENDPOINT | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ENDPOINT | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ENDPOINT | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| test | RAG_ENDPOINT | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% | 0.00 |
| train | BM25_ALL_MEAN | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_MEAN | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_MEAN | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_MEAN | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_TOP3 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_TOP3 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_TOP3 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | BM25_ALL_TOP3 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAPH_TEXT | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAPH_TEXT | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAPH_TEXT | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | GRAPH_TEXT | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | HYBRID | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | HYBRID | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | HYBRID | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | HYBRID | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_ALL | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_ALL | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_ALL | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_ALL | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_BM25 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_BM25 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_BM25 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_BM25 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_GRAPH | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_GRAPH | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_GRAPH | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_GRAPH | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_LEXICAL | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_LEXICAL | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_LEXICAL | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_LEXICAL | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_LEXICAL_GRAPH | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_LEXICAL_GRAPH | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_LEXICAL_GRAPH | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_LEXICAL_GRAPH | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_SCHEMA_PARAM | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_SCHEMA_PARAM | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_SCHEMA_PARAM | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | LEARNED_SCHEMA_PARAM | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_MEAN | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_MEAN | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_MEAN | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_MEAN | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_TOP3 | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_TOP3 | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_TOP3 | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ALL_TOP3 | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ENDPOINT | 1 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ENDPOINT | 3 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ENDPOINT | 5 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |
| train | RAG_ENDPOINT | 10 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% | 0.00 |

## Metrics By Leakage Bucket

| Split | Bucket | Baseline | k | Tasks | Complete | Routing@1 | Routing@10 | Ambiguous Abstain | Policy Abstain | Macro Track | Required Params | Validation |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | low | BM25_ALL_MAX | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | BM25_ALL_MAX | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | BM25_ALL_MAX | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | BM25_ALL_MAX | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | BM25_ALL_MAX | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | BM25_ALL_MAX | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | BM25_ALL_MAX | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | BM25_ALL_MAX | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | BM25_ALL_MAX | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | BM25_ALL_MAX | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | BM25_ALL_MAX | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | BM25_ALL_MAX | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_MAX | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_MAX | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_MAX | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_MAX | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | BM25_ALL_MAX | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | BM25_ALL_MAX | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | BM25_ALL_MAX | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | BM25_ALL_MAX | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | BM25_ALL_MAX | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | BM25_ALL_MAX | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | BM25_ALL_MAX | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | BM25_ALL_MAX | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_MAX | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_MAX | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_MAX | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_MAX | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_MAX | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_MAX | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_MAX | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_MAX | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | BM25_ALL_MAX | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | BM25_ALL_MAX | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | BM25_ALL_MAX | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | BM25_ALL_MAX | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | BM25_ALL_MAX | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | BM25_ALL_MAX | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | BM25_ALL_MAX | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | BM25_ALL_MAX | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | BM25_ALL_MAX | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | BM25_ALL_MAX | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | BM25_ALL_MAX | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | BM25_ALL_MAX | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | BM25_ALL_MAX | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | BM25_ALL_MAX | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | BM25_ALL_MAX | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | BM25_ALL_MAX | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | BM25_ALL_MAX | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | BM25_ALL_MAX | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | BM25_ALL_MAX | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | BM25_ALL_MAX | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_MAX | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_MAX | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_MAX | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_MAX | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_MAX | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_MAX | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_MAX | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_MAX | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_MAX | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_MAX | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_MAX | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_MAX | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | BM25_ALL_MAX | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | BM25_ALL_MAX | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | BM25_ALL_MAX | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | BM25_ALL_MAX | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | BM25_ALL_MAX | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | BM25_ALL_MAX | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | BM25_ALL_MAX | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | BM25_ALL_MAX | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | BM25_ALL_MEAN | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | BM25_ALL_MEAN | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | BM25_ALL_MEAN | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | BM25_ALL_MEAN | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | BM25_ALL_MEAN | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | BM25_ALL_MEAN | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | BM25_ALL_MEAN | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | BM25_ALL_MEAN | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | BM25_ALL_MEAN | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | BM25_ALL_MEAN | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | BM25_ALL_MEAN | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | BM25_ALL_MEAN | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_MEAN | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_MEAN | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_MEAN | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_MEAN | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | BM25_ALL_MEAN | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | BM25_ALL_MEAN | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | BM25_ALL_MEAN | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | BM25_ALL_MEAN | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | BM25_ALL_MEAN | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | BM25_ALL_MEAN | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | BM25_ALL_MEAN | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | BM25_ALL_MEAN | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_MEAN | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_MEAN | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_MEAN | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_MEAN | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_MEAN | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_MEAN | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_MEAN | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_MEAN | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | BM25_ALL_MEAN | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | BM25_ALL_MEAN | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | BM25_ALL_MEAN | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | BM25_ALL_MEAN | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | BM25_ALL_MEAN | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | BM25_ALL_MEAN | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | BM25_ALL_MEAN | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | BM25_ALL_MEAN | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | BM25_ALL_MEAN | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | BM25_ALL_MEAN | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | BM25_ALL_MEAN | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | BM25_ALL_MEAN | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | BM25_ALL_MEAN | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | BM25_ALL_MEAN | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | BM25_ALL_MEAN | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | BM25_ALL_MEAN | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | BM25_ALL_MEAN | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | BM25_ALL_MEAN | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | BM25_ALL_MEAN | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | BM25_ALL_MEAN | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_MEAN | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_MEAN | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_MEAN | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_MEAN | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_MEAN | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_MEAN | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_MEAN | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_MEAN | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_MEAN | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_MEAN | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_MEAN | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_MEAN | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | BM25_ALL_MEAN | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | BM25_ALL_MEAN | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | BM25_ALL_MEAN | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | BM25_ALL_MEAN | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | BM25_ALL_MEAN | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | BM25_ALL_MEAN | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | BM25_ALL_MEAN | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | BM25_ALL_MEAN | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | BM25_ALL_TOP3 | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | BM25_ALL_TOP3 | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | BM25_ALL_TOP3 | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | BM25_ALL_TOP3 | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | BM25_ALL_TOP3 | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | BM25_ALL_TOP3 | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | BM25_ALL_TOP3 | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | BM25_ALL_TOP3 | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | BM25_ALL_TOP3 | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | BM25_ALL_TOP3 | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | BM25_ALL_TOP3 | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | BM25_ALL_TOP3 | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_TOP3 | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_TOP3 | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_TOP3 | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | BM25_ALL_TOP3 | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | BM25_ALL_TOP3 | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | BM25_ALL_TOP3 | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | BM25_ALL_TOP3 | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | BM25_ALL_TOP3 | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | BM25_ALL_TOP3 | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | BM25_ALL_TOP3 | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | BM25_ALL_TOP3 | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | BM25_ALL_TOP3 | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_TOP3 | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_TOP3 | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_TOP3 | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | BM25_ALL_TOP3 | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_TOP3 | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_TOP3 | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_TOP3 | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | BM25_ALL_TOP3 | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | BM25_ALL_TOP3 | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | BM25_ALL_TOP3 | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | BM25_ALL_TOP3 | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | BM25_ALL_TOP3 | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | BM25_ALL_TOP3 | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | BM25_ALL_TOP3 | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | BM25_ALL_TOP3 | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | BM25_ALL_TOP3 | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | BM25_ALL_TOP3 | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | BM25_ALL_TOP3 | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | BM25_ALL_TOP3 | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | BM25_ALL_TOP3 | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | BM25_ALL_TOP3 | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | BM25_ALL_TOP3 | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | BM25_ALL_TOP3 | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | BM25_ALL_TOP3 | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | BM25_ALL_TOP3 | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | BM25_ALL_TOP3 | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | BM25_ALL_TOP3 | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | BM25_ALL_TOP3 | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_TOP3 | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_TOP3 | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_TOP3 | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | BM25_ALL_TOP3 | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_TOP3 | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_TOP3 | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_TOP3 | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | BM25_ALL_TOP3 | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_TOP3 | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_TOP3 | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_TOP3 | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | BM25_ALL_TOP3 | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | BM25_ALL_TOP3 | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | BM25_ALL_TOP3 | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | BM25_ALL_TOP3 | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | BM25_ALL_TOP3 | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | BM25_ALL_TOP3 | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | BM25_ALL_TOP3 | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | BM25_ALL_TOP3 | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | BM25_ALL_TOP3 | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | GRAG_CONSTRAINED | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAG_CONSTRAINED | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAG_CONSTRAINED | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAG_CONSTRAINED | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | GRAG_CONSTRAINED | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAG_CONSTRAINED | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAG_CONSTRAINED | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAG_CONSTRAINED | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | GRAG_CONSTRAINED | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAG_CONSTRAINED | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAG_CONSTRAINED | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAG_CONSTRAINED | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_CONSTRAINED | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_CONSTRAINED | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_CONSTRAINED | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_CONSTRAINED | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | GRAG_CONSTRAINED | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAG_CONSTRAINED | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAG_CONSTRAINED | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAG_CONSTRAINED | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | GRAG_CONSTRAINED | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAG_CONSTRAINED | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAG_CONSTRAINED | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAG_CONSTRAINED | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_CONSTRAINED | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_CONSTRAINED | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_CONSTRAINED | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_CONSTRAINED | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_CONSTRAINED | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_CONSTRAINED | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_CONSTRAINED | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_CONSTRAINED | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | GRAG_CONSTRAINED | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAG_CONSTRAINED | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAG_CONSTRAINED | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAG_CONSTRAINED | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | GRAG_CONSTRAINED | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAG_CONSTRAINED | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAG_CONSTRAINED | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAG_CONSTRAINED | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | GRAG_CONSTRAINED | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAG_CONSTRAINED | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAG_CONSTRAINED | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAG_CONSTRAINED | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | GRAG_CONSTRAINED | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAG_CONSTRAINED | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAG_CONSTRAINED | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAG_CONSTRAINED | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | GRAG_CONSTRAINED | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAG_CONSTRAINED | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAG_CONSTRAINED | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAG_CONSTRAINED | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_CONSTRAINED | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_CONSTRAINED | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_CONSTRAINED | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_CONSTRAINED | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_CONSTRAINED | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_CONSTRAINED | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_CONSTRAINED | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_CONSTRAINED | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_CONSTRAINED | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_CONSTRAINED | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_CONSTRAINED | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_CONSTRAINED | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | GRAG_CONSTRAINED | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAG_CONSTRAINED | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAG_CONSTRAINED | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAG_CONSTRAINED | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | GRAG_CONSTRAINED | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAG_CONSTRAINED | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAG_CONSTRAINED | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAG_CONSTRAINED | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | GRAG_EXPAND | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAG_EXPAND | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAG_EXPAND | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAG_EXPAND | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | GRAG_EXPAND | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAG_EXPAND | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAG_EXPAND | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAG_EXPAND | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | GRAG_EXPAND | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAG_EXPAND | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAG_EXPAND | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAG_EXPAND | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_EXPAND | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_EXPAND | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_EXPAND | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_EXPAND | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | GRAG_EXPAND | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAG_EXPAND | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAG_EXPAND | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAG_EXPAND | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | GRAG_EXPAND | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAG_EXPAND | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAG_EXPAND | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAG_EXPAND | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_EXPAND | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_EXPAND | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_EXPAND | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_EXPAND | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_EXPAND | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_EXPAND | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_EXPAND | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_EXPAND | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | GRAG_EXPAND | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAG_EXPAND | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAG_EXPAND | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAG_EXPAND | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | GRAG_EXPAND | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAG_EXPAND | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAG_EXPAND | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAG_EXPAND | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | GRAG_EXPAND | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAG_EXPAND | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAG_EXPAND | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAG_EXPAND | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | GRAG_EXPAND | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAG_EXPAND | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAG_EXPAND | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAG_EXPAND | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | GRAG_EXPAND | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAG_EXPAND | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAG_EXPAND | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAG_EXPAND | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_EXPAND | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_EXPAND | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_EXPAND | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_EXPAND | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_EXPAND | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_EXPAND | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_EXPAND | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_EXPAND | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_EXPAND | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_EXPAND | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_EXPAND | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_EXPAND | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | GRAG_EXPAND | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAG_EXPAND | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAG_EXPAND | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAG_EXPAND | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | GRAG_EXPAND | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAG_EXPAND | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAG_EXPAND | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAG_EXPAND | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | GRAG_RERANK | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAG_RERANK | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAG_RERANK | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAG_RERANK | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | GRAG_RERANK | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAG_RERANK | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAG_RERANK | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAG_RERANK | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | GRAG_RERANK | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAG_RERANK | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAG_RERANK | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAG_RERANK | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_RERANK | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_RERANK | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_RERANK | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAG_RERANK | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | GRAG_RERANK | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAG_RERANK | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAG_RERANK | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAG_RERANK | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | GRAG_RERANK | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAG_RERANK | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAG_RERANK | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAG_RERANK | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_RERANK | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_RERANK | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_RERANK | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAG_RERANK | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_RERANK | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_RERANK | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_RERANK | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAG_RERANK | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | GRAG_RERANK | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAG_RERANK | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAG_RERANK | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAG_RERANK | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | GRAG_RERANK | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAG_RERANK | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAG_RERANK | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAG_RERANK | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | GRAG_RERANK | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAG_RERANK | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAG_RERANK | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAG_RERANK | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | GRAG_RERANK | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAG_RERANK | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAG_RERANK | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAG_RERANK | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | GRAG_RERANK | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAG_RERANK | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAG_RERANK | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAG_RERANK | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_RERANK | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_RERANK | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_RERANK | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAG_RERANK | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_RERANK | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_RERANK | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_RERANK | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAG_RERANK | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_RERANK | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_RERANK | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_RERANK | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAG_RERANK | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | GRAG_RERANK | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAG_RERANK | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAG_RERANK | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAG_RERANK | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | GRAG_RERANK | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAG_RERANK | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAG_RERANK | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAG_RERANK | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | GRAPH_SPARSE | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAPH_SPARSE | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAPH_SPARSE | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAPH_SPARSE | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | GRAPH_SPARSE | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAPH_SPARSE | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAPH_SPARSE | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAPH_SPARSE | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | GRAPH_SPARSE | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAPH_SPARSE | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAPH_SPARSE | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAPH_SPARSE | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAPH_SPARSE | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAPH_SPARSE | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAPH_SPARSE | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAPH_SPARSE | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | GRAPH_SPARSE | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAPH_SPARSE | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAPH_SPARSE | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAPH_SPARSE | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | GRAPH_SPARSE | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAPH_SPARSE | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAPH_SPARSE | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAPH_SPARSE | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAPH_SPARSE | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAPH_SPARSE | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAPH_SPARSE | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAPH_SPARSE | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAPH_SPARSE | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAPH_SPARSE | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAPH_SPARSE | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAPH_SPARSE | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | GRAPH_SPARSE | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAPH_SPARSE | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAPH_SPARSE | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAPH_SPARSE | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | GRAPH_SPARSE | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAPH_SPARSE | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAPH_SPARSE | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAPH_SPARSE | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | GRAPH_SPARSE | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAPH_SPARSE | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAPH_SPARSE | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAPH_SPARSE | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | GRAPH_SPARSE | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAPH_SPARSE | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAPH_SPARSE | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAPH_SPARSE | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | GRAPH_SPARSE | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAPH_SPARSE | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAPH_SPARSE | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAPH_SPARSE | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAPH_SPARSE | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAPH_SPARSE | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAPH_SPARSE | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAPH_SPARSE | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAPH_SPARSE | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAPH_SPARSE | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAPH_SPARSE | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAPH_SPARSE | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAPH_SPARSE | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAPH_SPARSE | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAPH_SPARSE | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAPH_SPARSE | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | GRAPH_SPARSE | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAPH_SPARSE | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAPH_SPARSE | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAPH_SPARSE | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | GRAPH_SPARSE | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAPH_SPARSE | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAPH_SPARSE | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAPH_SPARSE | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | GRAPH_TEXT | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAPH_TEXT | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAPH_TEXT | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | GRAPH_TEXT | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | GRAPH_TEXT | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAPH_TEXT | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAPH_TEXT | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | GRAPH_TEXT | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | GRAPH_TEXT | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAPH_TEXT | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAPH_TEXT | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | GRAPH_TEXT | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAPH_TEXT | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAPH_TEXT | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAPH_TEXT | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | GRAPH_TEXT | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | GRAPH_TEXT | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAPH_TEXT | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAPH_TEXT | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | GRAPH_TEXT | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | GRAPH_TEXT | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAPH_TEXT | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAPH_TEXT | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | GRAPH_TEXT | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAPH_TEXT | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAPH_TEXT | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAPH_TEXT | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | GRAPH_TEXT | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAPH_TEXT | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAPH_TEXT | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAPH_TEXT | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | GRAPH_TEXT | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | GRAPH_TEXT | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAPH_TEXT | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAPH_TEXT | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | GRAPH_TEXT | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | GRAPH_TEXT | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAPH_TEXT | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAPH_TEXT | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | GRAPH_TEXT | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | GRAPH_TEXT | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAPH_TEXT | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAPH_TEXT | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | GRAPH_TEXT | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | GRAPH_TEXT | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAPH_TEXT | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAPH_TEXT | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | GRAPH_TEXT | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | GRAPH_TEXT | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAPH_TEXT | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAPH_TEXT | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | GRAPH_TEXT | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAPH_TEXT | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAPH_TEXT | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAPH_TEXT | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | GRAPH_TEXT | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAPH_TEXT | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAPH_TEXT | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAPH_TEXT | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | GRAPH_TEXT | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAPH_TEXT | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAPH_TEXT | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAPH_TEXT | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | GRAPH_TEXT | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | GRAPH_TEXT | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAPH_TEXT | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAPH_TEXT | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | GRAPH_TEXT | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | GRAPH_TEXT | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAPH_TEXT | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAPH_TEXT | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | GRAPH_TEXT | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | HYBRID | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | HYBRID | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | HYBRID | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | HYBRID | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | HYBRID | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | HYBRID | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | HYBRID | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | HYBRID | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | HYBRID | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | HYBRID | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | HYBRID | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | HYBRID | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | HYBRID | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | HYBRID | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | HYBRID | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | HYBRID | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | HYBRID | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | HYBRID | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | HYBRID | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | HYBRID | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | HYBRID | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | HYBRID | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | HYBRID | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | HYBRID | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | HYBRID | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | HYBRID | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | HYBRID | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | HYBRID | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | HYBRID | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | HYBRID | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | HYBRID | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | HYBRID | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | HYBRID | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | HYBRID | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | HYBRID | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | HYBRID | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | HYBRID | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | HYBRID | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | HYBRID | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | HYBRID | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | HYBRID | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | HYBRID | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | HYBRID | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | HYBRID | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | HYBRID | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | HYBRID | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | HYBRID | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | HYBRID | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | HYBRID | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | HYBRID | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | HYBRID | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | HYBRID | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | HYBRID | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | HYBRID | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | HYBRID | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | HYBRID | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | HYBRID | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | HYBRID | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | HYBRID | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | HYBRID | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | HYBRID | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | HYBRID | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | HYBRID | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | HYBRID | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | HYBRID | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | HYBRID | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | HYBRID | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | HYBRID | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | HYBRID | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | HYBRID | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | HYBRID | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | HYBRID | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | LEARNED | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | LEARNED | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | LEARNED | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | LEARNED | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | LEARNED | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | LEARNED | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | LEARNED | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | LEARNED | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | LEARNED | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | LEARNED | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | LEARNED | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | LEARNED | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | LEARNED_ALL | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_ALL | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_ALL | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_ALL | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | LEARNED_ALL | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_ALL | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_ALL | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_ALL | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | LEARNED_ALL | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_ALL | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_ALL | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_ALL | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_ALL | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_ALL | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_ALL | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_ALL | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | LEARNED_ALL | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_ALL | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_ALL | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_ALL | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | LEARNED_ALL | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_ALL | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_ALL | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_ALL | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_ALL | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_ALL | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_ALL | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_ALL | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_ALL | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_ALL | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_ALL | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_ALL | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | LEARNED_ALL | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_ALL | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_ALL | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_ALL | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | LEARNED_ALL | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_ALL | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_ALL | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_ALL | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | LEARNED_ALL | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_ALL | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_ALL | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_ALL | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | LEARNED_ALL | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_ALL | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_ALL | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_ALL | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | LEARNED_ALL | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_ALL | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_ALL | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_ALL | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_ALL | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_ALL | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_ALL | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_ALL | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_ALL | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_ALL | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_ALL | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_ALL | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_ALL | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_ALL | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_ALL | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_ALL | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | LEARNED_ALL | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_ALL | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_ALL | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_ALL | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | LEARNED_ALL | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_ALL | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_ALL | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_ALL | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | LEARNED_BM25 | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_BM25 | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_BM25 | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_BM25 | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | LEARNED_BM25 | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_BM25 | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_BM25 | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_BM25 | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | LEARNED_BM25 | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_BM25 | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_BM25 | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_BM25 | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_BM25 | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_BM25 | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_BM25 | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_BM25 | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | LEARNED_BM25 | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_BM25 | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_BM25 | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_BM25 | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | LEARNED_BM25 | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_BM25 | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_BM25 | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_BM25 | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_BM25 | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_BM25 | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_BM25 | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_BM25 | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_BM25 | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_BM25 | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_BM25 | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_BM25 | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | LEARNED_BM25 | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_BM25 | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_BM25 | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_BM25 | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | LEARNED_BM25 | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_BM25 | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_BM25 | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_BM25 | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | LEARNED_BM25 | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_BM25 | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_BM25 | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_BM25 | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | LEARNED_BM25 | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_BM25 | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_BM25 | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_BM25 | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | LEARNED_BM25 | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_BM25 | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_BM25 | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_BM25 | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_BM25 | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_BM25 | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_BM25 | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_BM25 | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_BM25 | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_BM25 | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_BM25 | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_BM25 | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_BM25 | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_BM25 | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_BM25 | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_BM25 | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | LEARNED_BM25 | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_BM25 | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_BM25 | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_BM25 | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | LEARNED_BM25 | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_BM25 | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_BM25 | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_BM25 | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | LEARNED_GRAPH | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_GRAPH | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_GRAPH | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_GRAPH | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | LEARNED_GRAPH | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_GRAPH | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_GRAPH | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_GRAPH | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | LEARNED_GRAPH | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_GRAPH | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_GRAPH | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_GRAPH | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_GRAPH | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_GRAPH | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_GRAPH | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_GRAPH | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | LEARNED_GRAPH | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_GRAPH | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_GRAPH | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_GRAPH | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | LEARNED_GRAPH | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_GRAPH | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_GRAPH | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_GRAPH | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_GRAPH | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_GRAPH | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_GRAPH | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_GRAPH | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_GRAPH | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_GRAPH | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_GRAPH | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_GRAPH | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | LEARNED_GRAPH | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_GRAPH | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_GRAPH | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_GRAPH | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | LEARNED_GRAPH | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_GRAPH | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_GRAPH | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_GRAPH | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | LEARNED_GRAPH | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_GRAPH | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_GRAPH | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_GRAPH | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | LEARNED_GRAPH | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_GRAPH | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_GRAPH | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_GRAPH | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | LEARNED_GRAPH | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_GRAPH | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_GRAPH | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_GRAPH | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_GRAPH | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_GRAPH | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_GRAPH | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_GRAPH | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_GRAPH | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_GRAPH | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_GRAPH | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_GRAPH | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_GRAPH | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_GRAPH | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_GRAPH | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_GRAPH | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | LEARNED_GRAPH | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_GRAPH | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_GRAPH | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_GRAPH | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | LEARNED_GRAPH | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_GRAPH | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_GRAPH | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_GRAPH | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | LEARNED_LEXICAL | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_LEXICAL | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_LEXICAL | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_LEXICAL | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | LEARNED_LEXICAL | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_LEXICAL | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_LEXICAL | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_LEXICAL | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | LEARNED_LEXICAL | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_LEXICAL | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_LEXICAL | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_LEXICAL | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_LEXICAL | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_LEXICAL | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_LEXICAL | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_LEXICAL | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | LEARNED_LEXICAL | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_LEXICAL | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_LEXICAL | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_LEXICAL | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | LEARNED_LEXICAL | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_LEXICAL | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_LEXICAL | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_LEXICAL | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_LEXICAL | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_LEXICAL | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_LEXICAL | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_LEXICAL | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_LEXICAL | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_LEXICAL | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_LEXICAL | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_LEXICAL | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | LEARNED_LEXICAL | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_LEXICAL | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_LEXICAL | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_LEXICAL | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | LEARNED_LEXICAL | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_LEXICAL | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_LEXICAL | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_LEXICAL | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | LEARNED_LEXICAL | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_LEXICAL | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_LEXICAL | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_LEXICAL | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | LEARNED_LEXICAL | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_LEXICAL | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_LEXICAL | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_LEXICAL | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | LEARNED_LEXICAL | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_LEXICAL | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_LEXICAL | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_LEXICAL | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_LEXICAL | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_LEXICAL | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_LEXICAL | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_LEXICAL | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_LEXICAL | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_LEXICAL | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_LEXICAL | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_LEXICAL | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_LEXICAL | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_LEXICAL | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_LEXICAL | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_LEXICAL | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | LEARNED_LEXICAL | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_LEXICAL | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_LEXICAL | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_LEXICAL | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | LEARNED_LEXICAL | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_LEXICAL | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_LEXICAL | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_LEXICAL | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | LEARNED_LEXICAL_GRAPH | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_LEXICAL_GRAPH | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_LEXICAL_GRAPH | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_LEXICAL_GRAPH | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | LEARNED_LEXICAL_GRAPH | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_LEXICAL_GRAPH | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_LEXICAL_GRAPH | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_LEXICAL_GRAPH | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | LEARNED_LEXICAL_GRAPH | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_LEXICAL_GRAPH | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_LEXICAL_GRAPH | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_LEXICAL_GRAPH | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_LEXICAL_GRAPH | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_LEXICAL_GRAPH | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_LEXICAL_GRAPH | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_LEXICAL_GRAPH | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | LEARNED_LEXICAL_GRAPH | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_LEXICAL_GRAPH | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_LEXICAL_GRAPH | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_LEXICAL_GRAPH | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | LEARNED_LEXICAL_GRAPH | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_LEXICAL_GRAPH | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_LEXICAL_GRAPH | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_LEXICAL_GRAPH | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_LEXICAL_GRAPH | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_LEXICAL_GRAPH | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_LEXICAL_GRAPH | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_LEXICAL_GRAPH | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_LEXICAL_GRAPH | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_LEXICAL_GRAPH | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_LEXICAL_GRAPH | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_LEXICAL_GRAPH | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | LEARNED_LEXICAL_GRAPH | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_LEXICAL_GRAPH | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_LEXICAL_GRAPH | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_LEXICAL_GRAPH | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | LEARNED_LEXICAL_GRAPH | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_LEXICAL_GRAPH | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_LEXICAL_GRAPH | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_LEXICAL_GRAPH | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | LEARNED_LEXICAL_GRAPH | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_LEXICAL_GRAPH | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_LEXICAL_GRAPH | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_LEXICAL_GRAPH | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | LEARNED_LEXICAL_GRAPH | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_LEXICAL_GRAPH | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_LEXICAL_GRAPH | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_LEXICAL_GRAPH | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | LEARNED_LEXICAL_GRAPH | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_LEXICAL_GRAPH | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_LEXICAL_GRAPH | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_LEXICAL_GRAPH | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_LEXICAL_GRAPH | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_LEXICAL_GRAPH | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_LEXICAL_GRAPH | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_LEXICAL_GRAPH | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_LEXICAL_GRAPH | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_LEXICAL_GRAPH | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_LEXICAL_GRAPH | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_LEXICAL_GRAPH | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_LEXICAL_GRAPH | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_LEXICAL_GRAPH | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_LEXICAL_GRAPH | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_LEXICAL_GRAPH | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | LEARNED_LEXICAL_GRAPH | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_LEXICAL_GRAPH | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_LEXICAL_GRAPH | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_LEXICAL_GRAPH | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | LEARNED_LEXICAL_GRAPH | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_LEXICAL_GRAPH | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_LEXICAL_GRAPH | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_LEXICAL_GRAPH | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | LEARNED_SCHEMA_PARAM | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_SCHEMA_PARAM | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_SCHEMA_PARAM | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | LEARNED_SCHEMA_PARAM | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | LEARNED_SCHEMA_PARAM | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_SCHEMA_PARAM | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_SCHEMA_PARAM | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | LEARNED_SCHEMA_PARAM | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | LEARNED_SCHEMA_PARAM | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_SCHEMA_PARAM | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_SCHEMA_PARAM | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | LEARNED_SCHEMA_PARAM | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_SCHEMA_PARAM | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_SCHEMA_PARAM | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_SCHEMA_PARAM | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | LEARNED_SCHEMA_PARAM | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | LEARNED_SCHEMA_PARAM | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_SCHEMA_PARAM | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_SCHEMA_PARAM | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | LEARNED_SCHEMA_PARAM | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | LEARNED_SCHEMA_PARAM | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_SCHEMA_PARAM | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_SCHEMA_PARAM | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | LEARNED_SCHEMA_PARAM | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_SCHEMA_PARAM | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_SCHEMA_PARAM | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_SCHEMA_PARAM | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | LEARNED_SCHEMA_PARAM | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_SCHEMA_PARAM | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_SCHEMA_PARAM | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_SCHEMA_PARAM | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | LEARNED_SCHEMA_PARAM | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | LEARNED_SCHEMA_PARAM | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_SCHEMA_PARAM | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_SCHEMA_PARAM | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | LEARNED_SCHEMA_PARAM | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | LEARNED_SCHEMA_PARAM | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_SCHEMA_PARAM | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_SCHEMA_PARAM | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | LEARNED_SCHEMA_PARAM | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | LEARNED_SCHEMA_PARAM | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_SCHEMA_PARAM | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_SCHEMA_PARAM | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | LEARNED_SCHEMA_PARAM | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | LEARNED_SCHEMA_PARAM | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_SCHEMA_PARAM | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_SCHEMA_PARAM | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | LEARNED_SCHEMA_PARAM | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | LEARNED_SCHEMA_PARAM | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_SCHEMA_PARAM | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_SCHEMA_PARAM | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | LEARNED_SCHEMA_PARAM | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_SCHEMA_PARAM | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_SCHEMA_PARAM | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_SCHEMA_PARAM | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | LEARNED_SCHEMA_PARAM | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_SCHEMA_PARAM | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_SCHEMA_PARAM | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_SCHEMA_PARAM | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | LEARNED_SCHEMA_PARAM | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_SCHEMA_PARAM | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_SCHEMA_PARAM | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_SCHEMA_PARAM | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | LEARNED_SCHEMA_PARAM | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | LEARNED_SCHEMA_PARAM | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_SCHEMA_PARAM | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_SCHEMA_PARAM | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | LEARNED_SCHEMA_PARAM | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | LEARNED_SCHEMA_PARAM | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_SCHEMA_PARAM | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_SCHEMA_PARAM | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | LEARNED_SCHEMA_PARAM | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | RAG_ALL_MAX | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ALL_MAX | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ALL_MAX | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ALL_MAX | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | RAG_ALL_MAX | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ALL_MAX | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ALL_MAX | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ALL_MAX | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | RAG_ALL_MAX | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ALL_MAX | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ALL_MAX | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ALL_MAX | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_MAX | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_MAX | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_MAX | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_MAX | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | RAG_ALL_MAX | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ALL_MAX | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ALL_MAX | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ALL_MAX | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | RAG_ALL_MAX | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ALL_MAX | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ALL_MAX | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ALL_MAX | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_MAX | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_MAX | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_MAX | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_MAX | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_MAX | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_MAX | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_MAX | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_MAX | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | RAG_ALL_MAX | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ALL_MAX | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ALL_MAX | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ALL_MAX | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | RAG_ALL_MAX | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ALL_MAX | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ALL_MAX | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ALL_MAX | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | RAG_ALL_MAX | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ALL_MAX | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ALL_MAX | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ALL_MAX | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | RAG_ALL_MAX | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ALL_MAX | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ALL_MAX | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ALL_MAX | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | RAG_ALL_MAX | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ALL_MAX | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ALL_MAX | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ALL_MAX | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_MAX | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_MAX | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_MAX | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_MAX | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_MAX | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_MAX | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_MAX | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_MAX | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_MAX | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_MAX | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_MAX | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_MAX | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | RAG_ALL_MAX | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ALL_MAX | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ALL_MAX | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ALL_MAX | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | RAG_ALL_MAX | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ALL_MAX | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ALL_MAX | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ALL_MAX | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | RAG_ALL_MEAN | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ALL_MEAN | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ALL_MEAN | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ALL_MEAN | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | RAG_ALL_MEAN | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ALL_MEAN | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ALL_MEAN | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ALL_MEAN | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | RAG_ALL_MEAN | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ALL_MEAN | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ALL_MEAN | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ALL_MEAN | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_MEAN | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_MEAN | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_MEAN | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_MEAN | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | RAG_ALL_MEAN | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ALL_MEAN | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ALL_MEAN | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ALL_MEAN | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | RAG_ALL_MEAN | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ALL_MEAN | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ALL_MEAN | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ALL_MEAN | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_MEAN | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_MEAN | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_MEAN | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_MEAN | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_MEAN | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_MEAN | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_MEAN | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_MEAN | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | RAG_ALL_MEAN | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ALL_MEAN | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ALL_MEAN | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ALL_MEAN | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | RAG_ALL_MEAN | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ALL_MEAN | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ALL_MEAN | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ALL_MEAN | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | RAG_ALL_MEAN | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ALL_MEAN | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ALL_MEAN | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ALL_MEAN | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | RAG_ALL_MEAN | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ALL_MEAN | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ALL_MEAN | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ALL_MEAN | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | RAG_ALL_MEAN | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ALL_MEAN | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ALL_MEAN | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ALL_MEAN | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_MEAN | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_MEAN | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_MEAN | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_MEAN | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_MEAN | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_MEAN | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_MEAN | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_MEAN | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_MEAN | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_MEAN | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_MEAN | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_MEAN | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | RAG_ALL_MEAN | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ALL_MEAN | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ALL_MEAN | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ALL_MEAN | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | RAG_ALL_MEAN | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ALL_MEAN | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ALL_MEAN | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ALL_MEAN | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | RAG_ALL_TOP3 | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ALL_TOP3 | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ALL_TOP3 | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ALL_TOP3 | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | RAG_ALL_TOP3 | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ALL_TOP3 | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ALL_TOP3 | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ALL_TOP3 | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | RAG_ALL_TOP3 | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ALL_TOP3 | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ALL_TOP3 | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ALL_TOP3 | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_TOP3 | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_TOP3 | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_TOP3 | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ALL_TOP3 | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | RAG_ALL_TOP3 | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ALL_TOP3 | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ALL_TOP3 | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ALL_TOP3 | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | RAG_ALL_TOP3 | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ALL_TOP3 | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ALL_TOP3 | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ALL_TOP3 | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_TOP3 | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_TOP3 | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_TOP3 | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ALL_TOP3 | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_TOP3 | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_TOP3 | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_TOP3 | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ALL_TOP3 | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | RAG_ALL_TOP3 | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ALL_TOP3 | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ALL_TOP3 | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ALL_TOP3 | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | RAG_ALL_TOP3 | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ALL_TOP3 | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ALL_TOP3 | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ALL_TOP3 | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | RAG_ALL_TOP3 | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ALL_TOP3 | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ALL_TOP3 | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ALL_TOP3 | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | RAG_ALL_TOP3 | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ALL_TOP3 | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ALL_TOP3 | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ALL_TOP3 | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | RAG_ALL_TOP3 | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ALL_TOP3 | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ALL_TOP3 | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ALL_TOP3 | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_TOP3 | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_TOP3 | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_TOP3 | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ALL_TOP3 | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_TOP3 | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_TOP3 | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_TOP3 | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ALL_TOP3 | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_TOP3 | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_TOP3 | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_TOP3 | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ALL_TOP3 | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | RAG_ALL_TOP3 | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ALL_TOP3 | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ALL_TOP3 | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ALL_TOP3 | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | RAG_ALL_TOP3 | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ALL_TOP3 | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ALL_TOP3 | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ALL_TOP3 | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| all | low | RAG_ENDPOINT | 1 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ENDPOINT | 3 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ENDPOINT | 5 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| all | low | RAG_ENDPOINT | 10 | 200 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 56.0% | 50.0% |
| dev | low | RAG_ENDPOINT | 1 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ENDPOINT | 3 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ENDPOINT | 5 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| dev | low | RAG_ENDPOINT | 10 | 40 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 52.5% | 50.0% |
| leave_domain_out:api_keys | low | RAG_ENDPOINT | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ENDPOINT | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ENDPOINT | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:api_keys | low | RAG_ENDPOINT | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ENDPOINT | 1 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ENDPOINT | 3 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ENDPOINT | 5 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:auth | low | RAG_ENDPOINT | 10 | 11 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:carts | low | RAG_ENDPOINT | 1 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ENDPOINT | 3 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ENDPOINT | 5 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:carts | low | RAG_ENDPOINT | 10 | 29 | 55.2% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.2% | 55.2% |
| leave_domain_out:claims | low | RAG_ENDPOINT | 1 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ENDPOINT | 3 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ENDPOINT | 5 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:claims | low | RAG_ENDPOINT | 10 | 18 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ENDPOINT | 1 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ENDPOINT | 3 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ENDPOINT | 5 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:collections | low | RAG_ENDPOINT | 10 | 4 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ENDPOINT | 1 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ENDPOINT | 3 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ENDPOINT | 5 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | low | RAG_ENDPOINT | 10 | 3 | 100.0% | 0.0% | 0.0% | 100.0% | 0.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:customers | low | RAG_ENDPOINT | 1 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ENDPOINT | 3 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ENDPOINT | 5 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:customers | low | RAG_ENDPOINT | 10 | 36 | 13.9% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 25.0% | 13.9% |
| leave_domain_out:fulfillment | low | RAG_ENDPOINT | 1 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ENDPOINT | 3 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ENDPOINT | 5 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:fulfillment | low | RAG_ENDPOINT | 10 | 18 | 33.3% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 44.4% | 33.3% |
| leave_domain_out:inventory | low | RAG_ENDPOINT | 1 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ENDPOINT | 3 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ENDPOINT | 5 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:inventory | low | RAG_ENDPOINT | 10 | 16 | 31.2% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 31.2% |
| leave_domain_out:orders | low | RAG_ENDPOINT | 1 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ENDPOINT | 3 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ENDPOINT | 5 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:orders | low | RAG_ENDPOINT | 10 | 39 | 15.4% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 23.1% | 15.4% |
| leave_domain_out:payments | low | RAG_ENDPOINT | 1 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ENDPOINT | 3 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ENDPOINT | 5 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:payments | low | RAG_ENDPOINT | 10 | 5 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ENDPOINT | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ENDPOINT | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ENDPOINT | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:products | low | RAG_ENDPOINT | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ENDPOINT | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ENDPOINT | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ENDPOINT | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | low | RAG_ENDPOINT | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ENDPOINT | 1 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ENDPOINT | 3 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ENDPOINT | 5 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| leave_domain_out:returns | low | RAG_ENDPOINT | 10 | 6 | 100.0% | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 100.0% | 100.0% |
| test | low | RAG_ENDPOINT | 1 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ENDPOINT | 3 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ENDPOINT | 5 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| test | low | RAG_ENDPOINT | 10 | 38 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 55.3% | 50.0% |
| train | low | RAG_ENDPOINT | 1 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ENDPOINT | 3 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ENDPOINT | 5 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |
| train | low | RAG_ENDPOINT | 10 | 122 | 50.0% | 0.0% | 0.0% | 100.0% | 100.0% | 66.7% | 57.4% | 50.0% |

The benchmark uses official OpenAPI specs as the routing source of truth. Write operations are evaluated as dry-run schema/plan candidates only.