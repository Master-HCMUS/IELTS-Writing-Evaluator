# Feature: Task 1 Image → Facts JSON

Objective
- Extract structured facts (overview, trends, extremes, units) from charts/diagrams, then score rubric using facts + essay.

Deliverables
- Vision prompt for GPT-4o (only when needed).
- Facts JSON schema (compact, deterministic keys).
- Scoring prompt that consumes essay + facts JSON.

Key Tasks
- Vision step: analyze image → facts.json with fields: overview, measures[], trends[], extremes[], units.
- Confidence heuristic: if parse low-confidence or multi-chart complex → optional retry with stricter instructions.
- Integrate facts into Task 1 scoring system prompt; instruct grounding on facts.

Interfaces
- extract_facts(image) → FactsJSON.
- score_task1(essay, facts) → Task1Score.

Acceptance
- Facts JSON generated for ≥95% typical bar/line/pie/table images.
- Downstream scorer references facts in evidence.
- Errors degrade gracefully: if vision fails, return low confidence and proceed with essay-only scoring (flagged).

Risks/Mitigations
- Misread axes/units → require explicit units in schema; add unit consistency checks.
