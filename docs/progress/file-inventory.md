# File Inventory

Inventory
| Path | Purpose | Owner | Last Updated |
|------|---------|-------|--------------|
| pyproject.toml | Pin runtime, deps, and tooling (ruff, pytest, mypy) | Copilot | 2025-08-15 |
| .gitignore | Ignore venv, caches, local env, build | Copilot | 2025-08-15 |
| .env.example | Environment template | Copilot | 2025-08-15 |
| src/app/main.py | FastAPI skeleton with health endpoints | Copilot | 2025-08-15 |
| src/app/config.py | Pydantic Settings for env config | Copilot | 2025-08-15 |
| src/app/versioning/determinism.py | Deterministic params, prompt hash, RunMeta | Copilot | 2025-08-15 |
| schemas/score_request.v1.json | API request JSON Schema v1 | Copilot | 2025-08-15 |
| schemas/score_response.v1.json | API response JSON Schema v1 | Copilot | 2025-08-15 |
| schemas/facts_task1.v1.json | Task 1 facts JSON Schema v1 | Copilot | 2025-08-15 |
| tests/test_prompt_hash.py | Prompt hash determinism test | Copilot | 2025-08-15 |
| docs/progress/plan-order-and-progress.md | Roadmap and tracker | User | 2025-08-15 |
| docs/specifications.md | PoC specification | User | 2025-08-15 |
| .github/copilot-instructions.md | Repo guidance for Copilot | Copilot | 2025-08-15 |

Change Log
- [2025-08-15 09:00Z] Editor: Copilot
  - files: pyproject.toml, .gitignore, .env.example, src/app/__init__.py, src/app/config.py, src/app/main.py, src/app/versioning/determinism.py, schemas/score_request.v1.json, schemas/score_response.v1.json, schemas/facts_task1.v1.json, tests/test_prompt_hash.py, docs/progress/plan-order-and-progress.md, docs/progress/file-inventory.md
  - summary: Initialize Phase 0 scaffolding with pinned deps, schemas v1, determinism utilities, FastAPI skeleton, and unit test; update tracker and add file inventory.
  - notes: FND-1 and FND-2 set to In progress; next add validation wiring and run metadata capture in API responses.
