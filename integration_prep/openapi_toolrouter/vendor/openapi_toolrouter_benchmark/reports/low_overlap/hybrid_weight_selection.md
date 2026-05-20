# Hybrid Weight Selection

The reported hybrid baseline uses weights selected on the active dev rows only.

| Scope | Lexical | BM25 | Graph sparse | Param/schema | Dev Complete@1 | Dev Complete@10 | Held-out Complete@1 | Held-out Complete@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 1.00 | 0.00 | 0.00 | 0.00 | 50.0% | 50.0% | 50.0% | 50.0% |
| dev | 1.00 | 0.00 | 0.00 | 0.00 | 50.0% | 50.0% | 50.0% | 50.0% |
| leave_domain_out:api_keys | 1.00 | 0.00 | 0.00 | 0.00 | 73.7% | 73.7% | 100.0% | 100.0% |
| leave_domain_out:auth | 1.00 | 0.00 | 0.00 | 0.00 | 73.7% | 73.7% | 100.0% | 100.0% |
| leave_domain_out:carts | 1.00 | 0.00 | 0.00 | 0.00 | 76.5% | 76.5% | 55.2% | 55.2% |
| leave_domain_out:claims | 1.00 | 0.00 | 0.00 | 0.00 | 73.7% | 73.7% | 100.0% | 100.0% |
| leave_domain_out:collections | 1.00 | 0.00 | 0.00 | 0.00 | 73.7% | 73.7% | 100.0% | 100.0% |
| leave_domain_out:currencies | 1.00 | 0.00 | 0.00 | 0.00 | 73.7% | 73.7% | 100.0% | 100.0% |
| leave_domain_out:customers | 1.00 | 0.00 | 0.00 | 0.00 | 77.8% | 77.8% | 13.9% | 13.9% |
| leave_domain_out:fulfillment | 1.00 | 0.00 | 0.00 | 0.00 | 77.8% | 77.8% | 33.3% | 33.3% |
| leave_domain_out:inventory | 1.00 | 0.00 | 0.00 | 0.00 | 77.8% | 77.8% | 31.2% | 31.2% |
| leave_domain_out:orders | 1.00 | 0.00 | 0.00 | 0.00 | 77.8% | 77.8% | 15.4% | 15.4% |
| leave_domain_out:payments | 1.00 | 0.00 | 0.00 | 0.00 | 73.7% | 73.7% | 100.0% | 100.0% |
| leave_domain_out:products | 1.00 | 0.00 | 0.00 | 0.00 | 73.7% | 73.7% | 100.0% | 100.0% |
| leave_domain_out:promotions | 1.00 | 0.00 | 0.00 | 0.00 | 73.7% | 73.7% | 100.0% | 100.0% |
| leave_domain_out:returns | 1.00 | 0.00 | 0.00 | 0.00 | 73.7% | 73.7% | 100.0% | 100.0% |
| test | 1.00 | 0.00 | 0.00 | 0.00 | 50.0% | 50.0% | 50.0% | 50.0% |
| train | 1.00 | 0.00 | 0.00 | 0.00 | 50.0% | 50.0% | 50.0% | 50.0% |

## Selected Grid Rows

| Scope | Config | Threshold | Selected | Dev tasks | Complete@1 | Complete@10 | First-step@1 |
|---|---|---:|---|---:|---:|---:|---:|
| all | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 40 | 50.0% | 50.0% | 0.0% |
| train | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 40 | 50.0% | 50.0% | 0.0% |
| dev | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 40 | 50.0% | 50.0% | 0.0% |
| test | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 40 | 50.0% | 50.0% | 0.0% |
| leave_domain_out:api_keys | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 19 | 73.7% | 73.7% | 0.0% |
| leave_domain_out:auth | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 19 | 73.7% | 73.7% | 0.0% |
| leave_domain_out:carts | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 17 | 76.5% | 76.5% | 0.0% |
| leave_domain_out:claims | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 19 | 73.7% | 73.7% | 0.0% |
| leave_domain_out:collections | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 19 | 73.7% | 73.7% | 0.0% |
| leave_domain_out:currencies | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 19 | 73.7% | 73.7% | 0.0% |
| leave_domain_out:customers | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 18 | 77.8% | 77.8% | 0.0% |
| leave_domain_out:fulfillment | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 18 | 77.8% | 77.8% | 0.0% |
| leave_domain_out:inventory | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 18 | 77.8% | 77.8% | 0.0% |
| leave_domain_out:orders | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 18 | 77.8% | 77.8% | 0.0% |
| leave_domain_out:payments | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 19 | 73.7% | 73.7% | 0.0% |
| leave_domain_out:products | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 19 | 73.7% | 73.7% | 0.0% |
| leave_domain_out:promotions | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 19 | 73.7% | 73.7% | 0.0% |
| leave_domain_out:returns | lexical1.00_bm250.00_graph0.00_schema_param0.00 | 1.0000 | yes | 19 | 73.7% | 73.7% | 0.0% |