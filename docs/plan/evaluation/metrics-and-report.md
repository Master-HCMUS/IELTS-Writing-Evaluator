# Metrics & Report

Metrics
- Agreement
  - Quadratic Weighted Kappa (QWK): `sklearn.metrics.cohen_kappa_score(weights="quadratic")`.
  - Within-0.5 rate: fraction of samples with `abs(pred - true) ≤ 0.5`.
  - MAE: mean absolute error in bands.
- Consistency & Confidence
  - Dispersion: mean, p50, p95 of 3-pass spread; low-confidence rate where dispersion > 0.5.
- Correlation
  - Pearson r between `band_pred` and `word_count`.
- Operational (if available)
  - Average token usage and latency.

Rounding & Validity
- Predictions already on 0.5 grid; ensure ground truth parsed as float (0.5 increments).
- Remove or flag essays < 250 words if scorer enforces a minimum.

Artifacts
- Folder: `reports/eval/YYYY-MM-DD/`
  - `metrics.json` — complete metrics and run config (dataset, split, N, seed, model, prompt_hash, mock_mode).
  - `report.md` — narrative + tables + embedded plots.
  - `predictions.csv` — per-item rows: `id, prompt, band_true, band_pred, diff, dispersion, confidence, word_count, votes_json, prompt_hash, model`.
  - `plots/*.png` (optional) — error histogram, confusion matrix, scatter true vs pred.

Report Structure (Markdown)
1. Overview
2. Configuration (dataset, split=test, N≈491 by default, seed, model, prompt_hash, date)
3. Metrics Summary (table)
4. Visuals (optional)
5. Error Analysis (top over/under predictions, diff distribution)
6. Notes & Limitations (mock mode, time/cost)
