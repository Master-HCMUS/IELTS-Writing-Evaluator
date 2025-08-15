# Plan: Storage & Run Logging

Objective
- Persist inputs/outputs, metadata, and artifacts for traceability and audits.

Deliverables
- Blob container structure:
  - runs/{date}/{run_id}/request.json
  - runs/{date}/{run_id}/response.json
  - runs/{date}/{run_id}/meta.json (hashes, model, tokens, timings)
  - prompts/{version}/system.txt, user.txt, schema.json
  - calibration/{version}/calibrator.pkl, report.json
- Naming with ULIDs for run_id.

Key Tasks
- Standardize meta.json fields: prompt_hash, schema_version, rubric_version, sdk_versions, git_commit.
- Redact PII where applicable.
- Add small retention policy (e.g., 30 days) for PoC.

Acceptance
- Every API call produces a complete, replayable record.
- Span/evidence validation recorded and pass/fail status stored.
