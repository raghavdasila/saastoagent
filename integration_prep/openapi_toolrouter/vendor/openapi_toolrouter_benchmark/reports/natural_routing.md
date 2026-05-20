# Natural Routing

Realistic phrasing tasks are evaluated with routing-only metrics.

| Split | Track | Tasks | Routing tasks | Follow-up tasks | Top1 route | Top3 recover | Top10 recall | Decision type | Follow-up type | Param questions | Policy gaps | False execution | False overclarification | Validation | Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | natural_routing | 100 | 100 | 0 | 72.0% | 92.0% | 100.0% | 68.0% | 0.0% | 0.0% | 100.0% | 0.0% | 32.0% | 59.0% | 289.56 |
| dev | natural_routing | 20 | 20 | 0 | 65.0% | 95.0% | 100.0% | 70.0% | 0.0% | 0.0% | 100.0% | 0.0% | 30.0% | 55.0% | 296.10 |
| test | natural_routing | 19 | 19 | 0 | 73.7% | 94.7% | 100.0% | 78.9% | 0.0% | 0.0% | 100.0% | 0.0% | 21.1% | 68.4% | 275.64 |
| train | natural_routing | 61 | 61 | 0 | 73.8% | 90.2% | 100.0% | 63.9% | 0.0% | 0.0% | 100.0% | 0.0% | 36.1% | 57.4% | 291.74 |

## Examples

- `medusa_nat_001` Can you help me create cart -> ROUTE / medusa_store:PostCarts / top3=medusa_store:PostCarts, medusa_store:GetCartsId, medusa_store:PostCartsIdGiftCards
- `medusa_nat_002` Please update a cart -> ROUTE / medusa_store:PostCartsId / top3=medusa_store:PostCartsId, medusa_admin:GetProducts, medusa_admin:GetOrders
- `medusa_nat_003` A user wants to add gift card to cart -> ROUTE / medusa_store:PostCartsIdGiftCards / top3=medusa_store:PostCartsIdGiftCards, medusa_admin:GetGiftCardsId, medusa_store:DeleteCartsIdGiftCards
- `medusa_nat_004` I need to add line item to cart -> ASK_PARAM / medusa_store:DeleteCartsIdLineItemsLine_id / top3=medusa_store:DeleteCartsIdLineItemsLine_id, medusa_store:PostCartsIdLineItems, medusa_store:PostCartsIdLineItemsLine_id
- `medusa_nat_005` Can you help me update a line item in a cart -> ROUTE / medusa_store:PostCartsIdLineItemsLine_id / top3=medusa_store:PostCartsIdLineItemsLine_id, medusa_store:DeleteCartsIdLineItemsLine_id, medusa_store:PostCartsIdLineItems
- `medusa_nat_006` Please add promotions to cart -> ROUTE / medusa_store:PostCartsIdPromotions / top3=medusa_store:PostCartsIdPromotions, medusa_admin:GetPromotions, medusa_admin:DeletePromotionsId
- `medusa_nat_007` A user wants to add shipping method to cart -> ASK_PARAM / medusa_admin:PostReturnsIdShippingMethod / top3=medusa_admin:PostReturnsIdShippingMethod, medusa_store:PostCartsIdShippingMethods, medusa_admin:PostOrderEditsIdShippingMethod
- `medusa_nat_008` I need to add credit to cart -> ROUTE / medusa_store:PostCartsIdStoreCredits / top3=medusa_store:PostCartsIdStoreCredits, medusa_admin:PostStoreCreditAccountsIdCredit, medusa_store:PostCartsIdGiftCards
- `medusa_nat_009` Can you help me calculate cart taxes -> ROUTE / medusa_store:PostCartsIdTaxes / top3=medusa_store:PostCartsIdTaxes, medusa_store:PostShippingOptionsIdCalculate, medusa_store:GetProducts
- `medusa_nat_010` Please remove gift card from cart -> BLOCK_UNSAFE / None / top3=medusa_store:DeleteCartsIdGiftCards, medusa_admin:GetGiftCardsId, medusa_store:PostCartsIdGiftCards
- `medusa_nat_011` A user wants to remove line item from cart -> BLOCK_UNSAFE / None / top3=medusa_store:DeleteCartsIdLineItemsLine_id, medusa_store:PostCartsIdLineItemsLine_id, medusa_store:PostCartsIdLineItems
- `medusa_nat_012` I need to remove promotions from cart -> BLOCK_UNSAFE / None / top3=medusa_store:DeleteCartsIdPromotions, medusa_admin:GetPromotions, medusa_admin:PostPromotionsId
- `medusa_nat_013` Can you help me get a cart -> ROUTE / medusa_store:GetCartsId / top3=medusa_store:GetCartsId, medusa_store:PostCartsIdGiftCards, medusa_store:DeleteCartsIdGiftCards
- `medusa_nat_014` Please create customer group -> ROUTE / medusa_admin:PostCustomerGroups / top3=medusa_admin:PostCustomerGroups, medusa_admin:DeleteCustomerGroupsId, medusa_admin:GetCustomerGroups
- `medusa_nat_015` A user wants to create customer -> ROUTE / medusa_admin:GetCustomers / top3=medusa_admin:GetCustomers, medusa_admin:PostCustomers, medusa_store:PostCustomers
- `medusa_nat_016` I need to register customer -> ASK_PARAM / medusa_store:PostActor_typeAuth_provider_register / top3=medusa_store:PostActor_typeAuth_provider_register, medusa_store:PostCustomers, medusa_admin:GetCustomers
- `medusa_nat_017` Can you help me update customer -> ROUTE / medusa_admin:GetCustomers / top3=medusa_admin:GetCustomers, medusa_store:PostCustomersMe, medusa_admin:GetCustomerGroups
- `medusa_nat_018` Please create address for logged in customer -> ROUTE / medusa_store:PostCustomersMeAddresses / top3=medusa_store:PostCustomersMeAddresses, medusa_store:PostCustomersMeAddressesAddress_id, medusa_admin:DeleteCustomersIdAddressesAddress_id
- `medusa_nat_019` A user wants to update a customer group -> ROUTE / medusa_admin:PostCustomerGroupsId / top3=medusa_admin:PostCustomerGroupsId, medusa_admin:DeleteCustomerGroupsId, medusa_admin:PostCustomerGroupsIdCustomers
- `medusa_nat_020` I need to manage customers of a customer group -> ROUTE / medusa_admin:PostCustomerGroupsIdCustomers / top3=medusa_admin:PostCustomerGroupsIdCustomers, medusa_admin:DeleteCustomerGroupsId, medusa_admin:PostCustomersIdCustomerGroups