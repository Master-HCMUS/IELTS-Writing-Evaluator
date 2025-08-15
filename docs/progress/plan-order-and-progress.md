# Implementation Roadmap & Progress Tracker

Purpose
- Define the execution order to meet the PoC goals (specifications.md).
- Track progress across features, with clear acceptance gates and owners.

Phases and Order (with dependencies)
- Phase 0 — Foundations (Day 0–0.5)
  - Repo scaffolding, env configs, SDK pinning, basic lint/test.
  - JSON Schemas & Validation (request/response/facts).
  - Determinism & Versioning (fixed decoding, prompt/schema hashing).
  - Deliverables: schema v1, prompt hash util, run metadata struct.

- Phase 1 — Task 2 Minimal Flow (Day 1–3)
  - Prompt Design (rubric summary + anchors, JSON-only).
  - Minimal API (/score task2), 3-pass adjudication, median + dispersion.
  - Storage & Run Logging, Observability (baseline metrics), Cost guardrails.
  - Deliverables: deterministic /score(Task2) returning schema-valid JSON.

- Phase 2 — Task 1 Vision Path (Day 3–4)
  - Vision: image → facts JSON; integrate facts into scorer.
  - Fallbacks and confidence flags; graceful degradation.
  - Deliverables: /score(Task1) with facts + evidence-first outputs.

- Phase 3 — Calibration & Evaluation (Day 4–6)
  - Dataset process (split, batch scoring), isotonic regression fit.
  - Apply calibrator at runtime (Task 2 overall only).
  - Evaluation report (QWK, within-0.5, MAE) and dashboards.
  - Deliverables: calibrator artifact + test metrics ≥ targets.

- Phase 4 — Hardening for PoC (Day 6–7)
  - Span Validation (quote/index positions), caps enforcement.
  - Security/Privacy controls, Cost & Budget alerts, Deployment & CI/CD.
  - CLI & Batch Scoring utility.
  - Deliverables: containerized service deployed; basic ops hygiene.

Acceptance Gates (exit criteria)
- G1: /score returns per-criterion, overall, evidence, errors, suggestions; JSON schema-valid.
- G2: 100% evidence quotes exist in essay; spans indexed; caps enforced.
- G3: 3-pass median; dispersion and low-confidence flagged deterministically.
- G4: Calibration test metrics: QWK ≥ 0.80, within-0.5 ≥ 85%, MAE ≤ 0.35.
- G5: Cost controls active; latency and token dashboards visible.
- G6: Simple FastAPI service deploys to Azure Container Apps/App Service with secrets in Key Vault.

Feature-to-Plan Mapping (reference)
- Evidence-first scoring → docs/plan/feature-evidence-first-scoring.md
- Multi-pass adjudication → docs/plan/feature-multi-pass-adjudication.md
- Task 1 image → facts → docs/plan/feature-task1-image-facts.md
- Calibration (Task 2) → docs/plan/feature-calibration-task2.md
- Determinism & versioning → docs/plan/feature-determinism-and-versioning.md
- Minimal API → docs/plan/feature-minimal-api.md
- Prompt design → docs/plan/prompt-design.md
- Azure setup → docs/plan/azure-resources-setup.md
- Storage/logging → docs/plan/storage-and-run-logging.md
- Observability/eval → docs/plan/observability-and-evaluation.md
- JSON schemas/validation → docs/plan/json-schemas-and-validation.md
- Security/privacy → docs/plan/security-privacy-and-compliance.md
- Cost/budget → docs/plan/cost-budget-and-scaling.md
- Dataset/calibration process → docs/plan/dataset-and-calibration-process.md
- Deployment/CI-CD → docs/plan/deployment-and-ci-cd.md
- Rubric/anchors → docs/plan/rubric-and-anchors.md
- Span validation → docs/plan/span-validation.md
- CLI & batch → docs/plan/cli-and-batch-scoring.md
- API schemas → docs/plan/api-schemas.md

Progress Checklist (update inline)
- [ ] Phase 0 Foundations complete (schemas v1, decoding, hash/versioning)
- [ ] Phase 1 Task 2 minimal API live (deterministic 3-pass, logging, metrics)
- [ ] Phase 2 Task 1 vision facts integrated and gated by confidence
- [ ] Phase 3 Calibration trained, applied at runtime, metrics meet targets
- [ ] Phase 4 Span validation + caps enforced in API responses
- [ ] Deployment to Azure (Container Apps/App Service) with KV-backed secrets
- [ ] Observability dashboards (latency, tokens, dispersion, low-confidence rate)
- [ ] Cost guards (budgets/alerts), concurrency/backpressure limits
- [ ] CLI batch runner operational for 1,000 essays

Lightweight Tracker Table
| ID | Work Item | Phase | Owner | Start | Due | Status | Notes |
|----|-----------|-------|-------|-------|-----|--------|-------|
| FND-1 | JSON Schemas v1 | 0 |  |  |  | Not started | score_request/response, facts_task1 |
| FND-2 | Determinism & versioning | 0 |  |  |  | Not started | temp=0, top_p=0.1, prompt hash |
| T2-API | /score Task 2 (3-pass) | 1 |  |  |  | Not started | median, dispersion, confidence |
| LOG-1 | Storage & run logging | 1 |  |  |  | Not started | request/response/meta blobs |
| OBS-1 | Baseline telemetry | 1 |  |  |  | Not started | p50/p95 latency, token usage |
| T1-VSN | Task 1 facts (vision) | 2 |  |  |  | Not started | facts schema + integration |
| CAL-1 | Batch scoring 1,000 | 3 |  |  |  | Not started | deterministic 2-pass |
| CAL-2 | Isotonic fit + apply | 3 |  |  |  | Not started | QWK ≥ 0.80 on test |
| VAL-1 | Span validation | 4 |  |  |  | Not started | positions for all quotes |
| SEC-1 | Sec/Privacy controls | 4 |  |  |  | Not started | KV, HTTPS, PII minimization |
| DEP-1 | Containerized deploy | 4 |  |  |  | Not started | ACA/App Service, CI/CD |
| CLI-1 | CLI & batch runner | 4 |  |  |  | Not started | resume, rate limit |

Milestones
- M1 (End Phase 1): Task 2 scoring API deterministic and schema-valid.
- M2 (End Phase 2): Task 1 supported with facts, confidence gating.
- M3 (End Phase 3): Calibration metrics achieved on held-out test.
- M4 (End Phase 4): PoC deployable with span validation, dashboards, and cost guards.

Risk Log (update as needed)
- R1: Vision misreads units → enforce units in schema; retry with stricter prompt.
- R2: Cost spikes from verbose outputs → stricter caps and max_tokens.
- R3: Dispersion high on niche prompts → anchors refresh; prompt tuning within version.

How to Update
- Edit this file to tick checkboxes, update the table, and add notes.
- Keep alignment with docs/plan files; version changes should bump prompt/schema hash.
