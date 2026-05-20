# Learned Ranker Ablations

| Split | Baseline | Complete@1 | Complete@10 | First-step@1 | Required Params | Validation | Abstention |
|---|---|---:|---:|---:|---:|---:|---:|
| all | learned_lexical | 50.0% | 50.0% | 50.0% | 56.0% | 50.0% | 100.0% |
| all | learned_bm25 | 50.0% | 50.0% | 50.0% | 56.0% | 50.0% | 100.0% |
| all | learned_graph | 50.0% | 50.0% | 50.0% | 56.0% | 50.0% | 100.0% |
| all | learned_schema_param | 50.0% | 50.0% | 50.0% | 56.0% | 50.0% | 100.0% |
| all | learned_lexical_graph | 50.0% | 50.0% | 50.0% | 56.0% | 50.0% | 100.0% |
| all | learned_all | 50.0% | 50.0% | 50.0% | 56.0% | 50.0% | 100.0% |
| all | learned | 50.0% | 50.0% | 50.0% | 56.0% | 50.0% | 100.0% |
| dev | learned_lexical | 50.0% | 50.0% | 50.0% | 52.5% | 50.0% | 100.0% |
| dev | learned_bm25 | 50.0% | 50.0% | 50.0% | 52.5% | 50.0% | 100.0% |
| dev | learned_graph | 50.0% | 50.0% | 50.0% | 52.5% | 50.0% | 100.0% |
| dev | learned_schema_param | 50.0% | 50.0% | 50.0% | 52.5% | 50.0% | 100.0% |
| dev | learned_lexical_graph | 50.0% | 50.0% | 50.0% | 52.5% | 50.0% | 100.0% |
| dev | learned_all | 50.0% | 50.0% | 50.0% | 52.5% | 50.0% | 100.0% |
| dev | learned | 50.0% | 50.0% | 50.0% | 52.5% | 50.0% | 100.0% |
| leave_domain_out:api_keys | learned_lexical | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:api_keys | learned_bm25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:api_keys | learned_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:api_keys | learned_schema_param | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:api_keys | learned_lexical_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:api_keys | learned_all | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:api_keys | learned | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:auth | learned_lexical | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:auth | learned_bm25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:auth | learned_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:auth | learned_schema_param | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:auth | learned_lexical_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:auth | learned_all | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:auth | learned | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:carts | learned_lexical | 55.2% | 55.2% | 55.2% | 55.2% | 55.2% | 100.0% |
| leave_domain_out:carts | learned_bm25 | 55.2% | 55.2% | 55.2% | 55.2% | 55.2% | 100.0% |
| leave_domain_out:carts | learned_graph | 55.2% | 55.2% | 55.2% | 55.2% | 55.2% | 100.0% |
| leave_domain_out:carts | learned_schema_param | 55.2% | 55.2% | 55.2% | 55.2% | 55.2% | 100.0% |
| leave_domain_out:carts | learned_lexical_graph | 55.2% | 55.2% | 55.2% | 55.2% | 55.2% | 100.0% |
| leave_domain_out:carts | learned_all | 55.2% | 55.2% | 55.2% | 55.2% | 55.2% | 100.0% |
| leave_domain_out:carts | learned | 55.2% | 55.2% | 55.2% | 55.2% | 55.2% | 100.0% |
| leave_domain_out:claims | learned_lexical | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:claims | learned_bm25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:claims | learned_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:claims | learned_schema_param | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:claims | learned_lexical_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:claims | learned_all | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:claims | learned | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:collections | learned_lexical | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:collections | learned_bm25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:collections | learned_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:collections | learned_schema_param | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:collections | learned_lexical_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:collections | learned_all | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:collections | learned | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:currencies | learned_lexical | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:currencies | learned_bm25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:currencies | learned_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:currencies | learned_schema_param | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:currencies | learned_lexical_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:currencies | learned_all | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:currencies | learned | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:customers | learned_lexical | 13.9% | 13.9% | 13.9% | 25.0% | 13.9% | 100.0% |
| leave_domain_out:customers | learned_bm25 | 13.9% | 13.9% | 13.9% | 25.0% | 13.9% | 100.0% |
| leave_domain_out:customers | learned_graph | 13.9% | 13.9% | 13.9% | 25.0% | 13.9% | 100.0% |
| leave_domain_out:customers | learned_schema_param | 13.9% | 13.9% | 13.9% | 25.0% | 13.9% | 100.0% |
| leave_domain_out:customers | learned_lexical_graph | 13.9% | 13.9% | 13.9% | 25.0% | 13.9% | 100.0% |
| leave_domain_out:customers | learned_all | 13.9% | 13.9% | 13.9% | 25.0% | 13.9% | 100.0% |
| leave_domain_out:customers | learned | 13.9% | 13.9% | 13.9% | 25.0% | 13.9% | 100.0% |
| leave_domain_out:fulfillment | learned_lexical | 33.3% | 33.3% | 33.3% | 44.4% | 33.3% | 100.0% |
| leave_domain_out:fulfillment | learned_bm25 | 33.3% | 33.3% | 33.3% | 44.4% | 33.3% | 100.0% |
| leave_domain_out:fulfillment | learned_graph | 33.3% | 33.3% | 33.3% | 44.4% | 33.3% | 100.0% |
| leave_domain_out:fulfillment | learned_schema_param | 33.3% | 33.3% | 33.3% | 44.4% | 33.3% | 100.0% |
| leave_domain_out:fulfillment | learned_lexical_graph | 33.3% | 33.3% | 33.3% | 44.4% | 33.3% | 100.0% |
| leave_domain_out:fulfillment | learned_all | 33.3% | 33.3% | 33.3% | 44.4% | 33.3% | 100.0% |
| leave_domain_out:fulfillment | learned | 33.3% | 33.3% | 33.3% | 44.4% | 33.3% | 100.0% |
| leave_domain_out:inventory | learned_lexical | 31.2% | 31.2% | 31.2% | 50.0% | 31.2% | 100.0% |
| leave_domain_out:inventory | learned_bm25 | 31.2% | 31.2% | 31.2% | 50.0% | 31.2% | 100.0% |
| leave_domain_out:inventory | learned_graph | 31.2% | 31.2% | 31.2% | 50.0% | 31.2% | 100.0% |
| leave_domain_out:inventory | learned_schema_param | 31.2% | 31.2% | 31.2% | 50.0% | 31.2% | 100.0% |
| leave_domain_out:inventory | learned_lexical_graph | 31.2% | 31.2% | 31.2% | 50.0% | 31.2% | 100.0% |
| leave_domain_out:inventory | learned_all | 31.2% | 31.2% | 31.2% | 50.0% | 31.2% | 100.0% |
| leave_domain_out:inventory | learned | 31.2% | 31.2% | 31.2% | 50.0% | 31.2% | 100.0% |
| leave_domain_out:orders | learned_lexical | 15.4% | 15.4% | 15.4% | 23.1% | 15.4% | 100.0% |
| leave_domain_out:orders | learned_bm25 | 15.4% | 15.4% | 15.4% | 23.1% | 15.4% | 100.0% |
| leave_domain_out:orders | learned_graph | 15.4% | 15.4% | 15.4% | 23.1% | 15.4% | 100.0% |
| leave_domain_out:orders | learned_schema_param | 15.4% | 15.4% | 15.4% | 23.1% | 15.4% | 100.0% |
| leave_domain_out:orders | learned_lexical_graph | 15.4% | 15.4% | 15.4% | 23.1% | 15.4% | 100.0% |
| leave_domain_out:orders | learned_all | 15.4% | 15.4% | 15.4% | 23.1% | 15.4% | 100.0% |
| leave_domain_out:orders | learned | 15.4% | 15.4% | 15.4% | 23.1% | 15.4% | 100.0% |
| leave_domain_out:payments | learned_lexical | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:payments | learned_bm25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:payments | learned_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:payments | learned_schema_param | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:payments | learned_lexical_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:payments | learned_all | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:payments | learned | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:products | learned_lexical | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:products | learned_bm25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:products | learned_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:products | learned_schema_param | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:products | learned_lexical_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:products | learned_all | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:products | learned | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:promotions | learned_lexical | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:promotions | learned_bm25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:promotions | learned_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:promotions | learned_schema_param | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:promotions | learned_lexical_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:promotions | learned_all | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:promotions | learned | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:returns | learned_lexical | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:returns | learned_bm25 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:returns | learned_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:returns | learned_schema_param | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:returns | learned_lexical_graph | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:returns | learned_all | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| leave_domain_out:returns | learned | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| test | learned_lexical | 50.0% | 50.0% | 50.0% | 55.3% | 50.0% | 100.0% |
| test | learned_bm25 | 50.0% | 50.0% | 50.0% | 55.3% | 50.0% | 100.0% |
| test | learned_graph | 50.0% | 50.0% | 50.0% | 55.3% | 50.0% | 100.0% |
| test | learned_schema_param | 50.0% | 50.0% | 50.0% | 55.3% | 50.0% | 100.0% |
| test | learned_lexical_graph | 50.0% | 50.0% | 50.0% | 55.3% | 50.0% | 100.0% |
| test | learned_all | 50.0% | 50.0% | 50.0% | 55.3% | 50.0% | 100.0% |
| test | learned | 50.0% | 50.0% | 50.0% | 55.3% | 50.0% | 100.0% |
| train | learned_lexical | 50.0% | 50.0% | 50.0% | 57.4% | 50.0% | 100.0% |
| train | learned_bm25 | 50.0% | 50.0% | 50.0% | 57.4% | 50.0% | 100.0% |
| train | learned_graph | 50.0% | 50.0% | 50.0% | 57.4% | 50.0% | 100.0% |
| train | learned_schema_param | 50.0% | 50.0% | 50.0% | 57.4% | 50.0% | 100.0% |
| train | learned_lexical_graph | 50.0% | 50.0% | 50.0% | 57.4% | 50.0% | 100.0% |
| train | learned_all | 50.0% | 50.0% | 50.0% | 57.4% | 50.0% | 100.0% |
| train | learned | 50.0% | 50.0% | 50.0% | 57.4% | 50.0% | 100.0% |

## Feature Masks

| Baseline | Features |
|---|---|
| learned_all | rag_endpoint, rag_all_max, rag_all_top3, bm25_all_max, bm25_all_top3, graph_sparse, graph_text, schema_param, hybrid, operation_class_match, query_endpoint_overlap, required_param_count, request_schema_count, response_schema_count, operation_confidence |
| learned_bm25 | bm25_all_max, bm25_all_top3 |
| learned_graph | graph_sparse, graph_text |
| learned_lexical | rag_endpoint, rag_all_max, rag_all_top3, query_endpoint_overlap |
| learned_lexical_graph | rag_endpoint, rag_all_max, rag_all_top3, graph_sparse, graph_text, query_endpoint_overlap |
| learned_schema_param | schema_param, required_param_count, request_schema_count, response_schema_count |