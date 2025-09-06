# IELTS Task 2 Scoring PoC

Minimal, deterministic 3-pass IELTS Task 2 essay scorer (FastAPI) with optional question alignment and evaluation tooling.

## Features
- FastAPI endpoint: POST /score
- Deterministic 3-pass aggregation (mock or Azure OpenAI)
- JSON schema validation (request/response)
- Optional question field to improve task relevance
- Local evaluation runner over public dataset
- Prompt hash + token usage metadata

## Requirements
- Python 3.11+
- pip (or uv / hatch optional)
- (Optional) Azure OpenAI credentials for real model calls; otherwise mock mode auto-enables

## Quick Start (API)
```
git clone <repo>
cd LLM
python -m venv .venv
. .venv/Scripts/activate  (Windows)  |  source .venv/bin/activate (Unix)
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open: http://localhost:8000/docs

## Environment (.env example)
```
APP_ENV=dev
LOG_LEVEL=INFO
AZURE_OPENAI_ENDPOINT=https://<your-endpoint>.openai.azure.com/
AZURE_OPENAI_API_KEY=xxxxxxxx
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_DEPLOYMENT_SCORER=gpt-4o-mini
```
Leave blank to use mock mode.

## Score Request (JSON)
```
{
  "task_type": "task2",
  "essay": "<250+ word essay>",
  "question": "Optional Task 2 prompt text"
}
```

## Local Test Script
```
python test_local.py
```
Writes test_response.json.

## Running Tests
```
pytest -q
```

## Evaluation Pipeline
```
python -m src.evaluation.runner --dataset chillies/IELTS-writing-task-2-evaluation --split test --num-samples 200
```
Artifacts under reports/eval/.

## Project Structure (key)
```
src/app/main.py          FastAPI entry
src/app/scoring/         Scoring pipeline + aggregation
src/app/prompts/         Prompt builders
schemas/                 JSON schemas
tests/                   API & logic tests
src/evaluation/          Batch prediction & reporting
docs/                    Plans, rubric, progress
```

## Determinism
- Temperature & top_p fixed
- 3 independent passes aggregated
- prompt_hash recorded with schema + rubric version

## Mock Mode
Activated automatically if AZURE_OPENAI_API_KEY is missing; returns stable stubbed bands for dev & CI.

## Troubleshooting
- 422: schema violation (missing task_type / essay)
- 400: essay <250 words
- Ensure question is ≤1000 chars if provided
- If Azure errors occur, fallback mock response is used (logged)
