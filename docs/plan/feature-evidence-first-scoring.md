# Feature: Evidence-first Scoring

Objective
- Enforce quotes tied to rubric criteria; each quote must exist in the essay. No chain-of-thought in outputs.

Deliverables
- System prompt enforcing evidence-first outputs.
- JSON schema for per-criterion fields: band, evidence_quotes[], errors[], suggestions[].
- Span validator to confirm every quote exists.
- Caps: evidence (≤3/criterion), errors (≤10), suggestion length.

Key Tasks
- Define response schema (see schemas plan).
- Prompt constraints: "cite verbatim quotes; do not reason in free text."
- Implement span validation: exact substring lookup with normalization (unicode/whitespace).
- Actionable feedback templates: brief, specific, aligned to rubric.
- Fail-closed: if any quote not found → re-ask once with stricter decoding; else return low confidence.

Interfaces
- score_pipeline.evaluate_essay(essay, rubric_version) → EvidenceScore.
- EvidenceScore fields per criterion: band, evidence_quotes[], errors[], suggestions[].

Acceptance
- 100% of quotes and error spans found in essay text.
- Suggestions rated actionable in manual audit ≥80% (n=50).
- Meets caps and schema validation.

Risks/Mitigations
- Hallucinated quotes → hard span checks; limit to short quotes (≤30 words).
- Overlong outputs → enforce max tokens and capped arrays.
