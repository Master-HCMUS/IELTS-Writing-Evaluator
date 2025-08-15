# Plan: Dataset & Calibration Process

Objective
- Use 1,000 Task 2 labels to fit and validate the calibrator.

Deliverables
- Data split: Train 70% / Val 15% / Test 15% with seed.
- Batch scoring script (2 deterministic passes).
- Isotonic regression fit; saved calibrator and metrics report.

Key Tasks
- Normalize labels to 0–9 with 0.5 steps.
- Produce raw predictions, aggregate (median of 2) for training.
- Save per-essay artifacts: raw and calibrated overall, per-criterion, dispersion.
- Finalize calibrator on val; test metrics reporting.

Acceptance
- Reproducible splits; metrics within targets.
- calibrator.pkl stored under calibration/{version}/ with metadata.

Risks/Mitigations
- Label noise → robust median, optional winsorization before fit.
