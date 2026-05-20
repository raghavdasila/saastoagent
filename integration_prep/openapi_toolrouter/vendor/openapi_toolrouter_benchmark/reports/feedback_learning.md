# Feedback Learning

Feedback events observed: `0`
Feedback model status: `not_loaded`

The feedback-aware ranker can use selected/corrected endpoints as positives and rejected endpoints as negatives.

## Synthetic Offline Experiment

These rows are generated from benchmark corrections. They are not real runtime feedback claims.

- Synthetic feedback events: `185`
- Model status: `trained`
- Feedback file: `data\synthetic_feedback_events.jsonl`
- Model file: `artifacts\synthetic_feedback_ranker.joblib`

### Before

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

### After

| Split | Track | Tasks | Routing tasks | Follow-up tasks | Top1 route | Top3 recover | Top10 recall | Decision type | Follow-up type | Param questions | Policy gaps | False execution | False overclarification | Validation | Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | natural_routing | 100 | 100 | 0 | 62.0% | 90.0% | 99.0% | 57.0% | 0.0% | 0.0% | 100.0% | 0.0% | 43.0% | 52.0% | 319.90 |
| all | recovery_followup | 85 | 35 | 85 | 68.6% | 82.9% | 100.0% | 68.2% | 68.2% | 98.8% | 100.0% | 4.7% | 0.0% | 77.6% | 307.65 |
| dev | natural_routing | 20 | 20 | 0 | 50.0% | 80.0% | 95.0% | 50.0% | 0.0% | 0.0% | 100.0% | 0.0% | 50.0% | 45.0% | 350.40 |
| dev | recovery_followup | 19 | 7 | 19 | 85.7% | 100.0% | 100.0% | 73.7% | 73.7% | 100.0% | 100.0% | 5.3% | 0.0% | 84.2% | 315.71 |
| test | natural_routing | 19 | 19 | 0 | 68.4% | 94.7% | 100.0% | 68.4% | 0.0% | 0.0% | 100.0% | 0.0% | 31.6% | 63.2% | 291.80 |
| test | recovery_followup | 22 | 8 | 22 | 75.0% | 87.5% | 100.0% | 72.7% | 72.7% | 100.0% | 100.0% | 9.1% | 0.0% | 81.8% | 308.15 |
| train | natural_routing | 61 | 61 | 0 | 63.9% | 91.8% | 100.0% | 55.7% | 0.0% | 0.0% | 100.0% | 0.0% | 44.3% | 50.8% | 318.65 |
| train | recovery_followup | 44 | 20 | 44 | 60.0% | 75.0% | 100.0% | 63.6% | 63.6% | 97.7% | 100.0% | 2.3% | 0.0% | 72.7% | 303.91 |

## Feature Surface

- `rag_score`
- `bm25_score`
- `graph_sparse_score`
- `grag_score`
- `schema_param_match`
- `operation_class_confidence`
- `resource_overlap`
- `path_token_overlap`
- `auth_required_param_compatibility`
- `previous_successful_usage_count`
- `previous_correction_count`
- `previous_rejection_count`