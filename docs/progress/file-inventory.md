# File Inventory

Inventory
| Path | Purpose | Owner | Last Updated |
|------|---------|-------|--------------|
| pyproject.toml | Pin runtime, deps, tooling; pytest pythonpath | Copilot | 2025-08-15 |
| .gitignore | Ignore venv, caches, local env, build | Copilot | 2025-08-15 |
| .env.example | Environment template | Copilot | 2025-08-15 |
| src/app/main.py | FastAPI app + /score endpoint; latency logging; local run storage | Copilot | 2025-08-15 |
| src/app/config.py | Pydantic Settings for env config | Copilot | 2025-08-15 |
| src/app/versioning/determinism.py | Deterministic params, prompt hash, RunMeta | Copilot | 2025-08-15 |
| src/app/validation/__init__.py | Validation package marker | Copilot | 2025-08-15 |
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
   - [2025-08-17 08:10Z] Editor: Copilot
    - files: docs/plan/evaluation/scope-and-dataset.md, docs/plan/evaluation/runbook.md, docs/plan/evaluation/metrics-and-report.md
    - summary: Updated plan to use all available test records (~491) by default and adjusted runbook commands accordingly.
    - notes: Runner should treat --num-samples as optional; default is full test split.
     - [2025-08-17 08:20Z] Editor: Copilot
      - files: docs/plan/evaluation/design-and-files.md
      - summary: Clarified that the FastAPI /score endpoint will use the reusable scorer pipeline to keep a single source of truth.
      - notes: Avoids duplication and keeps evaluation runner and API behavior aligned.
