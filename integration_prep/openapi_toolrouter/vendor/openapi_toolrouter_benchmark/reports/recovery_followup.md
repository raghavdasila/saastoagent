# Recovery Follow-Up

Ambiguous, missing-param, policy, and unsafe-write tasks are evaluated as follow-up decisions, not endpoint-routing accuracy.

| Split | Track | Tasks | Routing tasks | Follow-up tasks | Top1 route | Top3 recover | Top10 recall | Decision type | Follow-up type | Param questions | Policy gaps | False execution | False overclarification | Validation | Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | recovery_followup | 85 | 35 | 85 | 71.4% | 88.6% | 100.0% | 65.9% | 65.9% | 94.1% | 100.0% | 7.1% | 0.0% | 78.8% | 297.28 |
| dev | recovery_followup | 19 | 7 | 19 | 85.7% | 100.0% | 100.0% | 73.7% | 73.7% | 100.0% | 100.0% | 5.3% | 0.0% | 84.2% | 299.30 |
| test | recovery_followup | 22 | 8 | 22 | 75.0% | 87.5% | 100.0% | 68.2% | 68.2% | 95.5% | 100.0% | 13.6% | 0.0% | 81.8% | 291.50 |
| train | recovery_followup | 44 | 20 | 44 | 65.0% | 85.0% | 100.0% | 61.4% | 61.4% | 90.9% | 100.0% | 4.5% | 0.0% | 75.0% | 299.30 |

## Examples

- `medusa_rec_001` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /store/carts (Create Cart), but I need x-publishable-api-key before preparing the call.
- `medusa_rec_002` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /store/carts/{id} (Update a Cart), but I need id, x-publishable-api-key before preparing the call.
- `medusa_rec_003` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /store/carts/{id}/gift-cards (Add Gift Card to Cart), but I need id, x-publishable-api-key, code before preparing the call.
- `medusa_rec_004` expected=ASK_PARAM actual=ASK_PARAM question=I can use DELETE /store/carts/{id}/line-items/{line_id} (Remove Line Item from Cart), but I need id, line_id, x-publishable-api-key before preparing the call.
- `medusa_rec_005` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /store/carts/{id}/line-items/{line_id} (Update a Line Item in a Cart), but I need id, line_id, x-publishable-api-key before preparing the call.
- `medusa_rec_006` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /store/carts/{id}/promotions (Add Promotions to Cart), but I need id, x-publishable-api-key, promo_codes before preparing the call.
- `medusa_rec_007` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /admin/returns/{id}/shipping-method (Add a Shipping Method to a Return), but I need id, shipping_option_id before preparing the call.
- `medusa_rec_008` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /store/carts/{id}/store-credits (Add Store Credit to Cart), but I need id, x-publishable-api-key, amount before preparing the call.
- `medusa_rec_009` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /store/carts/{id}/taxes (Calculate Cart Taxes), but I need id, x-publishable-api-key before preparing the call.
- `medusa_rec_010` expected=ASK_PARAM actual=ASK_PARAM question=I can use DELETE /store/carts/{id}/gift-cards (Remove Gift Card from Cart), but I need id, x-publishable-api-key, code before preparing the call.
- `medusa_rec_011` expected=ASK_PARAM actual=ASK_PARAM question=I can use DELETE /store/carts/{id}/line-items/{line_id} (Remove Line Item from Cart), but I need id, line_id, x-publishable-api-key before preparing the call.
- `medusa_rec_012` expected=ASK_PARAM actual=ASK_PARAM question=I can use DELETE /store/carts/{id}/promotions (Remove Promotions from Cart), but I need id, x-publishable-api-key, promo_codes before preparing the call.
- `medusa_rec_013` expected=ASK_PARAM actual=ASK_PARAM question=I can use GET /store/carts/{id} (Get a Cart), but I need id, x-publishable-api-key before preparing the call.
- `medusa_rec_014` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /admin/customer-groups (Create Customer Group), but I need name before preparing the call.
- `medusa_rec_015` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /auth/customer/{auth_provider}/register (Retrieve Registration JWT Token), but I need auth_provider before preparing the call.
- `medusa_rec_016` expected=ASK_PARAM actual=ROUTE question=
- `medusa_rec_017` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /store/customers/me/addresses (Create Address for Logged-In Customer), but I need x-publishable-api-key before preparing the call.
- `medusa_rec_018` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /admin/customer-groups/{id} (Update a Customer Group), but I need id before preparing the call.
- `medusa_rec_019` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /admin/customer-groups/{id}/customers (Manage Customers of a Customer Group), but I need id before preparing the call.
- `medusa_rec_020` expected=ASK_PARAM actual=ROUTE question=
- `medusa_rec_021` expected=ASK_PARAM actual=ASK_PARAM question=I can use DELETE /admin/customers/{id}/addresses/{address_id} (Remove an Address from Customer), but I need id, address_id before preparing the call.
- `medusa_rec_022` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /admin/customers/{id}/addresses/{address_id} (Update a Customer's Address), but I need id, address_id before preparing the call.
- `medusa_rec_023` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /admin/customers/{id}/customer-groups (Manage Customer Groups of Customer), but I need id before preparing the call.
- `medusa_rec_024` expected=ASK_PARAM actual=ASK_PARAM question=I can use DELETE /admin/customers/{id} (Delete a Customer), but I need id before preparing the call.
- `medusa_rec_025` expected=ASK_PARAM actual=ASK_PARAM question=I can use POST /auth/user/{auth_provider}/callback (Validate Authentication Callback), but I need auth_provider before preparing the call.
- `medusa_rec_026` expected=ASK_DISAMBIGUATE actual=ROUTE question=
- `medusa_rec_027` expected=ASK_DISAMBIGUATE actual=ROUTE question=
- `medusa_rec_028` expected=ASK_DISAMBIGUATE actual=ROUTE question=
- `medusa_rec_029` expected=ASK_DISAMBIGUATE actual=ASK_PARAM question=I can use GET /admin/workflows-executions/{workflow_id}/{transaction_id} (Get Workflow Execution's Details), but I need workflow_id, transaction_id before preparing the call.
- `medusa_rec_030` expected=ASK_DISAMBIGUATE actual=ASK_PARAM question=I can use GET /admin/workflows-executions/{workflow_id}/{transaction_id} (Get Workflow Execution's Details), but I need workflow_id, transaction_id before preparing the call.