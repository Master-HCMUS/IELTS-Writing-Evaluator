# Plan: Cost, Budget & Scaling

Objective
- Maintain total spend ≈ $20–$40 for one-week PoC.

Deliverables
- Token budgets per request; max essay length checks.
- Azure Cost Management budget + alert.
- Concurrency limits and backpressure to prevent spikes.

Key Tasks
- Default model: gpt-4o-mini; use gpt-4o only for complex Task1 images.
- Cache identical requests (hash of normalized inputs).
- Collect token usage metrics and cost per request estimate.
- Turn down resources off-hours; auto-stop dev environments.

Acceptance
- Estimated LLM spend ≈ $3–$5 per spec assumptions.
- No unbounded concurrency; error rate does not rise under load test (small scale).

Risks/Mitigations
- Unexpected long outputs → enforce tight max_tokens and array caps.
