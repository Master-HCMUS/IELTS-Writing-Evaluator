# Plan: CLI & Batch Scoring

Objective
- Enable offline scoring for calibration and evaluation.

Deliverables
- CLI: llm-score batch --input data.jsonl --out runs/ --task task2 --passes 2|3
- Parallel execution with rate limiting.
- Resume on failure; checkpointing.

Key Tasks
- JSONL input schema: {id, task_type, essay, image_path?, label?}
- Emit artifacts per item to Blob and local cache.
- Aggregate metrics after run.

Acceptance
- Can score 1,000 essays within expected budget and time.
- Robust to transient API failures (exponential backoff, jitter).
