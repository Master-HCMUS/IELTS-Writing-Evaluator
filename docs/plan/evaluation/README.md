# Evaluation Plan (Task 2)

Objective
- Evaluate the current Task 2 scoring method against the Hugging Face dataset `chillies/IELTS-writing-task-2-evaluation`.
- Run on a 491-sample subset, compute agreement metrics, and produce a human-readable + machine-readable report.

What this folder contains
- `scope-and-dataset.md` — dataset details and sampling rules.
- `design-and-files.md` — code structure to add under `src/` and responsibilities per file.
- `metrics-and-report.md` — metrics definitions and the report/artifacts layout.
- `runbook.md` — how to run the evaluation on Windows cmd.
- `progress-tracker.md` — checklist, status table, and acceptance gates.

Notes
- This plan reuses the same 3-pass deterministic scorer used by the `/score` endpoint to ensure apples-to-apples evaluation.
- The report will clearly indicate whether real LLM scoring or mock mode was used.
