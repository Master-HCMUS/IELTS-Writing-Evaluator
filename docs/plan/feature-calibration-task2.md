# Feature: Calibration (Task 2)

Objective
- Map model overall bands to human bands using isotonic regression; improve QWK and within-0.5.

Deliverables
- Offline pipeline: train/val/test split, predictions (2 deterministic passes), isotonic fit.
- Metrics: QWK, within-0.5, MAE; report on held-out test.
- Artifact: calibrator.pkl + versioned metadata.

Key Tasks
- Generate raw overall scores on training set; fit IsotonicRegression (monotonic=True).
- Lock model on val; evaluate on test; log metrics.
- Runtime: apply calibrator to overall only; then round to nearest 0.5 (banker’s).

Interfaces
- calibrate.fit(train_preds, train_labels) → calibrator.pkl.
- calibrate.apply(overall_raw) → overall_calibrated.

Acceptance
- Test QWK ≥ 0.80; within-0.5 ≥ 85%; MAE ≤ 0.35.
- Stable across resamples; store seeds, splits, versions.

Risks/Mitigations
- Distribution shift → periodic recalibration; monitor drift metrics.
