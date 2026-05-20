# Product Readiness

This report keeps routing accuracy separate from follow-up accuracy. Low-overlap remains a research stress track, not the product headline.

## Selected Decision Config

- Selected from: `dev`
- Route confidence: `0.3`
- Route margin: `0.0`
- Param confidence: `0.0`
- Top-k confidence: `0.18`
- Unsafe write threshold: `0.2`

| Split | Track | Tasks | Routing tasks | Follow-up tasks | Top1 route | Top3 recover | Top10 recall | Decision type | Follow-up type | Param questions | Policy gaps | False execution | False overclarification | Validation | Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | natural_routing | 100 | 100 | 0 | 72.0% | 92.0% | 100.0% | 68.0% | 0.0% | 0.0% | 100.0% | 0.0% | 32.0% | 59.0% | 289.56 |
| all | recovery_followup | 85 | 35 | 85 | 71.4% | 88.6% | 100.0% | 65.9% | 65.9% | 94.1% | 100.0% | 7.1% | 0.0% | 78.8% | 297.28 |
| dev | natural_routing | 20 | 20 | 0 | 65.0% | 95.0% | 100.0% | 70.0% | 0.0% | 0.0% | 100.0% | 0.0% | 30.0% | 55.0% | 296.10 |
| dev | recovery_followup | 19 | 7 | 19 | 85.7% | 100.0% | 100.0% | 73.7% | 73.7% | 100.0% | 100.0% | 5.3% | 0.0% | 84.2% | 299.30 |
| test | natural_routing | 19 | 19 | 0 | 73.7% | 94.7% | 100.0% | 78.9% | 0.0% | 0.0% | 100.0% | 0.0% | 21.1% | 68.4% | 275.64 |
| test | recovery_followup | 22 | 8 | 22 | 75.0% | 87.5% | 100.0% | 68.2% | 68.2% | 95.5% | 100.0% | 13.6% | 0.0% | 81.8% | 291.50 |
| train | natural_routing | 61 | 61 | 0 | 73.8% | 90.2% | 100.0% | 63.9% | 0.0% | 0.0% | 100.0% | 0.0% | 36.1% | 57.4% | 291.74 |
| train | recovery_followup | 44 | 20 | 44 | 65.0% | 85.0% | 100.0% | 61.4% | 61.4% | 90.9% | 100.0% | 4.5% | 0.0% | 75.0% | 299.30 |

## Decision Types

- `ROUTE`: high-confidence endpoint selection.
- `SHOW_TOPK`: medium-confidence top candidate set.
- `ASK_PARAM`: endpoint is clear, but OpenAPI-required inputs are missing.
- `ASK_DISAMBIGUATE`: multiple endpoint families are plausible.
- `ASK_POLICY`: OpenAPI lacks the business policy source.
- `BLOCK_UNSAFE`: destructive write needs confirmation; benchmark remains dry-run.