# Plan: Prompt Design

Objective
- IELTS examiner persona with rubric + anchors, JSON-only responses, and evidence-first guidance.

Deliverables
- System prompt template with injected: rubric summary, anchor micro-exemplars, constraints (no chain-of-thought, JSON only).
- User prompt template per task type (Task1 with facts JSON; Task2 with essay).
- Response JSON schema and repair prompt for invalid outputs.

Key Tasks
- Draft concise rubric and anchors (small, versioned file).
- Enforce "respond strictly in JSON; cite verbatim quotes from the essay; no reasoning prose."
- Add safety rails (refuse unrelated inputs).
- Build repair loop: if schema invalid → one corrective reprompt with explicit JSON schema.

Acceptance
- >99% schema-valid responses without repair on test essays.
- Quotes always present and grounded.

Risks/Mitigations
- Prompt drift → store prompt hash; review drift alerts if schema errors spike.
