# Pattern Gap: Deployed Chat Result Continuity

Date: 2026-05-22
Status: Known gap, not fixed

## Observed Failure

The deployed Medusa chat could list products but failed the follow-up purchase
flow.

Conversation:

```text
visitor: what products do we have
assistant: returned raw product JSON with Medusa T-Shirt
visitor: i want to buy medusa tshirt
assistant: asked for id
visitor: idk
assistant: recovered the T-shirt and sizes
visitor: add the L size to cart
assistant: asked a generic missing-detail question with unrelated route choices
assistant: mentioned x publishable api key
```

## Diagnosis

This is not a Medusa problem. It is a generic deployed-runtime continuity and
orchestration gap.

The runtime needs to carry forward structured information from prior tool
results:

- product title and handle
- product ID
- variants/options and selected size
- required cart/region/customer fields
- credential requirements that should be satisfied by connection credentials,
  not public visitor text

## Required Product Behavior

The public assistant should:

- summarize product results naturally before details
- resolve follow-up phrases like `the Medusa T-Shirt` against prior results
- resolve size/variant choices from prior product details
- create or reuse a cart when needed
- ask natural missing details only, such as quantity, region, shipping, or
  confirmation
- never ask the visitor for internal operation IDs, product IDs, endpoint paths,
  scores, trace IDs, tool names, or credential header names

## Short-Term UI Stopgap

Until final product cards are designed, public JSON results should be placed
behind a collapsible details control:

- visible summary first
- expandable raw details second
- full raw payloads remain available in builder diagnostics

## Non-Goal

Do not hardcode Medusa product/cart behavior to fix this. The fix must be
OpenAPI-driven and reusable for other SaaS APIs.
