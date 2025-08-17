# Scope & Dataset

Dataset
- Source: Hugging Face `chillies/IELTS-writing-task-2-evaluation`.
- Columns: `prompt`, `essay`, `evaluation`, `band`.
- Task: IELTS Task 2 (argumentative/discursive).

Sampling
- Default split: test (evaluate on the dataset's test split).
- Use all available test samples by default (currently 491).
- Optional: if a specific `--num-samples` is provided, use `min(num_samples, len(test))` with deterministic selection (fixed seed, e.g., 42).
- Track word count per essay for correlation checks and optional filtering (min length ≥ 250 words recommended to match API constraints).

Ground Truth
- Use `band` as the overall band reference (float, 0.5 increments).
- Ignore `evaluation` for metrics; may be used later for qualitative error analysis.

Out-of-Scope (for this pass)
- Per-criterion ground truth (not provided in dataset).
- Task 1 vision facts.
- Calibration fitting (separate Phase 3 effort).
