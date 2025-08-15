# Plan: Rubric & Anchor Exemplars

Objective
- Condensed, versioned IELTS rubric with tiny anchor exemplars to calibrate the model behavior.

Deliverables
- rubric/v1/summary.md (concise per-criterion descriptors for Task1/Task2).
- rubric/v1/anchors.json (micro examples per band boundary).

Key Tasks
- Draft succinct band descriptors emphasizing discriminative cues.
- Curate micro-anchors (1–2 sentences) for borderline bands.
- Reference rubric version in prompts and outputs.

Acceptance
- Prompt token footprint small enough for budget (≤1–2k tokens).
- Improved consistency observed in dry runs (lower dispersion).

Risks/Mitigations
- Overfitting anchors → rotate or randomize small set within version scope.
