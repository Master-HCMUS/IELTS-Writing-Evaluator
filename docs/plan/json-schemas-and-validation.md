# Plan: JSON Schemas & Validation

Objective
- Strict, versioned schemas for requests/responses with enforcement and repair.

Deliverables
- schema/score_request.v1.json
- schema/score_response.v1.json
- schema/facts_task1.v1.json
- Pydantic models mirroring JSON Schema.

Key Tasks
- Caps: evidence_quotes ≤3 per criterion, errors ≤10 (span+type+fix), suggestion length ≤200 chars.
- Validation pipeline: LLM → validate → repair prompt (once) → final or fail.
- Span validation after schema validation.

Acceptance
- ≥99% valid on first attempt; ≥99.5% valid after one repair attempt.
- All arrays capped; overflows truncated with audit note.

Risks/Mitigations
- Model verbosity → constrain via system prompt and max_tokens.
