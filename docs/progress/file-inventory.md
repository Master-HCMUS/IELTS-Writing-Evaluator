# File Inventory

| Path | Purpose | Owner | Last Updated |
|------|---------|-------|--------------|
| README.md | Root usage & setup guide | team | 2025-09-06 |
| docs/progress/file-inventory.md | Inventory + change log | team | 2025-09-06 |

| cook-training-data/finetuning_data/train.jsonl | Fine-tuning training data (744 examples, compact) | Copilot | 2025-09-27 |
| cook-training-data/finetuning_data/test.jsonl | Fine-tuning test data (187 examples, compact) | Copilot | 2025-09-27 |
| cook-training-data/finetuning_data/train_pretty.jsonl | Human-readable training data | Copilot | 2025-09-27 |
| cook-training-data/finetuning_data/test_pretty.jsonl | Human-readable test data | Copilot | 2025-09-27 |
| cook-training-data/README.md | Fine-tuning data documentation | Copilot | 2025-09-27 |
| src/cook_training_data/prepare.py | Production modular fine-tuning data preparation script | Copilot | 2025-09-27 |
| src/cook_training_data/data_loader.py | HuggingFace dataset loader | Copilot | 2025-09-27 |
| src/cook_training_data/schema_mapper.py | Score response schema mapping | Copilot | 2025-09-27 |
| src/cook_training_data/synthetic_generator.py | Azure OpenAI synthetic data generator | Copilot | 2025-09-27 |
| src/cook_training_data/finetuning_formatter.py | JSONL formatting and validation | Copilot | 2025-09-27 |

## Change Log
- [2025-09-27 15:00Z] Editor: Copilot
  - files: src/cook_training_data/ (modular architecture), cook-training-data/finetuning_data/ (production dataset)
  - summary: Established production-ready modular fine-tuning pipeline with 931 examples (744 train/187 validation), cost estimation ($8.93), and comprehensive validation
  - notes: Removed standalone script, focused on modular architecture with proper Python module structure and CLI interface

- [2025-09-06 00:00Z] Editor: Copilot
  - files: README.md, docs/progress/file-inventory.md
  - summary: Added root README with setup/run/test instructions; created inventory log.
  - notes: Update plan-order-and-progress.md in next change (not provided in context).
| src/app/validation/schemas.py | JSON Schema loaders and validators | Copilot | 2025-08-15 |
| src/app/scoring/__init__.py | Scoring package marker | Copilot | 2025-08-15 |
| src/app/scoring/aggregate.py | Median/dispersion and per-criterion aggregation utilities | Copilot | 2025-08-15 |
| src/app/scoring/task2_stub.py | Deterministic heuristic Task 2 scorer (Phase 1 stub) | Copilot | 2025-08-15 |
| schemas/score_request.v1.json | API request JSON Schema v1 | Copilot | 2025-08-15 |
| schemas/score_response.v1.json | API response JSON Schema v1 | Copilot | 2025-08-15 |
| schemas/facts_task1.v1.json | Task 1 facts JSON Schema v1 | Copilot | 2025-08-15 |
| tests/test_prompt_hash.py | Prompt hash determinism test | Copilot | 2025-08-15 |
| tests/test_schema_validation.py | Schema validation tests | Copilot | 2025-08-15 |
| tests/test_aggregate.py | Aggregation utility tests | Copilot | 2025-08-15 |
| tests/test_score_endpoint.py | /score endpoint tests | Copilot | 2025-08-15 |
| docs/progress/plan-order-and-progress.md | Roadmap and tracker | User | 2025-08-15 |
| docs/specifications.md | PoC specification | User | 2025-08-15 |
| .github/copilot-instructions.md | Repo guidance for Copilot | Copilot | 2025-08-15 |
| src/app/prompts/__init__.py | Prompts package marker | Copilot | 2024-12-18 |
| src/app/prompts/task2.py | Task 2 prompt templates with rubric and JSON constraints | Copilot | 2024-12-18 |
| src/app/scoring/llm_client.py | Azure OpenAI client wrapper with mock mode | Copilot | 2024-12-18 |
| test_local.py | Local test script for Task 2 scoring | Copilot | 2024-12-18 |
| src/app/main.py | FastAPI app with LLM-integrated /score endpoint | Copilot | 2024-12-18 |
| docs/rubric/v1/summary.md | Condensed IELTS rubric v1 | Copilot | 2025-08-15 |
| docs/rubric/v1/anchors.json | Anchor micro-exemplars v1 | Copilot | 2025-08-15 |
| tests/test_metrics_endpoint.py | Metrics endpoint test | Copilot | 2025-08-15 |
| src/app/scoring/pipeline.py | Reusable 3-pass scorer callable by API and eval | Copilot | 2025-08-17 |
| src/evaluation/datasets/hf_task2.py | Load HF dataset and sample/test split | Copilot | 2025-08-17 |
| src/evaluation/predictor.py | Batch predictions using scorer pipeline | Copilot | 2025-08-17 |
| src/evaluation/metrics.py | Metrics: QWK, MAE, within-0.5, dispersion, corr | Copilot | 2025-08-17 |
| src/evaluation/reporting.py | Save metrics/predictions and markdown report | Copilot | 2025-08-17 |
| src/evaluation/runner.py | CLI entrypoint for evaluation | Copilot | 2025-08-17 |
| tests/test_evaluation_smoke.py | Smoke test for pipeline + reporting | Copilot | 2025-08-17 |
| docs/plan/evaluation/README.md | Evaluation plan overview and index | Copilot | 2025-08-17 |
| docs/plan/evaluation/scope-and-dataset.md | Dataset details and sampling rules | Copilot | 2025-08-17 |
| docs/plan/evaluation/design-and-files.md | Code structure for evaluation under src/ | Copilot | 2025-08-17 |
| docs/plan/evaluation/metrics-and-report.md | Metrics definitions and report format | Copilot | 2025-08-17 |
| docs/plan/evaluation/runbook.md | How to run the evaluation | Copilot | 2025-08-17 |
| docs/plan/evaluation/progress-tracker.md | Checklist and status table | Copilot | 2025-08-17 |

Change Log
- [2025-08-15 09:00Z] Editor: Copilot
  - files: pyproject.toml, .gitignore, .env.example, src/app/__init__.py, src/app/config.py, src/app/main.py, src/app/versioning/determinism.py, schemas/score_request.v1.json, schemas/score_response.v1.json, schemas/facts_task1.v1.json, tests/test_prompt_hash.py, docs/progress/plan-order-and-progress.md, docs/progress/file-inventory.md
  - summary: Initialize Phase 0 scaffolding with pinned deps, schemas v1, determinism utilities, FastAPI skeleton, and unit test; update tracker and add file inventory.
  - notes: FND-1 and FND-2 set to In progress; next add validation wiring and run metadata capture in API responses.
- [2025-08-15 09:30Z] Editor: Copilot
  - files: pyproject.toml, src/app/validation/__init__.py, src/app/validation/schemas.py, tests/test_schema_validation.py, docs/progress/plan-order-and-progress.md, docs/progress/file-inventory.md
  - summary: Completed Phase 0 by adding JSON Schema validation utilities and tests; configured pytest to import src; marked Phase 0 complete in tracker.
  - notes: Next Phase 1 — implement /score (Task 2) with 3-pass adjudication and logging.
- [2025-08-15 10:00Z] Editor: Copilot
  - files: src/app/scoring/__init__.py, src/app/scoring/aggregate.py, src/app/scoring/task2_stub.py, src/app/main.py, tests/test_aggregate.py, tests/test_score_endpoint.py, docs/progress/plan-order-and-progress.md, docs/progress/file-inventory.md
  - summary: Implemented Phase 1 minimal /score (Task 2) with deterministic 3-pass aggregation and schema validation; added tests.
  - notes: Next: wire real LLM scorer, add storage/logging and baseline telemetry (LOG-1, OBS-1).
- [2025-08-15 10:30Z] Editor: Copilot
  - files: src/app/main.py, docs/progress/plan-order-and-progress.md, docs/progress/file-inventory.md
  - summary: Added latency middleware, local run logging (runs/{date}/{run_id}), prompt_hash computation, and max word guardrail for Task 2.
  - notes: Phase 1 continues; next wire basic metrics export and start Azure storage integration (optional).
- [2025-08-15 11:00Z] Editor: Copilot
  - files: src/app/scoring/aggregate.py, src/app/main.py, tests/test_aggregate.py, docs/progress/plan-order-and-progress.md, docs/progress/file-inventory.md
  - summary: Implemented per-criterion median aggregation and wired it into /score; added unit test.
  - notes: Phase 1 next steps: wire basic metrics export and consider simple language detection pre-check.
- [2024-12-18 10:00Z] Editor: Copilot
  - files: pyproject.toml, src/app/prompts/__init__.py, src/app/prompts/task2.py, src/app/scoring/llm_client.py, src/app/main.py, test_local.py, docs/progress/plan-order-and-progress.md, docs/progress/file-inventory.md
  - summary: Integrated LLM scoring for Task 2 with Azure OpenAI client and mock mode for local testing; added prompts with rubric integration.
  - notes: Task 2 now runnable locally without Azure credentials (uses mock mode); with credentials, calls Azure OpenAI.
   - [2025-08-17 08:00Z] Editor: Copilot
  - files: docs/plan/evaluation/README.md, docs/plan/evaluation/scope-and-dataset.md, docs/plan/evaluation/design-and-files.md, docs/plan/evaluation/metrics-and-report.md, docs/plan/evaluation/runbook.md, docs/plan/evaluation/progress-tracker.md
  - summary: Added evaluation plan docs and updated to use the test split for evaluation; documented run steps and metrics.
  - notes: Evaluate 1,000 samples from the test split by default; artifacts go to reports/eval/.
   - [2025-08-17 08:30Z] Editor: Copilot
    - files: src/app/scoring/pipeline.py, src/evaluation/datasets/hf_task2.py, src/evaluation/predictor.py, src/evaluation/metrics.py, src/evaluation/reporting.py, src/evaluation/runner.py, tests/test_evaluation_smoke.py, src/app/main.py, pyproject.toml, docs/plan/evaluation/progress-tracker.md
    - summary: Implemented evaluation pipeline and runner, added reusable scorer, wired API to use it, added dependencies, and smoke test.
    - notes: Next: run smoke (mock mode) then execute full test split evaluation and publish artifacts.
   - [2025-08-17 08:10Z] Editor: Copilot
    - files: docs/plan/evaluation/scope-and-dataset.md, docs/plan/evaluation/runbook.md, docs/plan/evaluation/metrics-and-report.md
    - summary: Updated plan to use all available test records (~491) by default and adjusted runbook commands accordingly.
    - notes: Runner should treat --num-samples as optional; default is full test split.
     - [2025-08-17 08:20Z] Editor: Copilot
      - files: docs/plan/evaluation/design-and-files.md
      - summary: Clarified that the FastAPI /score endpoint will use the reusable scorer pipeline to keep a single source of truth.
      - notes: Avoids duplication and keeps evaluation runner and API behavior aligned.
