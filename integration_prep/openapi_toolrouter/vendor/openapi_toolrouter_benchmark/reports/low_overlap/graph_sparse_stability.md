# Graph Sparse Stability

Graph sparse configuration selection is performed from the active dev rows only for each evaluation scope.

## Selected Config Frequency

| Config | Count |
|---|---:|
| directed | 16 |
| seed_50 | 1 |
| weighted_structural | 1 |

## Selected Config By Scope

| Scope | Config | Seed top n | Steps | Damping | Directed | High-degree | Endpoint prior | Dev Complete@1 | Dev Complete@10 | Held-out Complete@1 | Held-out Complete@10 |
|---|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|
| all | directed | 200 | 3 | 0.85 | true | false | 0.00 | 37.5% | 45.0% | 50.0% | 50.0% |
| dev | directed | 200 | 3 | 0.85 | true | false | 0.00 | 37.5% | 45.0% | 50.0% | 50.0% |
| leave_domain_out:api_keys | directed | 200 | 3 | 0.85 | true | false | 0.00 | 26.3% | 26.3% | 100.0% | 100.0% |
| leave_domain_out:auth | directed | 200 | 3 | 0.85 | true | false | 0.00 | 26.3% | 26.3% | 100.0% | 100.0% |
| leave_domain_out:carts | seed_50 | 50 | 3 | 0.85 | false | false | 0.00 | 23.5% | 23.5% | 55.2% | 55.2% |
| leave_domain_out:claims | directed | 200 | 3 | 0.85 | true | false | 0.00 | 26.3% | 26.3% | 100.0% | 100.0% |
| leave_domain_out:collections | directed | 200 | 3 | 0.85 | true | false | 0.00 | 26.3% | 26.3% | 100.0% | 100.0% |
| leave_domain_out:currencies | directed | 200 | 3 | 0.85 | true | false | 0.00 | 26.3% | 26.3% | 100.0% | 100.0% |
| leave_domain_out:customers | weighted_structural | 200 | 3 | 0.85 | false | false | 0.00 | 22.2% | 22.2% | 13.9% | 13.9% |
| leave_domain_out:fulfillment | directed | 200 | 3 | 0.85 | true | false | 0.00 | 22.2% | 22.2% | 33.3% | 33.3% |
| leave_domain_out:inventory | directed | 200 | 3 | 0.85 | true | false | 0.00 | 22.2% | 22.2% | 31.2% | 31.2% |
| leave_domain_out:orders | directed | 200 | 3 | 0.85 | true | false | 0.00 | 22.2% | 22.2% | 15.4% | 15.4% |
| leave_domain_out:payments | directed | 200 | 3 | 0.85 | true | false | 0.00 | 26.3% | 26.3% | 100.0% | 100.0% |
| leave_domain_out:products | directed | 200 | 3 | 0.85 | true | false | 0.00 | 26.3% | 26.3% | 100.0% | 100.0% |
| leave_domain_out:promotions | directed | 200 | 3 | 0.85 | true | false | 0.00 | 26.3% | 26.3% | 100.0% | 100.0% |
| leave_domain_out:returns | directed | 200 | 3 | 0.85 | true | false | 0.00 | 26.3% | 26.3% | 100.0% | 100.0% |
| test | directed | 200 | 3 | 0.85 | true | false | 0.00 | 37.5% | 45.0% | 50.0% | 50.0% |
| train | directed | 200 | 3 | 0.85 | true | false | 0.00 | 37.5% | 45.0% | 50.0% | 50.0% |

## Resource-Wise Graph Sparse Comparison

| Split | Resource | Comparator | Outcome | Complete@1 Delta | Complete@10 Delta | First-step@1 Delta | Validation Delta |
|---|---|---|---|---:|---:|---:|---:|
| all | api_keys | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | auth | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | carts | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | claims | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | collections | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | currencies | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | customers | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | fulfillment | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | inventory | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | orders | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | payments | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | products | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | promotions | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | returns | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | api_keys | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | auth | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | carts | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | claims | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | collections | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | currencies | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | customers | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | fulfillment | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | inventory | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | orders | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | payments | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | products | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | promotions | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | returns | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:api_keys | api_keys | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:auth | auth | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:carts | carts | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:claims | claims | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:collections | collections | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:currencies | currencies | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:customers | customers | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:fulfillment | fulfillment | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:inventory | inventory | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:orders | orders | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:payments | payments | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:products | products | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:promotions | promotions | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:returns | returns | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | api_keys | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | auth | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | carts | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | claims | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | collections | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | currencies | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | customers | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | fulfillment | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | inventory | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | orders | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | payments | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | products | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | promotions | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | returns | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | api_keys | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | auth | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | carts | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | claims | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | collections | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | currencies | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | customers | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | fulfillment | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | inventory | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | orders | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | payments | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | products | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | promotions | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | returns | rag_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | api_keys | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | auth | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | carts | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | claims | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | collections | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | currencies | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | customers | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | fulfillment | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | inventory | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | orders | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | payments | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | products | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | promotions | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| all | returns | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | api_keys | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | auth | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | carts | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | claims | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | collections | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | currencies | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | customers | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | fulfillment | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | inventory | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | orders | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | payments | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | products | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | promotions | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| dev | returns | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:api_keys | api_keys | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:auth | auth | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:carts | carts | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:claims | claims | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:collections | collections | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:currencies | currencies | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:customers | customers | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:fulfillment | fulfillment | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:inventory | inventory | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:orders | orders | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:payments | payments | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:products | products | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:promotions | promotions | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| leave_domain_out:returns | returns | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | api_keys | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | auth | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | carts | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | claims | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | collections | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | currencies | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | customers | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | fulfillment | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | inventory | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | orders | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | payments | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | products | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | promotions | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| test | returns | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | api_keys | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | auth | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | carts | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | claims | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | collections | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | currencies | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | customers | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | fulfillment | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | inventory | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | orders | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | payments | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | products | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | promotions | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |
| train | returns | bm25_all_max | tie | +0.000 | +0.000 | +0.000 | +0.000 |