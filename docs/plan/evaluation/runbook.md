# Runbook (Windows cmd)

Prerequisites
- Python env with project dependencies installed.
- Access to Hugging Face dataset (internet required).
- Azure OpenAI credentials configured if running real scoring; otherwise mock mode will be used automatically by `LLMClient`.

Commands
- Set path and run evaluation on the test split (uses all available ~491 by default):

```
set PYTHONPATH=%CD%\src
python -m evaluation.runner --dataset chillies/IELTS-writing-task-2-evaluation --split test --seed 42 --workers 2
```

- Quick smoke (20 samples, single worker, no plots on test split):

```
set PYTHONPATH=%CD%\src
python -m evaluation.runner --dataset chillies/IELTS-writing-task-2-evaluation --split test --num-samples 20 --seed 42 --workers 1 --no-plots
```

Outputs
- Artifacts in `reports/eval/YYYY-MM-DD/` as defined in `metrics-and-report.md`.

Troubleshooting
- If you see schema errors, check that the scorer pipeline mirrors `/score` behavior and that `validate_score_response` passes.
- If network issues with Hugging Face, pre-download or set the HF cache directory.
- If you hit rate limits/cost concerns, reduce `--workers` or `--num-samples`.
