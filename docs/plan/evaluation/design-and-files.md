# Design & Files to Add under `src/`

Goal
- Reuse the existing 3-pass scorer outside FastAPI and provide a clean evaluation runner.

New/Updated Code (proposed)

1) Reusable scorer pipeline
- File: `src/app/scoring/pipeline.py`
- Expose `score_task2_3pass(essay: str) -> dict` returning:
  - `overall`, `votes`, `dispersion`, `confidence`
  - `per_criterion` (aggregated)
  - `meta` (prompt_hash, model, token_usage)
- Internals: use `get_system_prompt`, `get_user_prompt`, `get_response_schema`, `LLMClient`, `aggregate_votes`, `aggregate_per_criterion`, `prompt_hash`, and `validate_score_response`.

Integration with FastAPI (`src/app/main.py`)
- The `/score` endpoint will call `score_task2_3pass` from `app.scoring.pipeline` to execute the 3-pass scoring and aggregation.
- `main.py` will retain request validation, word-count guardrails, latency logging/metrics, and run artifact persistence. The scorer pipeline returns the aggregated response (including `per_criterion`, `overall`, `votes`, `dispersion`, `confidence`, and `meta`) which `main.py` can return directly after schema validation.
- This removes duplicated logic in `main.py` and ensures a single source of truth for scoring used by both the API and the evaluation runner.

2) Evaluation package
- Folder: `src/evaluation/`
  - `datasets/hf_task2.py`
    - Load HF dataset, select 1000 deterministic samples, compute word_count.
    - Return a pandas DataFrame with columns: `id`, `prompt`, `essay`, `band_true`, `word_count`.
  - `predictor.py`
    - Wrap calls to `score_task2_3pass`; control concurrency (workers). Capture per-item fields and optional latency.
    - Optional on-disk cache to resume.
  - `metrics.py`
    - Compute QWK (quadratic weighted kappa), MAE, within-0.5 rate, Pearson r(pred, word_count), dispersion stats.
  - `reporting.py`
    - Create `report.md`, `metrics.json`, `predictions.csv`, and optional plots.
  - `runner.py`
    - CLI entry point to execute end-to-end evaluation with args: dataset, split, num-samples, seed, workers, output-dir, no-plots.

3) Tests
- File: `tests/test_evaluation_smoke.py`
  - Tiny synthetic batch with LLM mock mode enabled; verify artifacts exist and basic schema of outputs.

Dependencies
- Add: `datasets`, `pandas`, `scikit-learn`, `numpy`, `scipy`, `matplotlib`, `seaborn`.
- Keep versions pinned via `pyproject.toml`.
