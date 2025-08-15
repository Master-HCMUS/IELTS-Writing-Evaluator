# Plan: Observability & Evaluation

Objective
- Monitor reliability and measure alignment with human scores.

Deliverables
- App Insights telemetry: request counts, latency, token usage, error rates, dispersion/confidence metrics.
- Dashboards for pass latency and cost per request.
- Offline eval notebook/script: compute QWK, within-0.5, MAE; save reports.

Key Tasks
- Emit custom metrics: dispersion, low_confidence_rate, schema_repair_rate.
- Structured logs with correlation IDs across 3 passes.
- Batch runner to score labeled datasets and produce metrics.

Acceptance
- Live dashboard reflects p50/p95 latency and token usage.
- Test metrics meet targets: QWK ≥0.80, within-0.5 ≥85%, MAE ≤0.35.

Risks/Mitigations
- Incomplete traces across passes → propagate a parent trace id and pass index tags.
