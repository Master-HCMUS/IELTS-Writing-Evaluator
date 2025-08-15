# Feature: Multi-pass Adjudication

Objective
- Stabilize scores via 3 independent deterministic passes; aggregate by median per criterion and overall.

Deliverables
- Pass runner: executes 3 scoring calls with identical prompts/params.
- Aggregator: median per-criterion; dispersion (max-min) and std dev.
- Confidence flag: low_confidence if dispersion > 0.5 bands.

Key Tasks
- Implement pass_runner.run_n(3) with idempotent request bodies (same seed if available).
- Define band arithmetic with 0.5 increments; median with banker’s rounding to nearest 0.5.
- Collect votes and stats in response for transparency.

Interfaces
- run_scoring_pass(essay, task_type) → ScorePass.
- aggregate_passes([ScorePass]) → AggregatedScore { per_criterion, overall, votes[], dispersion, confidence }.

Acceptance
- Re-score std dev ≤ 0.25 bands on stable inputs.
- Dispersion correctly computed and returned.
- Deterministic across runs with identical inputs.

Risks/Mitigations
- Latency x3 → parallelize passes up to concurrency limit; cache identical inputs.
