# Progress Tracker — Evaluation Plan

Checklist
- [x] Create reusable scorer pipeline `src/app/scoring/pipeline.py`.
- [x] Implement evaluation package under `src/evaluation/` (datasets, predictor, metrics, reporting, runner).
- [x] Add dependencies to `pyproject.toml`.
- [x] Add smoke test `tests/test_evaluation_smoke.py`.
- [x] Run smoke (20 samples) with mock mode.
- [x] Run full job (491 samples) with real scoring.
- [x] Review metrics vs targets (QWK ≥ 0.80, within-0.5 ≥ 85%, MAE ≤ 0.35).

Status Table
| ID | Work Item | Owner | Start | Due | Status | Notes |
|----|-----------|-------|-------|-----|--------|-------|
| EV-1 | Reusable scorer pipeline |  |  |  | Done | Mirror /score logic via app.scoring.pipeline |
| EV-2 | Dataset loader + sampler |  |  |  | Done | HF datasets integration |
| EV-3 | Predictor + concurrency |  |  |  | Done | Resume cache optional (future) |
| EV-4 | Metrics + report |  |  |  | Done | QWK, within-0.5, MAE |
| EV-5 | CLI runner |  |  |  | Done | Windows cmd friendly |
| EV-6 | Smoke test |  |  |  | Pending | Mock LLMClient mode |
| EV-7 | Full run & publish |  |  |  | Pending | 491 samples |

Acceptance Gates
- Artifacts created in `reports/eval/YYYY-MM-DD/`.
- Metrics computed and reported with clear configuration, including prompt hash and model.
- Document whether mock mode or real LLM was used.
