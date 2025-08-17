# Progress Tracker — Evaluation Plan

Checklist
- [ ] Create reusable scorer pipeline `src/app/scoring/pipeline.py`.
- [ ] Implement evaluation package under `src/evaluation/` (datasets, predictor, metrics, reporting, runner).
- [ ] Add dependencies to `pyproject.toml`.
- [ ] Add smoke test `tests/test_evaluation_smoke.py`.
- [ ] Run smoke (20 samples) with mock mode.
- [ ] Run full job (491 samples) with real scoring.
- [ ] Review metrics vs targets (QWK ≥ 0.80, within-0.5 ≥ 85%, MAE ≤ 0.35).

Status Table
| ID | Work Item | Owner | Start | Due | Status | Notes |
|----|-----------|-------|-------|-----|--------|-------|
| EV-1 | Reusable scorer pipeline |  |  |  | Not started | Mirror /score logic |
| EV-2 | Dataset loader + sampler |  |  |  | Not started | HF datasets integration |
| EV-3 | Predictor + concurrency |  |  |  | Not started | Resume cache optional |
| EV-4 | Metrics + report |  |  |  | Not started | QWK, within-0.5, MAE |
| EV-5 | CLI runner |  |  |  | Not started | Windows cmd friendly |
| EV-6 | Smoke test |  |  |  | Not started | Mock LLMClient mode |
| EV-7 | Full run & publish |  |  |  | Not started | 491 samples |

Acceptance Gates
- Artifacts created in `reports/eval/YYYY-MM-DD/`.
- Metrics computed and reported with clear configuration, including prompt hash and model.
- Document whether mock mode or real LLM was used.
