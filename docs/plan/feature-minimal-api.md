# Feature: Minimal API

Objective
- Provide /score (Task1|Task2) and /calibrate endpoints with strict JSON schemas.

Deliverables
- FastAPI app with pydantic models for request/response.
- Input pre-checks (language detection, min words).
- Error handling: 422 for invalid schema; 400 for pre-check failures.

Key Tasks
- Define models: ScoreRequest { task_type, essay, image(optional), options }, ScoreResponse { per_criterion, overall, evidence, errors, votes, dispersion, confidence }.
- Implement /score → 3-pass pipeline (+Task1 facts when image supplied), optional calibration for Task2.
- Implement /calibrate (offline utility route or CLI-only) to fit isotonic reg on provided dataset.

Interfaces (pseudo)
- POST /score
- POST /calibrate (admin-only, or CLI script)

Acceptance
- JSON schema validation enforced; returns deterministic, schema-compliant JSON.
- Latency p50 ≤ 6s for Task2; p50 ≤ 9s for Task1 with vision (small inputs).

Risks/Mitigations
- Large essays → enforce size limits and truncate gracefully with user error.
