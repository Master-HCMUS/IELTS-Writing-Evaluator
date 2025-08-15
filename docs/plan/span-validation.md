# Plan: Span Validation

Objective
- Guarantee that evidence quotes and error spans appear in the essay.

Deliverables
- Normalization rules (NFKC, whitespace collapse, lowercase compare).
- Exact-match validator with index positions (start,end).
- Fallback approximate check (token-level) for minor punctuation variance, flagged.

Key Tasks
- Implement find_all(essay_norm, quote_norm) → positions[].
- Store positions in response for audit.
- If not found: repair pass instructing to only pick verbatim spans from essay.

Acceptance
- 100% of quotes found; ≥99% exact; ≤1% approximate (flagged).
- Positions recorded for all quotes.

Risks/Mitigations
- Quotes too long → cap to 30 words; instruct shorter spans.
